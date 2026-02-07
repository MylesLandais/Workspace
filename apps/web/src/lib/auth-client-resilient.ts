/**
 * Resilient Auth Client
 *
 * Wraps the auth client with circuit breakers, retry logic, and error handling
 */

import { signIn, signUp, signOut, useSession } from "./auth-client";
import { createCircuitBreaker } from "./resilience/circuit-breaker";
import { retry } from "./resilience/retry";
import { resilienceMonitor } from "./resilience/monitoring";
import { logError } from "./errorLogger";

// Create circuit breakers for auth operations
const signInBreaker = createCircuitBreaker("auth.signin", {
  failureThreshold: 5,
  resetTimeout: 60000, // 1 minute
  timeout: 30000, // 30 seconds
});

const signUpBreaker = createCircuitBreaker("auth.signup", {
  failureThreshold: 5,
  resetTimeout: 60000,
  timeout: 30000,
});

// Register for monitoring
resilienceMonitor.registerCircuitBreaker("auth.signin", signInBreaker);
resilienceMonitor.registerCircuitBreaker("auth.signup", signUpBreaker);

/**
 * Resilient sign in with retry and circuit breaker
 */
export async function resilientSignIn(
  params: Parameters<typeof signIn.email>[0],
) {
  return signInBreaker
    .execute(
      async () => {
        return retry(
          async () => {
            const result = await signIn.email(params);

            if (result.error) {
              const error = new Error(
                typeof result.error === "object" && result.error !== null
                  ? (result.error as any).message || String(result.error)
                  : String(result.error),
              );
              throw error;
            }

            return result;
          },
          {
            maxAttempts: 3,
            initialDelay: 1000,
            isRetryable: (error) => {
              // Retry on network errors and 5xx errors
              if (error instanceof Error) {
                const message = error.message.toLowerCase();
                return (
                  message.includes("network") ||
                  message.includes("timeout") ||
                  message.includes("fetch")
                );
              }
              return false;
            },
            onRetry: (attempt, error) => {
              resilienceMonitor.recordRetry(false);
              console.log(
                `[Resilient Auth] Retrying sign in (attempt ${attempt})`,
                {
                  error: error instanceof Error ? error.message : String(error),
                },
              );
            },
          },
        );
      },
      async () => {
        // Fallback when circuit is open
        logError(new Error("Auth service unavailable (circuit breaker open)"), {
          tags: {
            auth_flow: "signin",
            circuit_breaker: "open",
          },
        });

        return {
          error: {
            code: "SERVICE_UNAVAILABLE",
            message:
              "Authentication service is temporarily unavailable. Please try again later.",
          },
          data: null,
        };
      },
    )
    .then((result) => {
      resilienceMonitor.recordRetry(true);
      return result;
    })
    .catch((error) => {
      resilienceMonitor.recordError(error);
      throw error;
    });
}

/**
 * Resilient sign up with retry and circuit breaker
 */
export async function resilientSignUp(
  params: Parameters<typeof signUp.email>[0],
) {
  return signUpBreaker
    .execute(
      async () => {
        return retry(
          async () => {
            const result = await signUp.email(params);

            if (result.error) {
              const error = new Error(
                typeof result.error === "object" && result.error !== null
                  ? (result.error as any).message || String(result.error)
                  : String(result.error),
              );
              throw error;
            }

            return result;
          },
          {
            maxAttempts: 3,
            initialDelay: 1000,
            isRetryable: (error) => {
              if (error instanceof Error) {
                const message = error.message.toLowerCase();
                return (
                  message.includes("network") ||
                  message.includes("timeout") ||
                  message.includes("fetch")
                );
              }
              return false;
            },
            onRetry: (attempt, error) => {
              resilienceMonitor.recordRetry(false);
              console.log(
                `[Resilient Auth] Retrying sign up (attempt ${attempt})`,
                {
                  error: error instanceof Error ? error.message : String(error),
                },
              );
            },
          },
        );
      },
      async () => {
        // Fallback when circuit is open
        logError(new Error("Auth service unavailable (circuit breaker open)"), {
          tags: {
            auth_flow: "signup",
            circuit_breaker: "open",
          },
        });

        return {
          error: {
            code: "SERVICE_UNAVAILABLE",
            message:
              "Authentication service is temporarily unavailable. Please try again later.",
          },
          data: null,
        };
      },
    )
    .then((result) => {
      resilienceMonitor.recordRetry(true);
      return result;
    })
    .catch((error) => {
      resilienceMonitor.recordError(error);
      throw error;
    });
}

// Re-export other auth functions
export { signOut, useSession };
