/**
 * Circuit Breaker Pattern Implementation
 *
 * Prevents cascading failures by stopping requests to failing services
 * and allowing them to recover.
 */

export interface CircuitBreakerOptions {
  /** Number of failures before opening the circuit */
  failureThreshold: number;
  /** Time in ms to wait before attempting to close the circuit */
  resetTimeout: number;
  /** Time in ms to wait before considering a request timed out */
  timeout: number;
  /** Optional callback when circuit opens */
  onOpen?: (error: Error) => void;
  /** Optional callback when circuit closes */
  onClose?: () => void;
}

export enum CircuitState {
  CLOSED = "closed", // Normal operation
  OPEN = "open", // Circuit is open, failing fast
  HALF_OPEN = "half-open", // Testing if service recovered
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private lastFailureTime: number | null = null;
  private successCount = 0;
  private readonly options: Required<CircuitBreakerOptions>;

  constructor(options: Partial<CircuitBreakerOptions> = {}) {
    this.options = {
      failureThreshold: options.failureThreshold ?? 5,
      resetTimeout: options.resetTimeout ?? 60000, // 1 minute
      timeout: options.timeout ?? 30000, // 30 seconds
      onOpen: options.onOpen ?? (() => {}),
      onClose: options.onClose ?? (() => {}),
    };
  }

  /**
   * Execute a function with circuit breaker protection
   */
  async execute<T>(
    fn: () => Promise<T>,
    fallback?: () => Promise<T>,
  ): Promise<T> {
    // Check if circuit should transition
    this.updateState();

    // If circuit is open, fail fast
    if (this.state === CircuitState.OPEN) {
      const error = new Error("Circuit breaker is OPEN");
      if (fallback) {
        return fallback();
      }
      throw error;
    }

    // Execute with timeout
    try {
      const result = await Promise.race([
        fn(),
        new Promise<never>((_, reject) =>
          setTimeout(
            () => reject(new Error("Circuit breaker timeout")),
            this.options.timeout,
          ),
        ),
      ]);

      // Success - reset failure count
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error as Error);
      if (fallback) {
        return fallback();
      }
      throw error;
    }
  }

  private updateState(): void {
    const now = Date.now();

    if (this.state === CircuitState.OPEN) {
      // Check if reset timeout has passed
      if (
        this.lastFailureTime &&
        now - this.lastFailureTime >= this.options.resetTimeout
      ) {
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      }
    } else if (this.state === CircuitState.HALF_OPEN) {
      // If we've had enough successes in half-open, close the circuit
      if (this.successCount >= 2) {
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
        this.options.onClose();
      }
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.lastFailureTime = null;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
    }
  }

  private onFailure(error: Error): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.options.failureThreshold) {
      if (this.state !== CircuitState.OPEN) {
        this.state = CircuitState.OPEN;
        this.options.onOpen(error);
      }
    }
  }

  /**
   * Get current circuit state
   */
  getState(): CircuitState {
    this.updateState();
    return this.state;
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
    };
  }

  /**
   * Manually reset the circuit breaker
   */
  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = null;
  }
}

/**
 * Create a circuit breaker for a specific service
 */
export function createCircuitBreaker(
  serviceName: string,
  options?: Partial<CircuitBreakerOptions>,
): CircuitBreaker {
  const breaker = new CircuitBreaker({
    ...options,
    onOpen: (error) => {
      console.warn(`[Circuit Breaker] ${serviceName} circuit OPEN`, {
        error: error.message,
        metrics: breaker.getMetrics(),
      });
      options?.onOpen?.(error);
    },
    onClose: () => {
      console.log(`[Circuit Breaker] ${serviceName} circuit CLOSED`);
      options?.onClose?.();
    },
  });

  return breaker;
}
