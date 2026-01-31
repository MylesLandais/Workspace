/**
 * Sentry Helper with Feature Flag Integration
 *
 * Wraps Sentry functions to respect feature flags for controlling
 * error reporting and testing capabilities.
 */

import * as Sentry from "@sentry/bun";
import { isFeatureEnabled, getAllFlags, type FlagMap } from "./featureFlags.js";
import logger from "./logger.js";

const SENTRY_DSN =
  "https://460e27cb22c3b406da63b0e537a0b7cf@o4509979982823424.ingest.us.sentry.io/4509979988000768";

/**
 * Initialize Sentry with feature flag support
 */
export function initSentry(): void {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: process.env.NODE_ENV || "development",
    enableLogs: true,
    tracesSampleRate: 1.0,
    debug: true,
    // Use beforeSend to check flags dynamically at the moment of the error
    beforeSend(event) {
      if (!isFeatureEnabled("ops.sentry.enabled", true)) {
        // Drop the event if the flag is off
        logger.debug("Sentry event dropped: ops.sentry.enabled is false");
        return null;
      }
      return event;
    },
    // Also check flags when setting up breadcrumbs
    beforeBreadcrumb(breadcrumb) {
      if (!isFeatureEnabled("ops.sentry.enabled", true)) {
        return null;
      }
      return breadcrumb;
    },
  });

  logger.info("Sentry initialized with feature flag support");
}

/**
 * Capture an exception with feature flag check
 *
 * @param error - The error to capture
 * @param context - Optional additional context to attach
 */
export function captureException(
  error: unknown,
  context?: {
    tags?: Record<string, string>;
    extra?: Record<string, unknown>;
    user?: Sentry.User;
  },
): void {
  if (!isFeatureEnabled("ops.sentry.enabled", true)) {
    logger.debug(
      "Sentry captureException skipped: ops.sentry.enabled is false",
    );
    return;
  }

  Sentry.withScope((scope) => {
    // Attach feature flag states as tags for debugging
    const currentFlags = getAllFlags();
    scope.setTag(
      "feature_flags_enabled",
      Object.keys(currentFlags).length.toString(),
    );

    // Attach flag states (only enabled flags to reduce noise)
    Object.entries(currentFlags).forEach(([key, flag]) => {
      if (flag.enabled) {
        scope.setTag(`flag.${key}`, "true");
      }
    });

    // Attach any custom tags
    if (context?.tags) {
      Object.entries(context.tags).forEach(([key, value]) => {
        scope.setTag(key, value);
      });
    }

    // Attach any extra context
    if (context?.extra) {
      Object.entries(context.extra).forEach(([key, value]) => {
        scope.setExtra(key, value);
      });
    }

    // Set user context if provided
    if (context?.user) {
      scope.setUser(context.user);
    }

    Sentry.captureException(error);
  });
}

/**
 * Capture an exception with full feature flag context
 *
 * This is more comprehensive - it attaches all flag states (enabled and disabled)
 * which is useful for debugging which features were active when an error occurred.
 */
export function captureExceptionWithContext(error: unknown): void {
  if (!isFeatureEnabled("ops.sentry.enabled", true)) {
    logger.debug(
      "Sentry captureExceptionWithContext skipped: ops.sentry.enabled is false",
    );
    return;
  }

  Sentry.withScope((scope) => {
    // Attach the current state of all flags to this error report
    const currentFlags = getAllFlags();

    // Sentry tags are key/value pairs searchable in the dashboard
    Object.entries(currentFlags).forEach(([key, flag]) => {
      scope.setTag(`flag.${key}`, flag.enabled.toString());
    });

    Sentry.captureException(error);
  });
}

/**
 * Set user context for Sentry
 */
export function setUser(user: Sentry.User | null): void {
  if (!isFeatureEnabled("ops.sentry.enabled", true)) {
    return;
  }
  Sentry.setUser(user);
}

/**
 * Add breadcrumb to Sentry
 */
export function addBreadcrumb(breadcrumb: Sentry.Breadcrumb): void {
  if (!isFeatureEnabled("ops.sentry.enabled", true)) {
    return;
  }
  Sentry.addBreadcrumb(breadcrumb);
}
