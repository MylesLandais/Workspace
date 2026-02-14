"use client";

import { ReactNode, useEffect } from "react";
import * as Sentry from "@sentry/nextjs";
import { logError } from "@/lib/errorLogger";

const SENTRY_DSN =
  "https://460e27cb22c3b406da63b0e537a0b7cf@o4509979982823424.ingest.us.sentry.io/4509979988000768";

// Track initialization state to prevent multiple initializations
let isInitialized = false;

/**
 * Setup console filtering to silence Sentry transport errors
 * This must run BEFORE Sentry initialization to catch early errors
 */
const setupConsoleFiltering = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  // Check if already set up
  if (
    (window as unknown as { __sentryConsoleFilterSetup?: boolean })
      .__sentryConsoleFilterSetup
  ) {
    return;
  }

  (
    window as unknown as { __sentryConsoleFilterSetup?: boolean }
  ).__sentryConsoleFilterSetup = true;

  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;

  const shouldFilter = (message: unknown): boolean => {
    if (typeof message === "string") {
      const lowerMessage = message.toLowerCase();
      return (
        lowerMessage.includes("sentry logger") ||
        lowerMessage.includes("encountered error running transport") ||
        lowerMessage.includes("error while sending envelope") ||
        lowerMessage.includes("networkerror when attempting to fetch") ||
        lowerMessage.includes("networkerror") ||
        lowerMessage.includes("transport request") ||
        lowerMessage.includes("sending envelope") ||
        (lowerMessage.includes("[error]:") &&
          lowerMessage.includes("sentry")) ||
        (lowerMessage.includes("sentry") &&
          lowerMessage.includes("networkerror")) ||
        (lowerMessage.includes("sentry") &&
          lowerMessage.includes("fetch resource"))
      );
    }
    if (message && typeof message === "object") {
      const obj = message as Record<string, unknown>;
      if ("message" in obj) {
        const msg = String(obj.message || "");
        if (shouldFilter(msg)) return true;
      }
      if ("stack" in obj) {
        const stack = String(obj.stack || "");
        if (shouldFilter(stack)) return true;
      }
      const objString = JSON.stringify(obj).toLowerCase();
      if (
        objString.includes("sentry") &&
        (objString.includes("networkerror") || objString.includes("transport"))
      ) {
        return true;
      }
    }
    return false;
  };

  const errorFilter = (...args: unknown[]): void => {
    for (const arg of args) {
      if (shouldFilter(arg)) {
        return; // Silently ignore Sentry transport errors
      }
    }
    originalConsoleError(...args);
  };

  const warnFilter = (...args: unknown[]): void => {
    for (const arg of args) {
      if (shouldFilter(arg)) {
        return; // Silently ignore Sentry warnings
      }
    }
    originalConsoleWarn(...args);
  };

  // Override console methods early to catch Sentry errors
  console.error = errorFilter;
  console.warn = warnFilter;
};

/**
 * Initialize Sentry synchronously at module load time (client-side only)
 * This ensures Sentry is available before any component code runs.
 */
const initializeSentry = (): void => {
  // Only run on client-side
  if (typeof window === "undefined") {
    return;
  }

  // If already initialized, skip
  if (isInitialized) {
    return;
  }

  // Check if already initialized by Sentry itself
  const existingClient = Sentry.getClient();
  if (existingClient) {
    console.log(
      "[SentryProvider] ✅ Sentry already initialized (found existing client)",
    );
    isInitialized = true;
    return;
  }

  try {
    console.log("[SentryProvider] 🔧 Initializing Sentry synchronously...");

    const isDevelopment = process.env.NODE_ENV === "development";

    Sentry.init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV || "development",
      // Keep Sentry enabled - it was working before, so network errors are likely intermittent
      enabled: true,
      // Disable Sentry's internal logger to prevent console spam from transport errors
      // This prevents "Sentry Logger [error]" messages from appearing
      enableLogs: false,
      debug: false,
      tracesSampleRate: isDevelopment ? 1.0 : 1.0, // 100% in dev to see all signin attempts
      sampleRate: isDevelopment ? 1.0 : 1.0,
      integrations: [
        Sentry.replayIntegration({
          maskAllText: true,
          blockAllMedia: true,
        }),
        Sentry.feedbackIntegration({
          colorScheme: "system",
          // Auto-inject floating feedback button (can be disabled per-component)
          autoInject: true,
          // Default form configuration
          triggerLabel: "Report Issue",
          formTitle: "Report a Problem",
          submitButtonLabel: "Send Report",
          messagePlaceholder: "Please describe what happened...",
          isEmailRequired: false,
          showName: false,
          enableScreenshot: true,
        }),
      ],
      replaysSessionSampleRate: isDevelopment ? 0.1 : 0.1,
      replaysOnErrorSampleRate: isDevelopment ? 1.0 : 1.0,
      beforeSend(event, hint) {
        if (isDevelopment) {
          console.log("[Sentry Client] 📤 Sending event:", {
            eventId: event.event_id,
            message:
              event.message ||
              event.exception?.values?.[0]?.value ||
              "No message",
            tags: event.tags,
          });
        }
        return event;
      },
      // Ignore Sentry's own transport errors to prevent infinite loops
      ignoreErrors: [
        "NetworkError when attempting to fetch resource",
        "Failed to fetch",
        "Encountered error running transport request",
        "Error while sending envelope",
        "TypeError: NetworkError when attempting to fetch resource",
      ],
    });

    const client = Sentry.getClient();
    if (client) {
      isInitialized = true;
      console.log("[SentryProvider] ✅ Sentry initialized successfully", {
        dsn: SENTRY_DSN ? "Present" : "Missing",
        environment: process.env.NODE_ENV || "development",
        client: "Connected",
      });
    } else {
      console.error(
        "[SentryProvider] ❌ Sentry.init() called but getClient() returned null",
      );
    }
  } catch (error) {
    console.error("[SentryProvider] ❌ Failed to initialize Sentry:", error);
  }
};

// Setup console filtering FIRST, then initialize Sentry
// This ensures we catch any Sentry errors that occur during initialization
if (typeof window !== "undefined") {
  setupConsoleFiltering();
  initializeSentry();
}

/**
 * Setup global error handlers (must run after window is available)
 */
const setupGlobalHandlers = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  // Prevent multiple setups
  if (
    (window as unknown as { __sentryHandlersSetup?: boolean })
      .__sentryHandlersSetup
  ) {
    return;
  }

  (
    window as unknown as { __sentryHandlersSetup?: boolean }
  ).__sentryHandlersSetup = true;
  console.log("[SentryProvider] ✅ Setting up global error handlers");

  // Console filtering is already set up in setupConsoleFiltering() above
  // No need to set it up again here

  // Global error handler - capture ALL unhandled errors
  window.addEventListener(
    "error",
    (event) => {
      // Don't block Sentry transport errors
      if (
        event.message?.includes("NetworkError") ||
        event.message?.includes("transport") ||
        (event.message?.includes("Sentry") &&
          !event.message?.includes("Error Captured"))
      ) {
        event.preventDefault();
        return;
      }

      // Capture ALL other errors
      logError(event.error || new Error(event.message), {
        tags: {
          error_type: "unhandled_error",
          filename: event.filename || "unknown",
          lineno: String(event.lineno || "unknown"),
          colno: String(event.colno || "unknown"),
        },
      });
    },
    true,
  ); // Use capture phase to catch errors early

  // Global unhandled rejection handler - capture ALL promise rejections
  window.addEventListener("unhandledrejection", (event) => {
    const error = event.reason;
    const errorMessage = error?.message || String(error);

    // Don't block Sentry transport errors
    if (
      errorMessage.includes("NetworkError when attempting to fetch") ||
      errorMessage.includes("Failed to fetch") ||
      (errorMessage.includes("transport") &&
        !errorMessage.includes("Error Captured"))
    ) {
      event.preventDefault();
      return;
    }

    // Capture ALL other rejections
    logError(error, {
      tags: {
        error_type: "unhandled_rejection",
      },
    });
  });
};

/**
 * SentryProvider - Sets up global error handlers
 *
 * Note: Sentry is initialized synchronously at module load time (above),
 * so it's available before any components render.
 */
export function SentryProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    // Setup global handlers after component mounts
    setupGlobalHandlers();

    // Double-check initialization in case it failed earlier
    const client = Sentry.getClient();
    if (!client && typeof window !== "undefined") {
      console.warn("[SentryProvider] ⚠️ Sentry not initialized, retrying...");
      initializeSentry();
    }
  }, []);

  return <>{children}</>;
}
