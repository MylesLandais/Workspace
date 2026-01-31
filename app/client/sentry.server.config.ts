/**
 * Sentry Server Configuration for Next.js
 *
 * This file is automatically loaded by @sentry/nextjs for server-side initialization.
 * It runs in Node.js runtime (API routes, server components, etc.).
 */

import * as Sentry from "@sentry/nextjs";

const SENTRY_DSN =
  "https://460e27cb22c3b406da63b0e537a0b7cf@o4509979982823424.ingest.us.sentry.io/4509979988000768";

const isDevelopment = process.env.NODE_ENV === "development";

Sentry.init({
  dsn: SENTRY_DSN,
  environment: process.env.NODE_ENV || "development",

  // Keep Sentry enabled - network errors are likely intermittent
  enabled: true,

  // Disable Sentry's internal logging to prevent console spam
  enableLogs: false,
  debug: false,

  // Tracing
  tracesSampleRate: isDevelopment ? 0.1 : 1.0,

  // Log events being sent (for debugging)
  beforeSend(event, hint) {
    // Log that we're attempting to send an event
    if (isDevelopment) {
      console.log("[Sentry Server] 📤 Sending event:", {
        message: event.message,
        exception: event.exception?.values?.[0]?.value,
        tags: event.tags,
        eventId: event.event_id,
      });
    }
    return event;
  },
});

console.log("[Sentry Server] ✅ Initialized", {
  dsn: SENTRY_DSN ? "Present" : "Missing",
  environment: process.env.NODE_ENV || "development",
  client: Sentry.getClient() ? "Connected" : "Not connected",
});
