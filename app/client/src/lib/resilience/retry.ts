/**
 * Retry Utility with Exponential Backoff
 *
 * Provides configurable retry logic for resilient API calls
 */

export interface RetryOptions {
  /** Maximum number of retry attempts */
  maxAttempts: number;
  /** Initial delay in milliseconds */
  initialDelay: number;
  /** Maximum delay in milliseconds */
  maxDelay: number;
  /** Multiplier for exponential backoff */
  backoffMultiplier: number;
  /** Function to determine if error is retryable */
  isRetryable?: (error: unknown) => boolean;
  /** Optional callback for each retry attempt */
  onRetry?: (attempt: number, error: unknown) => void;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  isRetryable: (error) => {
    // Retry on network errors, 5xx errors, and rate limits
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      if (
        message.includes("network") ||
        message.includes("timeout") ||
        message.includes("fetch")
      ) {
        return true;
      }
    }

    // Check if it's an HTTP error response
    if (typeof error === "object" && error !== null && "status" in error) {
      const status = (error as { status: number }).status;
      return status >= 500 || status === 429;
    }

    return false;
  },
  onRetry: () => {},
};

/**
 * Retry a function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {},
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: unknown;

  for (let attempt = 0; attempt < opts.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Check if error is retryable
      if (!opts.isRetryable(error)) {
        throw error;
      }

      // Don't retry on last attempt
      if (attempt === opts.maxAttempts - 1) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        opts.initialDelay * Math.pow(opts.backoffMultiplier, attempt),
        opts.maxDelay,
      );

      opts.onRetry(attempt + 1, error);

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Retry with jitter to prevent thundering herd
 */
export async function retryWithJitter<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {},
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  return retry(fn, {
    ...opts,
    onRetry: (attempt, error) => {
      // Add random jitter to delay
      const baseDelay =
        opts.initialDelay * Math.pow(opts.backoffMultiplier, attempt - 1);
      const jitter = Math.random() * baseDelay * 0.3; // 30% jitter
      const delay = Math.min(baseDelay + jitter, opts.maxDelay);

      opts.onRetry?.(attempt, error);
    },
  });
}

/**
 * Create a retry wrapper for a function
 */
export function withRetry<TArgs extends unknown[], TReturn>(
  fn: (...args: TArgs) => Promise<TReturn>,
  options?: Partial<RetryOptions>,
): (...args: TArgs) => Promise<TReturn> {
  return async (...args: TArgs) => {
    return retry(() => fn(...args), options);
  };
}
