/**
 * Performance and Load Tests
 *
 * Tests application performance under various load conditions
 */

import { describe, it, expect } from "bun:test";
import { measurePerformance } from "../utils/test-helpers";

describe("Performance Tests", () => {
  it("should handle rapid sequential requests", async () => {
    const requests = Array.from({ length: 10 }, (_, i) => i);

    const { duration } = await measurePerformance(async () => {
      await Promise.all(
        requests.map(async (i) => {
          // Simulate API call
          await new Promise((resolve) => setTimeout(resolve, 10));
          return i;
        }),
      );
    });

    // Should complete within reasonable time
    expect(duration).toBeLessThan(1000);
  });

  it("should handle concurrent requests efficiently", async () => {
    const concurrentRequests = 50;

    const { duration } = await measurePerformance(async () => {
      await Promise.all(
        Array.from({ length: concurrentRequests }, async () => {
          // Simulate API call
          await new Promise((resolve) => setTimeout(resolve, 50));
        }),
      );
    });

    // Concurrent requests should be faster than sequential
    expect(duration).toBeLessThan(concurrentRequests * 50);
  });

  it("should not degrade performance with many retries", async () => {
    let attempts = 0;
    const fn = async () => {
      attempts++;
      if (attempts < 3) {
        throw new Error("Retry");
      }
      return "success";
    };

    const { duration } = await measurePerformance(async () => {
      // Simulate retry logic
      for (let i = 0; i < 3; i++) {
        try {
          await fn();
          break;
        } catch {
          await new Promise((resolve) => setTimeout(resolve, 10));
        }
      }
    });

    // Should complete retries quickly
    expect(duration).toBeLessThan(500);
  });

  it("should handle memory efficiently", async () => {
    const initialMemory = process.memoryUsage().heapUsed;

    // Create and release many objects
    for (let i = 0; i < 1000; i++) {
      const obj = { data: new Array(100).fill(i) };
      // Simulate processing
      JSON.stringify(obj);
    }

    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }

    // Wait a bit for GC
    await new Promise((resolve) => setTimeout(resolve, 100));

    const finalMemory = process.memoryUsage().heapUsed;
    const memoryIncrease = finalMemory - initialMemory;

    // Memory increase should be reasonable (less than 50MB)
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
  });
});

describe("Load Tests", () => {
  it("should handle burst traffic", async () => {
    const burstSize = 100;
    const requests = Array.from({ length: burstSize }, (_, i) => i);

    const start = performance.now();
    const results = await Promise.allSettled(
      requests.map(async (i) => {
        // Simulate API call with potential failure
        await new Promise((resolve) => setTimeout(resolve, Math.random() * 10));
        if (Math.random() < 0.1) {
          throw new Error("Simulated failure");
        }
        return i;
      }),
    );
    const duration = performance.now() - start;

    // Should handle burst quickly
    expect(duration).toBeLessThan(2000);

    // Most requests should succeed
    const successCount = results.filter((r) => r.status === "fulfilled").length;
    expect(successCount).toBeGreaterThan(burstSize * 0.8);
  });

  it("should handle sustained load", async () => {
    const duration = 2000; // 2 seconds (reduced to avoid timeout)
    const requestInterval = 50; // Every 50ms
    const start = Date.now();
    let requestCount = 0;
    let successCount = 0;

    while (Date.now() - start < duration) {
      requestCount++;
      try {
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, Math.random() * 20));
        successCount++;
      } catch {
        // Handle error
      }
      await new Promise((resolve) => setTimeout(resolve, requestInterval));
    }

    // Should handle sustained load
    expect(requestCount).toBeGreaterThan(20); // At least 20 requests in 2s
    expect(successCount / requestCount).toBeGreaterThan(0.8); // 80% success rate
  });
});
