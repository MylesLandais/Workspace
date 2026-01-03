/**
 * Error handling middleware for Express + Apollo Server
 */

import { Request, Response, NextFunction } from 'express';
import logger from './logger.js';
import type { GraphQLError } from '@apollo/server';

/**
 * Formats errors for GraphQL responses
 */
export function formatError(error: any): GraphQLError {
  logger.error('GraphQL error', {
    message: error.message,
    path: error.path,
    extensions: error.extensions,
  });

  // If it's a custom AppError, format it nicely
  if (error.extensions?.code) {
    return {
      ...error,
      message: error.message,
    };
  }

  // Log full stack for unknown errors
  if (!error.extensions?.code) {
    logger.error('Unexpected error', {
      message: error.message,
      stack: error.stack,
    });

    return {
      message: 'An unexpected error occurred',
      extensions: {
        code: 'INTERNAL_SERVER_ERROR',
      },
    };
  }

  return error;
}

/**
 * Express error handler
 */
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  logger.error('Express error', {
    message: err.message,
    path: req.path,
    method: req.method,
    stack: err.stack,
  });

  // Handle known error types
  if ('statusCode' in err) {
    const status = (err as any).statusCode;
    res.status(status).json({
      error: {
        message: err.message,
        code: (err as any).code || 'UNKNOWN_ERROR',
        path: req.path,
      },
    });
    return;
  }

  // Handle unexpected errors
  res.status(500).json({
    error: {
      message: 'Internal server error',
      code: 'INTERNAL_SERVER_ERROR',
      path: req.path,
    },
  });
}

/**
 * 404 handler
 */
export function notFoundHandler(req: Request, res: Response): void {
  res.status(404).json({
    error: {
      message: `Path ${req.path} not found`,
      code: 'NOT_FOUND',
      path: req.path,
    },
  });
}

/**
 * Async error wrapper for Express routes
 */
export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<any>
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
