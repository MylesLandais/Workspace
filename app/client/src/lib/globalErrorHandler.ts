/**
 * Global Error Handler
 *
 * Ensures all errors are captured and logged, even if they slip through
 */

import * as Sentry from "@sentry/nextjs";
import { logError } from "./errorLogger";

/**
 * Wrap a function to automatically capture any errors
 */
export function withErrorCapture<
  T extends (...args: unknown[]) => Promise<unknown>,
>(
  fn: T,
  context?: { tags?: Record<string, string>; extra?: Record<string, unknown> },
): T {
  return ((...args: unknown[]) => {
    return Promise.resolve(fn(...args)).catch((error) => {
      logError(error, {
        tags: {
          ...context?.tags,
          error_capture: "withErrorCapture",
        },
        extra: {
          ...context?.extra,
          function: fn.name || "anonymous",
        },
      });
      throw error; // Re-throw to maintain behavior
    });
  }) as T;
}

/**
 * Wrap synchronous function to capture errors
 */
export function withErrorCaptureSync<T extends (...args: unknown[]) => unknown>(
  fn: T,
  context?: { tags?: Record<string, string>; extra?: Record<string, unknown> },
): T {
  return ((...args: unknown[]) => {
    try {
      return fn(...args);
    } catch (error) {
      logError(error, {
        tags: {
          ...context?.tags,
          error_capture: "withErrorCaptureSync",
        },
        extra: {
          ...context?.extra,
          function: fn.name || "anonymous",
        },
      });
      throw error; // Re-throw to maintain behavior
    }
  }) as T;
}

/**
 * Verify Sentry is working and ready
 */
export function verifySentrySetup(): {
  initialized: boolean;
  client: ReturnType<typeof Sentry.getClient> | null;
  issues: string[];
} {
  const issues: string[] = [];
  const client = Sentry.getClient();

  if (!client) {
    issues.push("Sentry client is not initialized");
  }

  const dsn = client?.getDsn();
  if (!dsn) {
    issues.push("Sentry DSN is not configured");
  }

  return {
    initialized: !!client && !!dsn,
    client,
    issues,
  };
}

/**
 * Test Sentry capture - throws an error to test if it's captured
 */
export function testSentryCapture(
  message = "Test error from testSentryCapture",
): void {
  logError(new Error(message), {
    tags: {
      test: "true",
      source: "testSentryCapture",
    },
    extra: {
      timestamp: new Date().toISOString(),
    },
  });
}
