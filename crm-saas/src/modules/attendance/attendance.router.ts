import { Router } from 'express';
import { z } from 'zod';
import dayjs from 'dayjs';
import { AttendanceType, AttendanceSource } from '@prisma/client';
import { prisma } from '../../server';
import { auth } from '../../middlewares/auth.middleware';
import { validate, validateQuery } from '../../middlewares/validate.middleware';
import { logger } from '../../utils/logger';

const router = Router();

// Validation schemas
const punchSchema = z.object({
  type: z.enum(['IN_MORNING', 'OUT_MORNING', 'IN_AFTERNOON', 'OUT_EVENING']),
  source: z.enum(['WEB', 'MOBILE', 'QR', 'MANUAL']).default('WEB'),
  location: z.object({
    lat: z.number().optional(),
    lng: z.number().optional(),
    address: z.string().optional(),
  }).optional(),
  deviceInfo: z.object({
    userAgent: z.string().optional(),
    platform: z.string().optional(),
  }).optional(),
});

const reportQuerySchema = z.object({
  month: z.string().regex(/^\d{1,2}$/).transform(Number).optional(),
  year: z.string().regex(/^\d{4}$/).transform(Number).optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
});

// Helper function to detect anomalies
function detectAnomaly(
  type: AttendanceType,
  existingAttendances: any[],
  timestamp: Date
): string {
  const hour = timestamp.getHours();
  const expectedOrder = ['IN_MORNING', 'OUT_MORNING', 'IN_AFTERNOON', 'OUT_EVENING'];
  
  // Check for late arrival
  if (type === 'IN_MORNING' && hour > 9) {
    return 'LATE';
  }
  if (type === 'IN_AFTERNOON' && hour > 14) {
    return 'LATE';
  }
  
  // Check for early departure
  if (type === 'OUT_MORNING' && hour < 11) {
    return 'EARLY';
  }
  if (type === 'OUT_EVENING' && hour < 17) {
    return 'EARLY';
  }
  
  // Check for missing punches
  const lastAttendance = existingAttendances[existingAttendances.length - 1];
  if (lastAttendance) {
    const lastIndex = expectedOrder.indexOf(lastAttendance.type);
    const currentIndex = expectedOrder.indexOf(type);
    
    if (currentIndex <= lastIndex) {
      return 'OVERLAP';
    }
    if (currentIndex - lastIndex > 1) {
      return 'MISSING';
    }
  } else if (type !== 'IN_MORNING') {
    return 'MISSING';
  }
  
  return 'NONE';
}

// Record attendance punch
router.post('/punch', auth, validate(punchSchema), async (req, res, next) => {
  try {
    const { type, source, location, deviceInfo } = req.body;
    const userId = req.user!.id;
    const now = new Date();
    
    // Get today's existing attendances
    const startOfDay = dayjs(now).startOf('day').toDate();
    const endOfDay = dayjs(now).endOf('day').toDate();
    
    const todayAttendances = await prisma.attendance.findMany({
      where: {
        employeeId: userId,
        timestamp: {
          gte: startOfDay,
          lte: endOfDay,
        },
      },
      orderBy: { timestamp: 'asc' },
    });
    
    // Check if this exact type was already punched today
    const alreadyPunched = todayAttendances.find(a => a.type === type);
    if (alreadyPunched) {
      return res.status(400).json({
        error: 'Déjà pointé',
        message: `Vous avez déjà effectué ce pointage aujourd'hui à ${dayjs(alreadyPunched.timestamp).format('HH:mm')}`,
      });
    }
    
    // Detect anomalies
    const anomaly = detectAnomaly(type as AttendanceType, todayAttendances, now);
    
    // Create attendance record
    const attendance = await prisma.attendance.create({
      data: {
        employeeId: userId,
        type: type as AttendanceType,
        timestamp: now,
        source: source as AttendanceSource,
        anomaly,
        location: location || undefined,
        deviceInfo: deviceInfo || undefined,
      },
      include: {
        employee: {
          select: {
            firstName: true,
            lastName: true,
            email: true,
          },
        },
      },
    });
    
    logger.info(`Attendance punch recorded: ${type} for user ${userId}`, {
      anomaly,
      timestamp: now,
    });
    
    // Build response message
    let message = `Pointage ${type} enregistré à ${dayjs(now).format('HH:mm')}`;
    if (anomaly !== 'NONE') {
      const anomalyMessages: Record<string, string> = {
        LATE: 'Pointage en retard',
        EARLY: 'Pointage en avance',
        MISSING: 'Pointage(s) manquant(s) détecté(s)',
        OVERLAP: 'Ordre de pointage incorrect',
      };
      message += ` - Attention: ${anomalyMessages[anomaly] || anomaly}`;
    }
    
    res.status(201).json({
      message,
      attendance: {
        id: attendance.id,
        type: attendance.type,
        timestamp: attendance.timestamp,
        anomaly: attendance.anomaly,
      },
      todayTotal: todayAttendances.length + 1,
    });
  } catch (error) {
    next(error);
  }
});

// Get today's attendances
router.get('/today', auth, async (req, res, next) => {
  try {
    const userId = req.user!.id;
    const today = new Date();
    const startOfDay = dayjs(today).startOf('day').toDate();
    const endOfDay = dayjs(today).endOf('day').toDate();
    
    const attendances = await prisma.attendance.findMany({
      where: {
        employeeId: userId,
        timestamp: {
          gte: startOfDay,
          lte: endOfDay,
        },
      },
      orderBy: { timestamp: 'asc' },
    });
    
    // Calculate worked hours
    let workedMinutes = 0;
    const punches = attendances.map(a => ({
      type: a.type,
      time: a.timestamp,
    }));
    
    // Calculate morning session
    const morningIn = punches.find(p => p.type === 'IN_MORNING');
    const morningOut = punches.find(p => p.type === 'OUT_MORNING');
    if (morningIn && morningOut) {
      workedMinutes += dayjs(morningOut.time).diff(dayjs(morningIn.time), 'minute');
    }
    
    // Calculate afternoon session
    const afternoonIn = punches.find(p => p.type === 'IN_AFTERNOON');
    const eveningOut = punches.find(p => p.type === 'OUT_EVENING');
    if (afternoonIn && eveningOut) {
      workedMinutes += dayjs(eveningOut.time).diff(dayjs(afternoonIn.time), 'minute');
    }
    
    const workedHours = Math.floor(workedMinutes / 60);
    const workedMinutesRemainder = workedMinutes % 60;
    
    res.json({
      date: today.toISOString(),
      attendances: attendances.map(a => ({
        id: a.id,
        type: a.type,
        timestamp: a.timestamp,
        time: dayjs(a.timestamp).format('HH:mm'),
        anomaly: a.anomaly,
        source: a.source,
      })),
      summary: {
        totalPunches: attendances.length,
        workedTime: `${workedHours}h${workedMinutesRemainder.toString().padStart(2, '0')}`,
        workedMinutes,
        hasAnomalies: attendances.some(a => a.anomaly !== 'NONE'),
      },
    });
  } catch (error) {
    next(error);
  }
});

// Get monthly report
router.get('/report', auth, validateQuery(reportQuerySchema), async (req, res, next) => {
  try {
    const userId = req.user!.id;
    const now = new Date();
    
    // Parse dates from query
    const month = Number(req.query.month) || now.getMonth() + 1;
    const year = Number(req.query.year) || now.getFullYear();
    
    const startDate = req.query.startDate 
      ? dayjs(req.query.startDate as string).startOf('day').toDate()
      : dayjs(`${year}-${month}-01`).startOf('month').toDate();
    
    const endDate = req.query.endDate
      ? dayjs(req.query.endDate as string).endOf('day').toDate()
      : dayjs(startDate).endOf('month').toDate();
    
    // Get attendances for the period
    const attendances = await prisma.attendance.findMany({
      where: {
        employeeId: userId,
        timestamp: {
          gte: startDate,
          lte: endDate,
        },
      },
      orderBy: { timestamp: 'asc' },
    });
    
    // Group by day and calculate daily stats
    const dailyReport: Record<string, any> = {};
    let totalWorkedMinutes = 0;
    let totalAnomalies = 0;
    let daysWorked = 0;
    
    attendances.forEach(attendance => {
      const day = dayjs(attendance.timestamp).format('YYYY-MM-DD');
      
      if (!dailyReport[day]) {
        dailyReport[day] = {
          date: day,
          dayOfWeek: dayjs(attendance.timestamp).format('dddd'),
          punches: [],
          workedMinutes: 0,
          anomalies: [],
        };
      }
      
      dailyReport[day].punches.push({
        type: attendance.type,
        time: dayjs(attendance.timestamp).format('HH:mm'),
        timestamp: attendance.timestamp,
        anomaly: attendance.anomaly,
      });
      
      if (attendance.anomaly !== 'NONE') {
        dailyReport[day].anomalies.push(attendance.anomaly);
        totalAnomalies++;
      }
    });
    
    // Calculate worked time for each day
    Object.values(dailyReport).forEach((day: any) => {
      const punches = day.punches;
      
      // Morning session
      const morningIn = punches.find((p: any) => p.type === 'IN_MORNING');
      const morningOut = punches.find((p: any) => p.type === 'OUT_MORNING');
      if (morningIn && morningOut) {
        const minutes = dayjs(morningOut.timestamp).diff(dayjs(morningIn.timestamp), 'minute');
        day.workedMinutes += minutes;
      }
      
      // Afternoon session
      const afternoonIn = punches.find((p: any) => p.type === 'IN_AFTERNOON');
      const eveningOut = punches.find((p: any) => p.type === 'OUT_EVENING');
      if (afternoonIn && eveningOut) {
        const minutes = dayjs(eveningOut.timestamp).diff(dayjs(afternoonIn.timestamp), 'minute');
        day.workedMinutes += minutes;
      }
      
      if (day.workedMinutes > 0) {
        totalWorkedMinutes += day.workedMinutes;
        daysWorked++;
      }
      
      // Format worked time
      const hours = Math.floor(day.workedMinutes / 60);
      const minutes = day.workedMinutes % 60;
      day.workedTime = `${hours}h${minutes.toString().padStart(2, '0')}`;
    });
    
    // Calculate summary statistics
    const totalHours = Math.floor(totalWorkedMinutes / 60);
    const totalMinutesRemainder = totalWorkedMinutes % 60;
    const averageMinutesPerDay = daysWorked > 0 ? Math.floor(totalWorkedMinutes / daysWorked) : 0;
    const averageHours = Math.floor(averageMinutesPerDay / 60);
    const averageMinutes = averageMinutesPerDay % 60;
    
    res.json({
      period: {
        startDate: startDate.toISOString(),
        endDate: endDate.toISOString(),
        month,
        year,
      },
      dailyReports: Object.values(dailyReport),
      summary: {
        daysWorked,
        totalWorkedTime: `${totalHours}h${totalMinutesRemainder.toString().padStart(2, '0')}`,
        totalWorkedMinutes,
        averagePerDay: `${averageHours}h${averageMinutes.toString().padStart(2, '0')}`,
        totalAnomalies,
        attendanceRate: `${Math.round((daysWorked / 22) * 100)}%`, // Assuming 22 working days
      },
    });
  } catch (error) {
    next(error);
  }
});

// Get anomalies
router.get('/anomalies', auth, async (req, res, next) => {
  try {
    const userId = req.user!.id;
    
    const anomalies = await prisma.attendance.findMany({
      where: {
        employeeId: userId,
        anomaly: {
          not: 'NONE',
        },
      },
      orderBy: { timestamp: 'desc' },
      take: 50, // Last 50 anomalies
    });
    
    res.json({
      anomalies: anomalies.map(a => ({
        id: a.id,
        type: a.type,
        timestamp: a.timestamp,
        date: dayjs(a.timestamp).format('YYYY-MM-DD'),
        time: dayjs(a.timestamp).format('HH:mm'),
        anomaly: a.anomaly,
        validated: a.validated,
      })),
      total: anomalies.length,
    });
  } catch (error) {
    next(error);
  }
});

// Export for payroll (CSV format)
router.get('/export', auth, async (req, res, next) => {
  try {
    const userId = req.user!.id;
    const { month = new Date().getMonth() + 1, year = new Date().getFullYear() } = req.query;
    
    const startDate = dayjs(`${year}-${month}-01`).startOf('month').toDate();
    const endDate = dayjs(startDate).endOf('month').toDate();
    
    const attendances = await prisma.attendance.findMany({
      where: {
        employeeId: userId,
        timestamp: {
          gte: startDate,
          lte: endDate,
        },
      },
      orderBy: { timestamp: 'asc' },
      include: {
        employee: {
          select: {
            firstName: true,
            lastName: true,
            email: true,
          },
        },
      },
    });
    
    // Generate CSV content
    const csvLines = ['Date,Type,Heure,Anomalie'];
    
    attendances.forEach(a => {
      const date = dayjs(a.timestamp).format('YYYY-MM-DD');
      const time = dayjs(a.timestamp).format('HH:mm:ss');
      csvLines.push(`${date},${a.type},${time},${a.anomaly}`);
    });
    
    const csv = csvLines.join('\n');
    
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename=pointages_${month}_${year}.csv`);
    res.send(csv);
  } catch (error) {
    next(error);
  }
});

export { router as attendanceRouter };