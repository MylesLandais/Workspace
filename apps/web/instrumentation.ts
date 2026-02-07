import * as Sentry from "@sentry/nextjs";

export async function register() {
  const SENTRY_DSN =
    "https://460e27cb22c3b406da63b0e537a0b7cf@o4509979982823424.ingest.us.sentry.io/4509979988000768";

  // Initialize Sentry for server-side error tracking
  if (process.env.NEXT_RUNTIME === "nodejs") {
    Sentry.init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV || "development",
      enableLogs: true, // Enable logs to see what's happening
      tracesSampleRate: 1.0,
      debug: process.env.NODE_ENV === "development", // Enable debug in dev
      // Log events being sent (for debugging)
      beforeSend(event, hint) {
        if (process.env.NODE_ENV === "development") {
          console.log("[Sentry Server] Attempting to send event:", {
            message: event.message,
            exception: event.exception?.values?.[0]?.value,
            tags: event.tags,
          });
        }
        return event;
      },
    });

    console.log("[Sentry] Server-side initialized successfully", {
      dsn: SENTRY_DSN ? "Present" : "Missing",
      environment: process.env.NODE_ENV || "development",
    });

    try {
      await import("./src/lib/tracing/instrumentation.node");
    } catch (error) {
      // Silently ignore missing instrumentation file
    }
  }

  // Initialize Sentry for edge runtime
  if (process.env.NEXT_RUNTIME === "edge") {
    Sentry.init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV || "development",
      enableLogs: true,
      tracesSampleRate: 1.0,
      debug: process.env.NODE_ENV === "development",
      beforeSend(event, hint) {
        if (process.env.NODE_ENV === "development") {
          console.log("[Sentry Edge] Attempting to send event:", {
            message: event.message,
            exception: event.exception?.values?.[0]?.value,
            tags: event.tags,
          });
        }
        return event;
      },
    });

    console.log("[Sentry] Edge runtime initialized successfully");
  }
}
