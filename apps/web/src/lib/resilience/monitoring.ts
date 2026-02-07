/**
 * Resilience Monitoring
 *
 * Tracks metrics and health for resilience patterns
 */

import { withSpan, addSpanEvent } from "@/lib/tracing/tracer";
import { CircuitBreaker } from "./circuit-breaker";
import * as Sentry from "@sentry/nextjs";

export interface ResilienceMetrics {
  circuitBreaker: {
    state: string;
    failureCount: number;
    successCount: number;
  };
  retry: {
    totalAttempts: number;
    successfulRetries: number;
    failedRetries: number;
  };
  errors: {
    total: number;
    byType: Record<string, number>;
  };
}

class ResilienceMonitor {
  private metrics: ResilienceMetrics = {
    circuitBreaker: {
      state: "closed",
      failureCount: 0,
      successCount: 0,
    },
    retry: {
      totalAttempts: 0,
      successfulRetries: 0,
      failedRetries: 0,
    },
    errors: {
      total: 0,
      byType: {},
    },
  };

  private circuitBreakers = new Map<string, CircuitBreaker>();

  /**
   * Register a circuit breaker for monitoring
   */
  registerCircuitBreaker(name: string, breaker: CircuitBreaker): void {
    this.circuitBreakers.set(name, breaker);
  }

  /**
   * Record a retry attempt
   */
  recordRetry(success: boolean): void {
    this.metrics.retry.totalAttempts++;
    if (success) {
      this.metrics.retry.successfulRetries++;
    } else {
      this.metrics.retry.failedRetries++;
    }
  }

  /**
   * Record an error
   */
  recordError(error: Error): void {
    this.metrics.errors.total++;
    const errorType = error.constructor.name;
    this.metrics.errors.byType[errorType] =
      (this.metrics.errors.byType[errorType] || 0) + 1;
  }

  /**
   * Get current metrics
   */
  getMetrics(): ResilienceMetrics {
    // Update circuit breaker metrics
    const breakerStates: string[] = [];
    let totalFailures = 0;
    let totalSuccesses = 0;

    for (const [name, breaker] of this.circuitBreakers.entries()) {
      const metrics = breaker.getMetrics();
      breakerStates.push(`${name}:${metrics.state}`);
      totalFailures += metrics.failureCount;
      totalSuccesses += metrics.successCount;
    }

    return {
      ...this.metrics,
      circuitBreaker: {
        state: breakerStates.join(", ") || "none",
        failureCount: totalFailures,
        successCount: totalSuccesses,
      },
    };
  }

  /**
   * Report metrics to Sentry
   */
  async reportMetrics(): Promise<void> {
    const metrics = this.getMetrics();

    await withSpan("resilience.metrics.report", async (span) => {
      span.setAttributes({
        "resilience.circuit_breaker.state": metrics.circuitBreaker.state,
        "resilience.circuit_breaker.failures":
          metrics.circuitBreaker.failureCount,
        "resilience.circuit_breaker.successes":
          metrics.circuitBreaker.successCount,
        "resilience.retry.total": metrics.retry.totalAttempts,
        "resilience.retry.successful": metrics.retry.successfulRetries,
        "resilience.retry.failed": metrics.retry.failedRetries,
        "resilience.errors.total": metrics.errors.total,
      });

      addSpanEvent(span, "resilience.metrics", {
        metrics: JSON.stringify(metrics),
      });

      // Send to Sentry as a message (not an error)
      Sentry.captureMessage("Resilience metrics", {
        level: "info",
        tags: {
          metric_type: "resilience",
        },
        extra: metrics,
      });
    });
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    this.metrics = {
      circuitBreaker: {
        state: "closed",
        failureCount: 0,
        successCount: 0,
      },
      retry: {
        totalAttempts: 0,
        successfulRetries: 0,
        failedRetries: 0,
      },
      errors: {
        total: 0,
        byType: {},
      },
    };
  }
}

// Singleton instance
export const resilienceMonitor = new ResilienceMonitor();

// Report metrics periodically (every 5 minutes)
if (typeof window !== "undefined") {
  setInterval(
    () => {
      resilienceMonitor.reportMetrics().catch(console.error);
    },
    5 * 60 * 1000,
  );
}
