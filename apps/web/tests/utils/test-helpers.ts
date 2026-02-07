/**
 * Test Utilities and Helpers
 *
 * Common utilities for testing edge cases and resilience scenarios
 */

import { Page } from "@playwright/test";

/**
 * Wait for network to be idle with timeout
 */
export async function waitForNetworkIdle(
  page: Page,
  timeout = 5000,
): Promise<void> {
  await page.waitForLoadState("networkidle", { timeout });
}

/**
 * Generate random test data
 */
export function generateTestEmail(prefix = "test"): string {
  return `${prefix}_${Math.random().toString(36).substring(2, 11)}@example.com`;
}

export function generateTestPassword(length = 12): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
  return Array.from({ length }, () =>
    chars.charAt(Math.floor(Math.random() * chars.length)),
  ).join("");
}

export function generateTestName(): string {
  return `Test User ${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Mock network conditions
 */
export async function simulateSlowNetwork(
  page: Page,
  downloadThroughput = 500 * 1024, // 500 KB/s
  uploadThroughput = 500 * 1024,
  latency = 500,
): Promise<void> {
  const context = page.context();
  await context.route("**/*", async (route) => {
    // Add artificial delay
    await new Promise((resolve) => setTimeout(resolve, latency));
    await route.continue();
  });
}

export async function simulateOffline(page: Page): Promise<void> {
  await page.context().setOffline(true);
}

export async function simulateOnline(page: Page): Promise<void> {
  await page.context().setOffline(false);
}

/**
 * Intercept and mock API responses
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  response: {
    status?: number;
    body?: unknown;
    headers?: Record<string, string>;
  },
): Promise<void> {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status: response.status || 200,
      contentType: "application/json",
      headers: response.headers || {},
      body: JSON.stringify(response.body || {}),
    });
  });
}

/**
 * Wait for error message to appear
 */
export async function waitForErrorMessage(
  page: Page,
  timeout = 5000,
): Promise<string | null> {
  try {
    const errorElement = await page.waitForSelector(
      "text=/error|failed|invalid/i",
      { timeout },
    );
    return await errorElement.textContent();
  } catch {
    return null;
  }
}

/**
 * Check if element is visible and contains text
 * Note: This requires Playwright's expect to be imported in the test file
 */
export async function expectVisibleWithText(
  page: Page,
  selector: string,
  text: string | RegExp,
): Promise<boolean> {
  const element = page.locator(selector);
  const isVisible = await element.isVisible();
  if (!isVisible) return false;

  const elementText = await element.textContent();
  if (typeof text === "string") {
    return elementText?.includes(text) ?? false;
  } else {
    return text.test(elementText ?? "");
  }
}

/**
 * Fill form with validation
 */
export async function fillFormSafely(
  page: Page,
  fields: Record<string, string>,
): Promise<void> {
  for (const [selector, value] of Object.entries(fields)) {
    const input = page.locator(selector);
    await input.fill(value);
    // Verify value was set
    const actualValue = await input.inputValue();
    if (actualValue !== value) {
      throw new Error(
        `Failed to set value for ${selector}. Expected: ${value}, Got: ${actualValue}`,
      );
    }
  }
}

/**
 * Test SQL injection patterns
 */
export const SQL_INJECTION_PATTERNS = [
  "'; DROP TABLE users; --",
  "' OR '1'='1",
  "'; SELECT * FROM users; --",
  "admin'--",
  "' UNION SELECT * FROM users--",
];

/**
 * Test XSS patterns
 */
export const XSS_PATTERNS = [
  "<script>alert('xss')</script>",
  "<img src=x onerror=alert('xss')>",
  "javascript:alert('xss')",
  "<svg onload=alert('xss')>",
  "<iframe src=javascript:alert('xss')>",
];

/**
 * Test path traversal patterns
 */
export const PATH_TRAVERSAL_PATTERNS = [
  "../../etc/passwd",
  "..\\..\\windows\\system32",
  "....//....//etc/passwd",
  "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
];

/**
 * Measure performance of an action
 */
export async function measurePerformance<T>(
  fn: () => Promise<T>,
): Promise<{ result: T; duration: number }> {
  const start = performance.now();
  const result = await fn();
  const end = performance.now();
  return { result, duration: end - start };
}

/**
 * Retry an action with exponential backoff
 */
export async function retryAction<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  delay = 1000,
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt < maxAttempts - 1) {
        await new Promise((resolve) =>
          setTimeout(resolve, delay * Math.pow(2, attempt)),
        );
      }
    }
  }
  throw lastError;
}

/**
 * Capture console errors
 */
export async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });
  return errors;
}

/**
 * Capture network failures
 */
export async function captureNetworkFailures(
  page: Page,
): Promise<Array<{ url: string; status: number }>> {
  const failures: Array<{ url: string; status: number }> = [];
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failures.push({
        url: response.url(),
        status: response.status(),
      });
    }
  });
  return failures;
}
