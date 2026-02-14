/**
 * Performance Monitoring Utilities
 *
 * Tracks and measures performance metrics for development and production.
 *
 * Features:
 * - Measure synchronous and async function execution time
 * - Track metrics by name
 * - Calculate statistics (avg, min, max)
 * - Development mode logging
 *
 * @module lib/utils/performance
 */

import { performance } from "perf_hooks";

const metrics = new Map<string, number[]>();

/**
 * Measure synchronous function performance
 *
 * @param name - Metric name for tracking
 * @param fn - Function to measure
 * @returns Function result
 */
export function measurePerformance<T>(name: string, fn: () => T): T {
  const start = performance.now();
  const result = fn();
  const duration = performance.now() - start;

  if (!metrics.has(name)) {
    metrics.set(name, []);
  }
  metrics.get(name)!.push(duration);

  if (process.env.NODE_ENV === "development") {
    console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms`);
  }

  return result;
}

export async function measureAsyncPerformance<T>(
  name: string,
  fn: () => Promise<T>,
): Promise<T> {
  const start = performance.now();
  const result = await fn();
  const duration = performance.now() - start;

  if (!metrics.has(name)) {
    metrics.set(name, []);
  }
  metrics.get(name)!.push(duration);

  if (process.env.NODE_ENV === "development") {
    console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms`);
  }

  return result;
}

export function getMetrics() {
  const result: Record<
    string,
    { avg: number; min: number; max: number; count: number }
  > = {};

  metrics.forEach((durations, name) => {
    const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
    const min = Math.min(...durations);
    const max = Math.max(...durations);

    result[name] = {
      avg: parseFloat(avg.toFixed(2)),
      min: parseFloat(min.toFixed(2)),
      max: parseFloat(max.toFixed(2)),
      count: durations.length,
    };
  });

  return result;
}

export function logMetrics() {
  const metricsData = getMetrics();
  console.table(metricsData);
}

export function clearMetrics() {
  metrics.clear();
}
