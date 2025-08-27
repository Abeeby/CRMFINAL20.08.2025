import { Request, Response, NextFunction } from 'express';
import { Prisma } from '@prisma/client';
import { ZodError } from 'zod';
import { logger } from '../utils/logger';

export interface AppError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

export function errorHandler(
  err: AppError,
  req: Request,
  res: Response,
  next: NextFunction
) {
  let statusCode = err.statusCode || 500;
  let message = err.message || 'Internal Server Error';
  let details: any = undefined;

  // Log the error
  logger.error(`Error ${statusCode}: ${message}`, {
    error: err,
    path: req.path,
    method: req.method,
    body: req.body,
    query: req.query,
    ip: req.ip,
  });

  // Handle Prisma errors
  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === 'P2002') {
      statusCode = 400;
      message = 'Un enregistrement avec cette valeur existe déjà';
      details = { field: err.meta?.target };
    } else if (err.code === 'P2025') {
      statusCode = 404;
      message = 'Enregistrement non trouvé';
    } else if (err.code === 'P2003') {
      statusCode = 400;
      message = 'Référence invalide';
      details = { field: err.meta?.field_name };
    } else {
      statusCode = 400;
      message = 'Erreur de base de données';
      details = { code: err.code };
    }
  }

  // Handle Zod validation errors
  if (err instanceof ZodError) {
    statusCode = 400;
    message = 'Erreur de validation';
    details = err.errors.map(e => ({
      field: e.path.join('.'),
      message: e.message,
    }));
  }

  // Handle JWT errors
  if (err.name === 'JsonWebTokenError') {
    statusCode = 401;
    message = 'Token invalide';
  } else if (err.name === 'TokenExpiredError') {
    statusCode = 401;
    message = 'Token expiré';
  }

  // Send response
  res.status(statusCode).json({
    error: true,
    message,
    details,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
}