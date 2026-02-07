/**
 * API Route Logger
 *
 * Wraps API routes with automatic logging, timing, and error handling.
 */

import { NextRequest, NextResponse } from "next/server";
import { createLogger } from "./logger";

const log = createLogger("api");

export interface ApiLogContext {
  path: string;
  method: string;
  status?: number;
  duration?: number;
  error?: unknown;
  [key: string]: unknown;
}

export async function withApiLogging<T>(
  request: NextRequest,
  handler: () => Promise<NextResponse<T>>,
  context?: Partial<ApiLogContext>,
): Promise<NextResponse<T>> {
  const startTime = Date.now();
  const path = new URL(request.url).pathname;
  const method = request.method;

  const logContext: ApiLogContext = {
    path,
    method,
    ...context,
  };

  log.info(`API ${method} ${path}`, logContext);

  try {
    const response = await handler();
    const duration = Date.now() - startTime;

    log.info(`API ${method} ${path} completed`, {
      ...logContext,
      status: response.status,
      duration,
    });

    if (duration > 1000) {
      log.warn(`Slow API request: ${method} ${path}`, {
        ...logContext,
        duration,
        threshold: 1000,
      });
    }

    return response;
  } catch (error) {
    const duration = Date.now() - startTime;

    log.error(`API ${method} ${path} failed`, error, {
      ...logContext,
      duration,
    });

    if (error instanceof Error) {
      return NextResponse.json(
        {
          error: "Internal server error",
          message: error.message,
          path,
        },
        { status: 500 },
      ) as NextResponse<T>;
    }

    return NextResponse.json(
      {
        error: "Internal server error",
        path,
      },
      { status: 500 },
    ) as NextResponse<T>;
  }
}

export function logDatabaseQuery(query: string, params?: unknown[]): void {
  log.debug("Database query", {
    query: query.substring(0, 200),
    hasParams: !!params,
    paramCount: params?.length || 0,
  });
}

export function logDatabaseResult(rowCount: number, duration?: number): void {
  log.debug("Database result", {
    rowCount,
    duration,
  });
}
