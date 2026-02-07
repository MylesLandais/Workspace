/**
 * Client-side Error Logger
 *
 * Logs errors locally for debugging while attempting to send to Sentry.
 * Ensures errors are always logged even if Sentry transport fails.
 */

import * as Sentry from "@sentry/nextjs";

interface ErrorContext {
  tags?: Record<string, string>;
  extra?: Record<string, unknown>;
  user?: Sentry.User;
  level?: "error" | "warning" | "info";
}

/**
 * Log and capture an error with local debugging output
 */
export function logError(error: unknown, context?: ErrorContext): void {
  // Convert error to Error object first
  const errorObj = error instanceof Error ? error : new Error(String(error));

  try {
    const timestamp = new Date().toISOString();

    // Collect comprehensive error context
    const enhancedContext = {
      ...context,
      extra: {
        ...context?.extra,
        // Add browser/environment context
        userAgent:
          typeof window !== "undefined" ? navigator.userAgent : undefined,
        url: typeof window !== "undefined" ? window.location.href : undefined,
        timestamp,
        // Add error details
        errorName: errorObj.name,
        errorMessage: errorObj.message,
        errorStack: errorObj.stack,
      },
    };

    // Log to console with formatting for debugging
    console.group(`🚨 [${timestamp}] Error Captured`);
    console.error("Error:", errorObj);

    if (errorObj.stack) {
      console.error("Stack:", errorObj.stack);
    }

    if (enhancedContext.tags && Object.keys(enhancedContext.tags).length > 0) {
      console.info("Tags:", enhancedContext.tags);
    }

    if (
      enhancedContext.extra &&
      Object.keys(enhancedContext.extra).length > 0
    ) {
      console.info("Extra Context:", enhancedContext.extra);
    }

    if (enhancedContext.user) {
      console.info("User:", enhancedContext.user);
    }

    console.groupEnd();
  } catch (loggingError) {
    // If console logging fails, at least try to log something
    console.error("[logError] Failed to log error:", loggingError);
    console.error("[logError] Original error:", error);
  }

  // Attempt to send to Sentry (but don't fail if it fails)
  try {
    // Check if Sentry is initialized using the proper API
    const sentryClient =
      typeof window !== "undefined" ? Sentry.getClient() : null;

    if (!sentryClient) {
      console.warn("[Sentry] ⚠️ Not initialized yet, skipping error capture");
      console.warn("[Sentry] Check if sentry.client.config.ts is being loaded");
      return;
    }

    Sentry.withScope((scope) => {
      // Collect enhanced context with browser/environment info
      const enhancedContext = {
        ...context,
        extra: {
          ...context?.extra,
          // Add browser/environment context
          userAgent:
            typeof window !== "undefined" ? navigator.userAgent : undefined,
          url: typeof window !== "undefined" ? window.location.href : undefined,
          timestamp: new Date().toISOString(),
          // Add error details
          errorName: errorObj.name,
          errorMessage: errorObj.message,
          errorStack: errorObj.stack,
        },
      };

      // Set tags if provided
      if (enhancedContext.tags) {
        Object.entries(enhancedContext.tags).forEach(([key, value]) => {
          scope.setTag(key, value);
        });
      }

      // Set extra context if provided
      if (enhancedContext.extra) {
        Object.entries(enhancedContext.extra).forEach(([key, value]) => {
          // Serialize complex objects for Sentry (Sentry doesn't handle circular refs well)
          try {
            if (value && typeof value === "object") {
              // Try to serialize, but handle circular references
              const serialized = JSON.stringify(
                value,
                (k, v) => {
                  if (
                    k === "full_error" ||
                    k === "error_object" ||
                    k === "full_result"
                  ) {
                    // For complex error objects, try to extract useful info
                    if (v && typeof v === "object") {
                      try {
                        return {
                          message: (v as any).message,
                          code: (v as any).code,
                          status: (v as any).status,
                          statusText: (v as any).statusText,
                          name: (v as any).name,
                          stack: (v as any).stack,
                          _stringified: String(v),
                        };
                      } catch {
                        return String(v);
                      }
                    }
                  }
                  return v;
                },
                2,
              );
              scope.setExtra(key, serialized);
            } else {
              scope.setExtra(key, value);
            }
          } catch (serializeError) {
            // If serialization fails, just stringify it
            scope.setExtra(key, String(value));
          }
        });
      }

      // Set user if provided
      if (enhancedContext.user) {
        scope.setUser(enhancedContext.user);
      }

      // Set level if provided
      if (enhancedContext.level) {
        scope.setLevel(enhancedContext.level);
      }

      // Add auth context if available
      if (enhancedContext.tags?.auth_flow) {
        scope.setContext("auth", {
          flow_type: enhancedContext.tags.auth_flow,
          email_domain: enhancedContext.extra?.email
            ? (enhancedContext.extra.email as string).split("@")[1]
            : undefined,
        });
      }

      // Capture the exception
      let eventId: string | undefined;
      try {
        eventId = Sentry.captureException(errorObj);
      } catch (captureError) {
        console.error(
          "[Sentry] ❌ captureException threw an error:",
          captureError,
        );
        return;
      }

      // Always log that we attempted to send (for debugging)
      if (eventId) {
        console.log(`[Sentry] ✅ Event captured with ID: ${eventId}`);
        console.log("[Sentry] Event details:", {
          message: errorObj.message,
          tags: context?.tags,
          extra: context?.extra,
        });

        // Flush the event immediately to ensure it's sent
        Sentry.flush(2000)
          .then(() => {
            console.log(`[Sentry] ✅ Event ${eventId} flushed to Sentry`);
          })
          .catch((flushError) => {
            console.error(
              `[Sentry] ❌ Failed to flush event ${eventId}:`,
              flushError,
            );
          });
      } else {
        console.warn(
          "[Sentry] ⚠️ captureException returned no event ID - event may not be sent",
        );
        console.warn("[Sentry] Check if Sentry is properly initialized");
        console.warn("[Sentry] Client:", sentryClient);
      }
    });
  } catch (sentryError) {
    // Log if Sentry capture fails (for debugging)
    console.error("[Sentry] ❌ Failed to capture exception:", sentryError);
    if (sentryError instanceof Error) {
      console.error("[Sentry] Error stack:", sentryError.stack);
    }
  }
}

/**
 * Log a warning
 */
export function logWarning(
  message: string,
  context?: Omit<ErrorContext, "level">,
): void {
  const timestamp = new Date().toISOString();

  console.group(`⚠️ [${timestamp}] Warning`);
  console.warn(message);

  if (context?.tags && Object.keys(context.tags).length > 0) {
    console.info("Tags:", context.tags);
  }

  if (context?.extra && Object.keys(context.extra).length > 0) {
    console.info("Extra Context:", context.extra);
  }

  console.groupEnd();

  // Attempt to send to Sentry as warning
  try {
    Sentry.withScope((scope) => {
      if (context?.tags) {
        Object.entries(context.tags).forEach(([key, value]) => {
          scope.setTag(key, value);
        });
      }

      if (context?.extra) {
        Object.entries(context.extra).forEach(([key, value]) => {
          scope.setExtra(key, value);
        });
      }

      scope.setLevel("warning");
      Sentry.captureMessage(message, "warning");
    });
  } catch (sentryError) {
    // Silently fail if Sentry capture fails
  }
}

/**
 * Log an info message for debugging
 */
export function logInfo(message: string, data?: Record<string, unknown>): void {
  const timestamp = new Date().toISOString();

  console.log(`ℹ️ [${timestamp}] ${message}`);

  if (data && Object.keys(data).length > 0) {
    console.log("Data:", data);
  }
}
