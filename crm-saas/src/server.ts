import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import cookieParser from 'cookie-parser';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { PrismaClient } from '@prisma/client';
import { errorHandler } from './middlewares/error.middleware';
import { logger } from './utils/logger';

// Import routers
import { authRouter } from './modules/auth/auth.router';
import { usersRouter } from './modules/users/users.router';
import { companiesRouter } from './modules/companies/companies.router';
import { contactsRouter } from './modules/contacts/contacts.router';
import { dealsRouter } from './modules/deals/deals.router';
import { ticketsRouter } from './modules/tickets/tickets.router';
import { attendanceRouter } from './modules/attendance/attendance.router';

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true,
  },
});

export const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
});

// Global middlewares
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}));
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    query: req.query,
    ip: req.ip,
  });
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
    version: '1.0.0',
  });
});

// API Routes
app.use('/api/auth', authRouter);
app.use('/api/users', usersRouter);
app.use('/api/companies', companiesRouter);
app.use('/api/contacts', contactsRouter);
app.use('/api/deals', dealsRouter);
app.use('/api/tickets', ticketsRouter);
app.use('/api/attendance', attendanceRouter);

// 404 handler
app.use((req, res) => {
  res.status(404).json({ 
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`,
  });
});

// Error handler (must be last)
app.use(errorHandler);

// WebSocket handling
io.on('connection', (socket) => {
  logger.info(`WebSocket client connected: ${socket.id}`);
  
  socket.on('join-room', (room: string) => {
    socket.join(room);
    logger.info(`Socket ${socket.id} joined room ${room}`);
  });
  
  socket.on('leave-room', (room: string) => {
    socket.leave(room);
    logger.info(`Socket ${socket.id} left room ${room}`);
  });
  
  socket.on('disconnect', () => {
    logger.info(`WebSocket client disconnected: ${socket.id}`);
  });
});

// Export for use in other modules
export { io };

const PORT = process.env.PORT || 3333;

httpServer.listen(PORT, () => {
  logger.info(`🚀 Server running on http://localhost:${PORT}`);
  logger.info(`📊 Health check: http://localhost:${PORT}/health`);
  logger.info(`🔌 WebSocket ready on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  httpServer.close(() => {
    logger.info('HTTP server closed');
    prisma.$disconnect().then(() => {
      logger.info('Database connection closed');
      process.exit(0);
    });
  });
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully...');
  httpServer.close(() => {
    logger.info('HTTP server closed');
    prisma.$disconnect().then(() => {
      logger.info('Database connection closed');
      process.exit(0);
    });
  });
});