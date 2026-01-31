/**
 * Sentry Client Configuration for Next.js
 *
 * NOTE: This file is NOT used for initialization. Sentry is initialized
 * synchronously in SentryProvider.tsx at module load time to ensure it's
 * available before any components render.
 *
 * This file is kept for compatibility with @sentry/nextjs but initialization
 * is disabled to avoid conflicts with SentryProvider.
 */

import * as Sentry from "@sentry/nextjs";

// DISABLED: Initialization moved to SentryProvider.tsx for synchronous loading
// The config file auto-loading was not reliable, so we initialize directly
// in the provider component at module load time.

// If you need to re-enable this, remove the initialization from SentryProvider.tsx
// and uncomment the code below. However, this may cause timing issues where
// Sentry is not initialized when components check getClient().

/*
const SENTRY_DSN =
  "https://460e27cb22c3b406da63b0e537a0b7cf@o4509979982823424.ingest.us.sentry.io/4509979988000768";

Sentry.init({
  dsn: SENTRY_DSN,
  environment: process.env.NODE_ENV || "development",
  enableLogs: true,
  debug: process.env.NODE_ENV === "development",
  tracesSampleRate: 1.0,
  sampleRate: 1.0,
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  beforeSend(event, hint) {
    if (process.env.NODE_ENV === "development") {
      console.log("[Sentry Client] 📤 Sending event:", {
        eventId: event.event_id,
        message: event.message || event.exception?.values?.[0]?.value || "No message",
        tags: event.tags,
        environment: event.environment,
      });
    }
    return event;
  },
  beforeBreadcrumb(breadcrumb) {
    return breadcrumb;
  },
  ignoreErrors: [
    "NetworkError when attempting to fetch resource",
    "Failed to fetch",
    "Encountered error running transport request",
    "Error while sending envelope",
  ],
});
*/
