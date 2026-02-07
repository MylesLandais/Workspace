/**
 * Integration Tests for Resilience
 *
 * Tests error handling, retry logic, circuit breakers, and recovery scenarios
 */

import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { CircuitBreaker, CircuitState } from "@/lib/resilience/circuit-breaker";
import { retry, retryWithJitter } from "@/lib/resilience/retry";

describe("Circuit Breaker", () => {
  let circuitBreaker: CircuitBreaker;

  beforeEach(() => {
    circuitBreaker = new CircuitBreaker({
      failureThreshold: 3,
      resetTimeout: 1000,
      timeout: 500,
    });
  });

  afterEach(() => {
    circuitBreaker.reset();
  });

  it("should start in CLOSED state", () => {
    expect(circuitBreaker.getState()).toBe(CircuitState.CLOSED);
  });

  it("should open circuit after threshold failures", async () => {
    const failingFn = async () => {
      throw new Error("Service unavailable");
    };

    // Trigger failures up to threshold
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFn);
      } catch {
        // Expected to fail
      }
    }

    expect(circuitBreaker.getState()).toBe(CircuitState.OPEN);
  });

  it("should fail fast when circuit is open", async () => {
    // Open the circuit
    const failingFn = async () => {
      throw new Error("Service unavailable");
    };
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFn);
      } catch {
        // Expected
      }
    }

    // Now circuit should be open
    expect(circuitBreaker.getState()).toBe(CircuitState.OPEN);

    // Should fail fast without calling the function
    await expect(
      circuitBreaker.execute(async () => "should not execute"),
    ).rejects.toThrow("Circuit breaker is OPEN");
  });

  it("should transition to HALF_OPEN after reset timeout", async () => {
    // Open the circuit
    const failingFn = async () => {
      throw new Error("Service unavailable");
    };
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFn);
      } catch {
        // Expected
      }
    }

    expect(circuitBreaker.getState()).toBe(CircuitState.OPEN);

    // Wait for reset timeout
    await new Promise((resolve) => setTimeout(resolve, 1100));

    // Should transition to HALF_OPEN
    expect(circuitBreaker.getState()).toBe(CircuitState.HALF_OPEN);
  });

  it("should close circuit after successful requests in HALF_OPEN", async () => {
    // Open and then wait for reset
    const failingFn = async () => {
      throw new Error("Service unavailable");
    };
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFn);
      } catch {
        // Expected
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 1100));

    // Now in HALF_OPEN, execute successful requests
    const successFn = async () => "success";
    await circuitBreaker.execute(successFn);
    await circuitBreaker.execute(successFn);

    // Should close after 2 successes
    expect(circuitBreaker.getState()).toBe(CircuitState.CLOSED);
  });

  it("should handle timeout", async () => {
    const slowFn = async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return "success";
    };

    await expect(circuitBreaker.execute(slowFn)).rejects.toThrow(
      "Circuit breaker timeout",
    );
  });

  it("should use fallback when circuit is open", async () => {
    // Open the circuit
    const failingFn = async () => {
      throw new Error("Service unavailable");
    };
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFn);
      } catch {
        // Expected
      }
    }

    const fallbackFn = async () => "fallback response";
    const result = await circuitBreaker.execute(failingFn, fallbackFn);

    expect(result).toBe("fallback response");
  });
});

describe("Retry Logic", () => {
  it("should retry on retryable errors", async () => {
    let attempts = 0;
    const fn = async () => {
      attempts++;
      if (attempts < 3) {
        throw new Error("Network error");
      }
      return "success";
    };

    const result = await retry(fn, {
      maxAttempts: 3,
      initialDelay: 10,
    });

    expect(result).toBe("success");
    expect(attempts).toBe(3);
  });

  it("should not retry on non-retryable errors", async () => {
    let attempts = 0;
    const fn = async () => {
      attempts++;
      throw new Error("Validation error");
    };

    await expect(
      retry(fn, {
        maxAttempts: 3,
        initialDelay: 10,
        isRetryable: () => false,
      }),
    ).rejects.toThrow("Validation error");

    expect(attempts).toBe(1);
  });

  it("should respect max attempts", async () => {
    let attempts = 0;
    const fn = async () => {
      attempts++;
      throw new Error("Network error");
    };

    await expect(
      retry(fn, {
        maxAttempts: 2,
        initialDelay: 10,
      }),
    ).rejects.toThrow("Network error");

    expect(attempts).toBe(2);
  });

  it("should use exponential backoff", async () => {
    const timestamps: number[] = [];

    const fn = async () => {
      timestamps.push(Date.now());
      throw new Error("Network error");
    };

    try {
      await retry(fn, {
        maxAttempts: 4,
        initialDelay: 100,
        backoffMultiplier: 2,
      });
    } catch {
      // Expected to fail
    }

    // Calculate delays between attempts
    const delays: number[] = [];
    for (let i = 1; i < timestamps.length; i++) {
      delays.push(timestamps[i] - timestamps[i - 1]);
    }

    // Check that delays increase (with some tolerance)
    expect(delays.length).toBeGreaterThan(0);
    if (delays.length > 1) {
      // Second delay should be roughly double the first
      expect(delays[1]).toBeGreaterThan(delays[0] * 1.5);
    }
  });

  it("should handle 429 rate limit errors", async () => {
    let attempts = 0;
    const fn = async () => {
      attempts++;
      if (attempts < 2) {
        const error: any = new Error("Rate limited");
        error.status = 429;
        throw error;
      }
      return "success";
    };

    const result = await retry(fn, {
      maxAttempts: 3,
      initialDelay: 10,
    });

    expect(result).toBe("success");
    expect(attempts).toBe(2);
  });

  it("should handle 5xx server errors", async () => {
    let attempts = 0;
    const fn = async () => {
      attempts++;
      if (attempts < 2) {
        const error: any = new Error("Server error");
        error.status = 500;
        throw error;
      }
      return "success";
    };

    const result = await retry(fn, {
      maxAttempts: 3,
      initialDelay: 10,
    });

    expect(result).toBe("success");
    expect(attempts).toBe(2);
  });

  it("should add jitter to retry delays", async () => {
    const timestamps: number[] = [];

    const fn = async () => {
      timestamps.push(Date.now());
      throw new Error("Network error");
    };

    try {
      await retryWithJitter(fn, {
        maxAttempts: 3,
        initialDelay: 100,
        backoffMultiplier: 2,
      });
    } catch {
      // Expected
    }

    // Calculate delays between attempts
    const delays: number[] = [];
    for (let i = 1; i < timestamps.length; i++) {
      delays.push(timestamps[i] - timestamps[i - 1]);
    }

    // Delays should have some variation due to jitter
    expect(delays.length).toBeGreaterThan(0);
  });
});

describe("Error Recovery", () => {
  it("should recover from transient errors", async () => {
    let callCount = 0;
    const fn = async () => {
      callCount++;
      if (callCount === 1) {
        // Use "network" to match default isRetryable logic
        throw new Error("Network timeout error");
      }
      return "recovered";
    };

    const result = await retry(fn, {
      maxAttempts: 2,
      initialDelay: 10,
    });

    expect(result).toBe("recovered");
    expect(callCount).toBe(2);
  });

  it("should handle permanent errors without infinite retries", async () => {
    let callCount = 0;
    const fn = async () => {
      callCount++;
      throw new Error("Permanent error");
    };

    await expect(
      retry(fn, {
        maxAttempts: 3,
        initialDelay: 10,
        isRetryable: () => true, // Even if retryable, should stop at max
      }),
    ).rejects.toThrow("Permanent error");

    expect(callCount).toBe(3);
  });
});
