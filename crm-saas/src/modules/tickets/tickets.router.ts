import { Router } from 'express';
import { z } from 'zod';
import { TicketStatus, TicketPriority } from '@prisma/client';
import { prisma, io } from '../../server';
import { auth } from '../../middlewares/auth.middleware';
import { validate } from '../../middlewares/validate.middleware';

const router = Router();

const createTicketSchema = z.object({
  subject: z.string().min(1),
  description: z.string().min(1),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).default('MEDIUM'),
  companyId: z.string().optional(),
  contactId: z.string().optional(),
  tags: z.array(z.string()).optional(),
});

const createMessageSchema = z.object({
  content: z.string().min(1),
  internal: z.boolean().default(false),
  attachments: z.array(z.object({
    filename: z.string(),
    url: z.string(),
    size: z.number(),
  })).optional(),
});

// Generate ticket number
async function generateTicketNumber(): Promise<string> {
  const year = new Date().getFullYear();
  const count = await prisma.ticket.count({
    where: {
      number: {
        startsWith: `TK-${year}-`,
      },
    },
  });
  return `TK-${year}-${String(count + 1).padStart(4, '0')}`;
}

// Get all tickets
router.get('/', auth, async (req, res, next) => {
  try {
    const { status, priority, assigneeId, search } = req.query;
    
    const where: any = {};

    if (status) {
      where.status = status as TicketStatus;
    }

    if (priority) {
      where.priority = priority as TicketPriority;
    }

    if (assigneeId) {
      where.assigneeId = assigneeId;
    } else if (req.user!.role === 'SUPPORT_AGENT') {
      // Support agents see only their assigned tickets
      where.assigneeId = req.user!.id;
    }

    if (search) {
      where.OR = [
        { subject: { contains: search as string, mode: 'insensitive' } },
        { number: { contains: search as string, mode: 'insensitive' } },
      ];
    }

    const tickets = await prisma.ticket.findMany({
      where,
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
        contact: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
          },
        },
        assignee: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
          },
        },
        _count: {
          select: {
            messages: true,
          },
        },
      },
      orderBy: [
        { status: 'asc' },
        { priority: 'desc' },
        { createdAt: 'desc' },
      ],
    });

    res.json({ tickets });
  } catch (error) {
    next(error);
  }
});

// Get ticket by ID
router.get('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const ticket = await prisma.ticket.findUnique({
      where: { id },
      include: {
        company: true,
        contact: true,
        assignee: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
          },
        },
        messages: {
          orderBy: { createdAt: 'asc' },
        },
      },
    });

    if (!ticket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }

    res.json({ ticket });
  } catch (error) {
    next(error);
  }
});

// Create ticket
router.post('/', auth, validate(createTicketSchema), async (req, res, next) => {
  try {
    const number = await generateTicketNumber();
    
    const ticket = await prisma.ticket.create({
      data: {
        ...req.body,
        number,
        status: 'NEW',
      },
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    // Create initial message
    await prisma.ticketMessage.create({
      data: {
        ticketId: ticket.id,
        authorId: req.user!.id,
        authorEmail: req.user!.email,
        authorName: `${req.user!.firstName || ''} ${req.user!.lastName || ''}`.trim() || req.user!.email,
        content: req.body.description,
        internal: false,
      },
    });

    // Emit WebSocket event
    io.emit('ticket:created', {
      ticket,
      user: req.user,
    });

    res.status(201).json({ ticket });
  } catch (error) {
    next(error);
  }
});

// Update ticket
router.put('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const ticket = await prisma.ticket.update({
      where: { id },
      data: req.body,
    });

    // Emit WebSocket event
    io.emit('ticket:updated', {
      ticket,
      user: req.user,
    });

    res.json({ ticket });
  } catch (error) {
    next(error);
  }
});

// Update ticket status
router.patch('/:id/status', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!status || !['NEW', 'OPEN', 'PENDING', 'SOLVED', 'CLOSED'].includes(status)) {
      return res.status(400).json({ error: 'Invalid status' });
    }

    const ticket = await prisma.ticket.update({
      where: { id },
      data: {
        status,
        ...(status === 'OPEN' && !ticket.firstResponseAt && { firstResponseAt: new Date() }),
        ...(status === 'SOLVED' && { resolvedAt: new Date() }),
        ...(status === 'CLOSED' && { closedAt: new Date() }),
      },
    });

    // Add internal note about status change
    await prisma.ticketMessage.create({
      data: {
        ticketId: id,
        authorId: req.user!.id,
        authorEmail: req.user!.email,
        authorName: `${req.user!.firstName || ''} ${req.user!.lastName || ''}`.trim(),
        content: `Statut changé en ${status}`,
        internal: true,
      },
    });

    res.json({ ticket });
  } catch (error) {
    next(error);
  }
});

// Assign ticket
router.patch('/:id/assign', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    const { assigneeId } = req.body;

    const ticket = await prisma.ticket.update({
      where: { id },
      data: { assigneeId },
    });

    res.json({ ticket });
  } catch (error) {
    next(error);
  }
});

// Add message to ticket
router.post('/:id/messages', auth, validate(createMessageSchema), async (req, res, next) => {
  try {
    const { id } = req.params;
    const { content, internal, attachments } = req.body;

    // Verify ticket exists
    const ticket = await prisma.ticket.findUnique({
      where: { id },
    });

    if (!ticket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }

    const message = await prisma.ticketMessage.create({
      data: {
        ticketId: id,
        authorId: req.user!.id,
        authorEmail: req.user!.email,
        authorName: `${req.user!.firstName || ''} ${req.user!.lastName || ''}`.trim() || req.user!.email,
        content,
        internal,
        attachments: attachments || [],
      },
    });

    // Update ticket status if it was NEW
    if (ticket.status === 'NEW') {
      await prisma.ticket.update({
        where: { id },
        data: {
          status: 'OPEN',
          firstResponseAt: new Date(),
        },
      });
    }

    // Emit WebSocket event
    io.to(`ticket:${id}`).emit('ticket:message', {
      ticketId: id,
      message,
    });

    res.status(201).json({ message });
  } catch (error) {
    next(error);
  }
});

export { router as ticketsRouter };