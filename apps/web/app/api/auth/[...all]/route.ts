import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";
import { withSpan, addSpanEvent } from "@/lib/tracing/tracer";
import * as Sentry from "@sentry/nextjs";

/**
 * Better Auth Route Handler for Next.js 15.
 * Handles all /api/auth/* requests.
 * Includes OpenTelemetry tracing, Sentry error capture, and performance logging.
 */
const { GET: authGET, POST: authPOST } = toNextJsHandler(auth);

/**
 * Diagnose and log database connection issues
 */
function diagnoseDatabaseError(error: unknown): {
  isDatabaseError: boolean;
  errorType: string;
  details: Record<string, unknown>;
} {
  const errorStr = String(error);
  const errorObj = error instanceof Error ? error : { message: String(error) };

  // Check for common database errors
  const isDatabaseError =
    errorStr.includes("Access denied") ||
    errorStr.includes("ER_ACCESS_DENIED_ERROR") ||
    errorStr.includes("ECONNREFUSED") ||
    errorStr.includes("ENOTFOUND") ||
    errorStr.includes("PROTOCOL_ERROR") ||
    errorStr.includes("PROTOCOL_SEQUENCE_TIMEOUT") ||
    errorStr.includes("Connection timeout");

  let errorType = "unknown";
  if (errorStr.includes("Access denied")) {
    errorType = "auth_denied";
  } else if (errorStr.includes("ECONNREFUSED")) {
    errorType = "connection_refused";
  } else if (errorStr.includes("ENOTFOUND")) {
    errorType = "host_not_found";
  } else if (errorStr.includes("PROTOCOL")) {
    errorType = "protocol_error";
  } else if (errorStr.includes("timeout")) {
    errorType = "connection_timeout";
  }

  return {
    isDatabaseError,
    errorType,
    details: {
      message: errorObj instanceof Error ? errorObj.message : String(error),
      stack:
        errorObj instanceof Error && errorObj.stack
          ? errorObj.stack.split("\n").slice(0, 5).join("\n")
          : undefined,
      errorString: errorStr.substring(0, 200),
      dbHost: process.env.MYSQL_HOST,
      dbUser: process.env.MYSQL_USER,
      dbDatabase: process.env.MYSQL_DATABASE,
      nodeEnv: process.env.NODE_ENV,
    },
  };
}

/**
 * Expected auth error codes that shouldn't be logged to Sentry
 * These are normal user errors, not bugs
 */
const EXPECTED_AUTH_ERROR_CODES = [
  "INVALID_EMAIL_OR_PASSWORD",
  "USER_NOT_FOUND",
  "INVALID_PASSWORD",
  "EMAIL_NOT_VERIFIED",
  "INVALID_EMAIL",
  "INVALID_CREDENTIALS",
];

/**
 * Capture HTTP error responses to Sentry
 * Better Auth returns errors as HTTP responses, not thrown exceptions
 *
 * Note: Expected user errors (wrong password, user not found) are NOT sent to Sentry
 * to avoid noise from normal authentication failures.
 */
async function captureAuthErrorToSentry(
  response: Response,
  pathname: string,
  method: string,
): Promise<void> {
  if (response.status < 400) return;

  try {
    // Clone response to read body without consuming it
    const clonedResponse = response.clone();
    let errorBody: unknown;

    try {
      errorBody = await clonedResponse.json();
    } catch {
      errorBody = await clonedResponse.text();
    }

    const errorCode =
      typeof errorBody === "object" && errorBody !== null
        ? ((errorBody as Record<string, unknown>).code as string)
        : undefined;

    const errorMessage =
      typeof errorBody === "object" && errorBody !== null
        ? (errorBody as Record<string, unknown>).message ||
          (errorBody as Record<string, unknown>).error ||
          JSON.stringify(errorBody)
        : String(errorBody);

    // Log to console for debugging
    console.log(`[Auth] ${method} ${pathname} returned ${response.status}:`, {
      status: response.status,
      code: errorCode,
      message: errorMessage,
    });

    // Skip Sentry for expected user errors (wrong password, user not found, etc.)
    if (
      response.status === 401 &&
      errorCode &&
      EXPECTED_AUTH_ERROR_CODES.includes(errorCode)
    ) {
      console.log(`[Auth] Skipping Sentry for expected error: ${errorCode}`);
      return;
    }

    // Capture unexpected errors to Sentry with full context
    Sentry.withScope((scope) => {
      scope.setTag("auth.endpoint", pathname);
      scope.setTag("auth.method", method);
      scope.setTag("http.status_code", String(response.status));
      scope.setTag("error.type", "auth_http_error");
      if (errorCode) {
        scope.setTag("auth.error_code", errorCode);
      }

      scope.setExtra("response_status", response.status);
      scope.setExtra("response_status_text", response.statusText);
      scope.setExtra("response_body", errorBody);
      scope.setExtra("auth_pathname", pathname);

      scope.setContext("auth_error", {
        endpoint: pathname,
        method,
        status: response.status,
        statusText: response.statusText,
        body: errorBody,
      });

      const error = new Error(
        `Auth error: ${response.status} ${response.statusText} - ${errorMessage}`,
      );
      error.name = "AuthHTTPError";

      Sentry.captureException(error);
    });
  } catch (captureError) {
    console.error("[Auth] Failed to capture error to Sentry:", captureError);
  }
}

/**
 * Shared handler for auth requests to reduce duplication
 */
async function handleAuthRequest(
  request: Request,
  operation: "get" | "post",
  handler: (req: Request) => Promise<Response>,
) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  const method = request.method;

  return withSpan(
    `auth.${operation.toUpperCase()} ${pathname}`,
    async (span) => {
      const searchParams = Object.fromEntries(url.searchParams.entries());

      span.setAttributes({
        "http.method": method,
        "http.url": url.toString(),
        "http.target": pathname,
        "auth.path": pathname,
      });

      if (Object.keys(searchParams).length > 0) {
        span.setAttribute("http.query", JSON.stringify(searchParams));
      }

      addSpanEvent(span, "auth.request.start", { method, pathname });
      console.log(`[Auth] ${method} ${pathname} started`);

      try {
        const response = await handler(request);
        const statusCode = response.status;

        span.setAttribute("http.status_code", statusCode);
        addSpanEvent(span, "auth.request.complete", {
          status: statusCode,
        });

        console.log(
          `[Auth] ${method} ${pathname} completed with status ${statusCode}`,
        );

        // Capture HTTP error responses to Sentry
        if (statusCode >= 400) {
          span.setAttribute("error", true);
          await captureAuthErrorToSentry(response, pathname, method);
        }

        return response;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";
        const diagnosis = diagnoseDatabaseError(error);

        span.setAttribute("error", true);
        span.setAttribute("error.message", errorMessage);
        span.setAttribute("error.is_database_error", diagnosis.isDatabaseError);
        span.setAttribute("error.database_error_type", diagnosis.errorType);

        addSpanEvent(span, "auth.request.error", {
          error: errorMessage,
          isDatabaseError: diagnosis.isDatabaseError ? "1" : "0",
          errorType: diagnosis.errorType,
        });

        console.error(`[Auth] ${method} ${pathname} failed:`, {
          error: errorMessage,
          isDatabaseError: diagnosis.isDatabaseError,
          errorType: diagnosis.errorType,
          details: diagnosis.details,
        });

        // Capture thrown exceptions to Sentry with detailed diagnostic info
        Sentry.captureException(error, {
          tags: {
            "auth.endpoint": pathname,
            "auth.method": method,
            "error.type": diagnosis.isDatabaseError
              ? "database_error"
              : "auth_exception",
            "database.error_type": diagnosis.errorType,
          },
          extra: {
            isDatabaseError: diagnosis.isDatabaseError,
            errorType: diagnosis.errorType,
            diagnostic: diagnosis.details,
            errorMessage,
          },
          level: "error",
          contexts: {
            database: diagnosis.details,
            auth_request: {
              endpoint: pathname,
              method,
            },
          },
        });

        throw error;
      }
    },
    {
      attributes: {
        component: "auth-api",
        operation,
      },
      kind: "server",
    },
  );
}

export async function POST(request: Request) {
  return handleAuthRequest(request, "post", authPOST);
}

export async function GET(request: Request) {
  return handleAuthRequest(request, "get", authGET);
}
