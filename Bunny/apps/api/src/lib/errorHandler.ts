/**
 * Error handling middleware for Express + Apollo Server
 */

import { Request, Response, NextFunction } from "express";
import logger from "./logger.js";
import { GraphQLError } from "graphql";
import { captureException } from "./sentryHelper.js";

/**
 * Formats errors for GraphQL responses
 */
export function formatError(error: any): any {
  logger.error("GraphQL error", {
    message: error.message,
    path: error.path,
    extensions: error.extensions,
  });

  // Capture GraphQL errors to Sentry (respects feature flags)
  captureException(error, {
    tags: {
      error_type: "graphql_error",
      error_code: error.extensions?.code || "UNKNOWN",
    },
    extra: {
      path: error.path,
      extensions: error.extensions,
    },
  });

  // If it's already a GraphQLError or has a code, just return it
  if (error.extensions?.code) {
    return error;
  }

  // Otherwise wrap it in a standard internal error
  return new GraphQLError("An unexpected error occurred", {
    extensions: {
      code: "INTERNAL_SERVER_ERROR",
    },
  });
}

/**
 * Express error handler
 */
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  logger.error("Express error", {
    message: err.message,
    path: req.path,
    method: req.method,
    stack: err.stack,
  });

  // Capture Express errors to Sentry (respects feature flags)
  // Only capture 5xx errors to avoid noise from client errors
  const statusCode = "statusCode" in err ? (err as any).statusCode : 500;
  if (statusCode >= 500) {
    captureException(err, {
      tags: {
        error_type: "express_error",
        error_code: (err as any).code || "UNKNOWN_ERROR",
        status_code: statusCode.toString(),
      },
      extra: {
        path: req.path,
        method: req.method,
        headers: req.headers,
      },
    });
  }

  // Handle known error types
  if ("statusCode" in err) {
    const status = (err as any).statusCode;
    res.status(status).json({
      error: {
        message: err.message,
        code: (err as any).code || "UNKNOWN_ERROR",
        path: req.path,
      },
    });
    return;
  }

  // Handle unexpected errors
  res.status(500).json({
    error: {
      message: "Internal server error",
      code: "INTERNAL_SERVER_ERROR",
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
      code: "NOT_FOUND",
      path: req.path,
    },
  });
}

/**
 * Async error wrapper for Express routes
 */
export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<any>,
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
