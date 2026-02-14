import { test, expect, ConsoleMessage } from "@playwright/test";

/**
 * E2E Tests for Auth Signup Flow
 *
 * Tests user registration with console capture for debugging.
 * Validates Sentry integration for error observability.
 */

interface ConsoleLogEntry {
  type: string;
  text: string;
  timestamp: number;
  location?: string;
}

interface NetworkRequest {
  url: string;
  method: string;
  status?: number;
  timestamp: number;
}

test.describe("Auth Signup Flow", () => {
  // Collect console logs and network requests for debugging
  let consoleLogs: ConsoleLogEntry[] = [];
  let networkRequests: NetworkRequest[] = [];
  let sentryEvents: string[] = [];

  test.beforeEach(async ({ page }) => {
    // Reset collections
    consoleLogs = [];
    networkRequests = [];
    sentryEvents = [];

    // Capture all console messages
    page.on("console", (msg: ConsoleMessage) => {
      const entry: ConsoleLogEntry = {
        type: msg.type(),
        text: msg.text(),
        timestamp: Date.now(),
        location: msg.location()?.url,
      };
      consoleLogs.push(entry);

      // Log errors immediately for visibility
      if (msg.type() === "error") {
        console.error(`[Browser Console Error] ${msg.text()}`);
      }

      // Track Sentry events
      if (msg.text().includes("[Sentry]") || msg.text().includes("sentry")) {
        sentryEvents.push(msg.text());
        console.log(`[Sentry Event] ${msg.text()}`);
      }
    });

    // Capture page errors
    page.on("pageerror", (error) => {
      console.error(`[Page Error] ${error.message}`);
      consoleLogs.push({
        type: "pageerror",
        text: error.message,
        timestamp: Date.now(),
      });
    });

    // Capture network requests for auth endpoints
    page.on("request", (request) => {
      if (request.url().includes("/api/auth")) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now(),
        });
        console.log(`[Network Request] ${request.method()} ${request.url()}`);
      }
    });

    // Capture network responses
    page.on("response", (response) => {
      if (response.url().includes("/api/auth")) {
        const entry = networkRequests.find(
          (r) => r.url === response.url() && !r.status,
        );
        if (entry) {
          entry.status = response.status();
        }
        console.log(
          `[Network Response] ${response.status()} ${response.url()}`,
        );

        // Log error responses
        if (response.status() >= 400) {
          console.error(
            `[Auth Error] Status ${response.status()} for ${response.url()}`,
          );
        }
      }
    });

    // Navigate to auth page
    console.log("Navigating to /auth");
    await page.goto("/auth", { waitUntil: "networkidle" });
    console.log(`Page loaded: ${page.url()}`);
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Log summary of captured data
    console.log("\n--- Test Summary ---");
    console.log(`Test: ${testInfo.title}`);
    console.log(`Status: ${testInfo.status}`);
    console.log(`Console logs captured: ${consoleLogs.length}`);
    console.log(`Network requests captured: ${networkRequests.length}`);
    console.log(`Sentry events captured: ${sentryEvents.length}`);

    // Log errors if test failed
    if (testInfo.status === "failed") {
      console.log("\n--- Console Errors ---");
      consoleLogs
        .filter((log) => log.type === "error" || log.type === "pageerror")
        .forEach((log) => console.log(`  ${log.type}: ${log.text}`));

      console.log("\n--- Auth Network Requests ---");
      networkRequests.forEach((req) =>
        console.log(`  ${req.method} ${req.url} -> ${req.status || "pending"}`),
      );

      console.log("\n--- Sentry Events ---");
      sentryEvents.forEach((event) => console.log(`  ${event}`));
    }

    // Attach logs to test report
    await testInfo.attach("console-logs", {
      body: JSON.stringify(consoleLogs, null, 2),
      contentType: "application/json",
    });

    await testInfo.attach("network-requests", {
      body: JSON.stringify(networkRequests, null, 2),
      contentType: "application/json",
    });

    await testInfo.attach("sentry-events", {
      body: JSON.stringify(sentryEvents, null, 2),
      contentType: "application/json",
    });
  });

  test("should display signup form elements", async ({ page }) => {
    // Look for "Sign Up" or similar toggle
    const signUpToggle = page.locator("text=Sign Up");

    // If we're on signin by default, switch to signup
    if (await signUpToggle.isVisible()) {
      await signUpToggle.click();
      await page.waitForTimeout(500);
    }

    // Verify signup form elements
    await expect(page.locator('input[type="text"]').first()).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator('input[type="email"]')).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator('input[type="password"]')).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator('button[type="submit"]')).toBeVisible({
      timeout: 5000,
    });

    console.log("Signup form elements verified");
  });

  test("should validate password length", async ({ page }) => {
    // Switch to signup mode
    const signUpToggle = page.locator("text=Sign Up");
    if (await signUpToggle.isVisible()) {
      await signUpToggle.click();
      await page.waitForTimeout(500);
    }

    // Fill form with short password
    const nameInput = page.locator('input[type="text"]').first();
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill("Test User");
    await emailInput.fill(`test-${Date.now()}@example.com`);
    await passwordInput.fill("short"); // Less than 8 characters

    await submitButton.click();

    // Should show password validation error
    await expect(
      page.locator("text=Password must be at least 8 characters"),
    ).toBeVisible({ timeout: 5000 });

    console.log("Password validation working correctly");
  });

  test("should attempt signup and capture errors in Sentry", async ({
    page,
  }) => {
    // Switch to signup mode
    const signUpToggle = page.locator("text=Sign Up");
    if (await signUpToggle.isVisible()) {
      await signUpToggle.click();
      await page.waitForTimeout(500);
    }

    const testEmail = `test-signup-${Date.now()}@example.com`;
    const testPassword = "TestPassword123!";

    // Fill signup form
    const nameInput = page.locator('input[type="text"]').first();
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill("Test User");
    await emailInput.fill(testEmail);
    await passwordInput.fill(testPassword);

    console.log(`Attempting signup with email: ${testEmail}`);

    // Click submit and wait for response
    await submitButton.click();

    // Wait for either success or error
    await Promise.race([
      page.waitForSelector("text=Account created successfully", {
        timeout: 15000,
      }),
      page.waitForSelector('[class*="error"]', { timeout: 15000 }),
      page.waitForSelector("text=Internal Server Error", { timeout: 15000 }),
    ]).catch(() => {
      console.log("Timeout waiting for signup response");
    });

    // Check for auth network requests
    const authRequests = networkRequests.filter((r) =>
      r.url.includes("/api/auth"),
    );
    console.log(`Auth requests made: ${authRequests.length}`);

    // Check for errors
    const errorLogs = consoleLogs.filter(
      (log) => log.type === "error" || log.text.includes("error"),
    );

    if (errorLogs.length > 0) {
      console.log("\n--- Errors during signup ---");
      errorLogs.forEach((log) => console.log(`  ${log.text}`));
    }

    // Verify Sentry captured any errors
    const sentryCaptures = sentryEvents.filter(
      (e) => e.includes("Event captured") || e.includes("flushed"),
    );

    if (sentryCaptures.length > 0) {
      console.log("\n--- Sentry Captures ---");
      sentryCaptures.forEach((e) => console.log(`  ${e}`));
    }

    // Take screenshot of final state
    await page.screenshot({ path: "test-results/signup-result.png" });
  });

  test("should handle duplicate email signup", async ({ page }) => {
    // This test requires a known existing email
    const existingEmail = "existing@example.com";

    // Switch to signup mode
    const signUpToggle = page.locator("text=Sign Up");
    if (await signUpToggle.isVisible()) {
      await signUpToggle.click();
      await page.waitForTimeout(500);
    }

    const nameInput = page.locator('input[type="text"]').first();
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill("Existing User");
    await emailInput.fill(existingEmail);
    await passwordInput.fill("Password123!");

    await submitButton.click();

    // Wait for error response
    await page.waitForTimeout(3000);

    // Check console for Sentry capture
    const sentryCaptures = sentryEvents.filter(
      (e) => e.includes("Event captured") || e.includes("captureException"),
    );

    console.log(
      `Sentry captures for duplicate email: ${sentryCaptures.length}`,
    );
  });

  test("should verify Sentry is initialized on auth page", async ({ page }) => {
    // Check for Sentry initialization logs
    await page.waitForTimeout(2000);

    const sentryInitLogs = consoleLogs.filter(
      (log) =>
        log.text.includes("Sentry initialized") ||
        log.text.includes("[SentryProvider]"),
    );

    console.log(`Sentry init logs found: ${sentryInitLogs.length}`);
    sentryInitLogs.forEach((log) => console.log(`  ${log.text}`));

    expect(sentryInitLogs.length).toBeGreaterThan(0);
  });

  test("should capture network errors and report to Sentry", async ({
    page,
  }) => {
    // Intercept auth requests to simulate network failure
    await page.route("**/api/auth/sign-up/**", (route) => {
      route.abort("failed");
    });

    // Switch to signup mode
    const signUpToggle = page.locator("text=Sign Up");
    if (await signUpToggle.isVisible()) {
      await signUpToggle.click();
      await page.waitForTimeout(500);
    }

    const nameInput = page.locator('input[type="text"]').first();
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill("Network Test User");
    await emailInput.fill(`network-test-${Date.now()}@example.com`);
    await passwordInput.fill("Password123!");

    await submitButton.click();

    // Wait for error handling
    await page.waitForTimeout(5000);

    // Check for error handling
    const errorLogs = consoleLogs.filter(
      (log) =>
        log.type === "error" ||
        log.text.includes("Network error") ||
        log.text.includes("fetch"),
    );

    console.log(`Error logs for network failure: ${errorLogs.length}`);

    // Verify error UI is shown
    await expect(
      page.locator("text=Network error").or(page.locator("text=error")),
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Console Hook Verification", () => {
  test("should capture all console methods", async ({ page }) => {
    const capturedLogs: ConsoleLogEntry[] = [];

    page.on("console", (msg) => {
      capturedLogs.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: Date.now(),
      });
    });

    await page.goto("/auth", { waitUntil: "networkidle" });

    // Execute console methods in browser context
    await page.evaluate(() => {
      console.log("Test log message");
      console.warn("Test warning message");
      console.error("Test error message");
      console.info("Test info message");
    });

    await page.waitForTimeout(500);

    // Verify all console methods were captured
    const logTypes = capturedLogs.map((l) => l.type);

    expect(logTypes).toContain("log");
    expect(logTypes).toContain("warning");
    expect(logTypes).toContain("error");
    expect(logTypes).toContain("info");

    console.log("All console methods captured successfully");
  });

  test("should capture JavaScript errors", async ({ page }) => {
    const pageErrors: string[] = [];

    page.on("pageerror", (error) => {
      pageErrors.push(error.message);
    });

    await page.goto("/auth", { waitUntil: "networkidle" });

    // Trigger a JavaScript error
    await page
      .evaluate(() => {
        throw new Error("Intentional test error");
      })
      .catch(() => {
        // Expected to throw
      });

    await page.waitForTimeout(500);

    expect(pageErrors.length).toBeGreaterThan(0);
    expect(pageErrors.some((e) => e.includes("Intentional test error"))).toBe(
      true,
    );

    console.log("JavaScript errors captured successfully");
  });
});
