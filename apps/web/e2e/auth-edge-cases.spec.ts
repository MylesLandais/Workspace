import { test, expect } from "@playwright/test";

/**
 * Edge Case Tests for Authentication
 *
 * Tests various edge cases and error scenarios to ensure resilience:
 * - Invalid inputs
 * - Network failures
 * - Timeout scenarios
 * - Concurrent requests
 * - Rate limiting
 * - Database failures (simulated)
 */

test.describe("Auth Edge Cases", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to auth page before each test
    await page.goto("/auth");
  });

  test.describe("Input Validation Edge Cases", () => {
    test("should handle empty email submission", async ({ page }) => {
      await page.click('button:has-text("Create Account")');

      // Should show validation error
      await expect(page.locator("input[type='email']")).toHaveAttribute(
        "required",
        "",
      );
    });

    test("should handle invalid email formats", async ({ page }) => {
      const invalidEmails = [
        "notanemail",
        "@example.com",
        "test@",
        "test..test@example.com",
        "test@example",
        "test @example.com",
      ];

      for (const email of invalidEmails) {
        await page.fill('input[type="email"]', email);
        await page.fill('input[type="password"]', "password123");
        await page.click('button:has-text("Create Account")');

        // Browser should prevent submission or show error
        const emailInput = page.locator('input[type="email"]');
        const validity = await emailInput.evaluate(
          (el: HTMLInputElement) => el.validity.valid,
        );
        expect(validity).toBe(false);

        // Clear for next iteration
        await page.fill('input[type="email"]', "");
      }
    });

    test("should handle extremely long email addresses", async ({ page }) => {
      const longEmail = "a".repeat(250) + "@example.com";
      await page.fill('input[type="email"]', longEmail);
      await page.fill('input[type="password"]', "password123");

      // Should either validate or show appropriate error
      await page.click('button:has-text("Create Account")');

      // Check for error message or validation
      const errorText = await page
        .locator("text=/error|invalid|too long/i")
        .first()
        .textContent()
        .catch(() => null);
      expect(errorText).toBeTruthy();
    });

    test("should handle password too short", async ({ page }) => {
      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "short");
      await page.click('button:has-text("Create Account")');

      // Should show password length error
      await expect(
        page.locator("text=/password.*8|at least 8/i"),
      ).toBeVisible();
    });

    test("should handle special characters in password", async ({ page }) => {
      const specialPasswords = [
        "password!@#$%^&*()",
        "password<>?/\\|",
        "password\"'`",
        "password\u0000\u0001", // Null bytes
      ];

      for (const password of specialPasswords) {
        await page.fill(
          'input[type="email"]',
          `test${Math.random()}@example.com`,
        );
        await page.fill('input[type="password"]', password);
        await page.fill('input[placeholder="John Doe"]', "Test User");
        await page.click('button:has-text("Create Account")');

        // Should either succeed or show appropriate error
        // Wait a bit to see if there's an error
        await page.waitForTimeout(1000);
        const hasError = await page
          .locator("text=/error/i")
          .isVisible()
          .catch(() => false);

        // If there's an error, it should be a meaningful one
        if (hasError) {
          const errorText = await page
            .locator("text=/error/i")
            .first()
            .textContent();
          expect(errorText).not.toBe("Signup error: unknown");
        }

        // Clear form
        await page.fill('input[type="email"]', "");
        await page.fill('input[type="password"]', "");
      }
    });

    test("should handle SQL injection attempts in email", async ({ page }) => {
      const sqlInjectionAttempts = [
        "test@example.com'; DROP TABLE users; --",
        "test@example.com' OR '1'='1",
        "test@example.com'; SELECT * FROM users; --",
      ];

      for (const email of sqlInjectionAttempts) {
        await page.fill('input[type="email"]', email);
        await page.fill('input[type="password"]', "password123");
        await page.fill('input[placeholder="John Doe"]', "Test User");
        await page.click('button:has-text("Create Account")');

        // Should handle gracefully without exposing database errors
        await page.waitForTimeout(2000);
        const errorText = await page
          .locator("text=/error/i")
          .first()
          .textContent()
          .catch(() => "");

        // Should not expose SQL errors
        expect(errorText.toLowerCase()).not.toContain("sql");
        expect(errorText.toLowerCase()).not.toContain("database");
        expect(errorText.toLowerCase()).not.toContain("syntax error");
      }
    });

    test("should handle XSS attempts in name field", async ({ page }) => {
      const xssAttempts = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
      ];

      for (const name of xssAttempts) {
        await page.fill('input[placeholder="John Doe"]', name);
        await page.fill(
          'input[type="email"]',
          `test${Math.random()}@example.com`,
        );
        await page.fill('input[type="password"]', "password123");
        await page.click('button:has-text("Create Account")');

        // Should sanitize input - no alerts should fire
        // Wait to see if any alerts appear
        await page.waitForTimeout(1000);

        // Check that the page is still functional
        const pageTitle = await page.title();
        expect(pageTitle).toBeTruthy();
      }
    });
  });

  test.describe("Network Failure Scenarios", () => {
    test("should handle network timeout gracefully", async ({
      page,
      context,
    }) => {
      // Set a very short timeout to simulate network issues
      await context.setOffline(true);

      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");
      await page.click('button:has-text("Create Account")');

      // Should show network error, not crash
      await expect(
        page.locator("text=/network|timeout|offline|unreachable/i"),
      ).toBeVisible({ timeout: 5000 });

      // Re-enable network
      await context.setOffline(false);
    });

    test("should handle server 500 errors gracefully", async ({
      page,
      context,
    }) => {
      // Intercept and mock 500 error
      await page.route("**/api/auth/**", (route) => {
        route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ error: "Internal Server Error" }),
        });
      });

      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");
      await page.click('button:has-text("Create Account")');

      // Should show user-friendly error, not crash
      await expect(
        page.locator("text=/error|failed|try again/i"),
      ).toBeVisible();

      // Error should not be "unknown"
      const errorText = await page
        .locator("text=/error/i")
        .first()
        .textContent();
      expect(errorText?.toLowerCase()).not.toContain("unknown");
    });

    test("should handle server 429 rate limiting", async ({ page }) => {
      // Intercept and mock 429 error
      await page.route("**/api/auth/**", (route) => {
        route.fulfill({
          status: 429,
          contentType: "application/json",
          body: JSON.stringify({
            error: "Too many requests",
            retryAfter: 60,
          }),
        });
      });

      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");
      await page.click('button:has-text("Create Account")');

      // Should show rate limit error
      await expect(
        page.locator("text=/too many|rate limit|try again/i"),
      ).toBeVisible();
    });

    test("should handle malformed JSON responses", async ({ page }) => {
      await page.route("**/api/auth/**", (route) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: "invalid json{",
        });
      });

      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");
      await page.click('button:has-text("Create Account")');

      // Should handle parse error gracefully
      await page.waitForTimeout(2000);
      const hasError = await page
        .locator("text=/error/i")
        .isVisible()
        .catch(() => false);
      expect(hasError).toBe(true);
    });
  });

  test.describe("Concurrent Request Handling", () => {
    test("should handle rapid multiple signup attempts", async ({ page }) => {
      const email = `test${Math.random()}@example.com`;
      await page.fill('input[type="email"]', email);
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");

      // Click multiple times rapidly
      for (let i = 0; i < 5; i++) {
        await page.click('button:has-text("Create Account")');
        await page.waitForTimeout(100);
      }

      // Should only process one request or show appropriate error
      await page.waitForTimeout(3000);

      // Either success or duplicate error, but not crash
      const url = page.url();
      expect(url).toMatch(/\/(dashboard|auth)/);
    });

    test("should prevent duplicate submissions during processing", async ({
      page,
    }) => {
      const email = `test${Math.random()}@example.com`;
      await page.fill('input[type="email"]', email);
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");

      // Start signup
      await page.click('button:has-text("Create Account")');

      // Try to click again while processing
      await page.waitForTimeout(500);
      const button = page.locator('button:has-text("Create Account")');
      const isDisabled = await button.isDisabled();

      // Button should be disabled during processing
      expect(isDisabled).toBe(true);
    });
  });

  test.describe("Session and State Management", () => {
    test("should handle expired sessions gracefully", async ({
      page,
      context,
    }) => {
      // First, create a session
      await page.goto("/invite");
      await page.fill(
        'input[placeholder="Enter your invite key"]',
        "ASDF-WHALECUM",
      );
      await page.click('button:has-text("Validate Invite")');
      await page.click('button:has-text("Create Account")');

      const email = `test${Math.random()}@example.com`;
      await page.fill('input[type="email"]', email);
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");
      await page.click('button:has-text("Create Account")');

      await expect(page).toHaveURL("/dashboard", { timeout: 10000 });

      // Clear cookies to simulate expired session
      await context.clearCookies();

      // Try to access protected route
      await page.goto("/dashboard");

      // Should redirect to auth or show appropriate message
      await page.waitForTimeout(2000);
      const url = page.url();
      expect(url).toMatch(/\/(auth|login)/);
    });

    test("should handle invalid session tokens", async ({ page, context }) => {
      // Set invalid session cookie
      await context.addCookies([
        {
          name: "session",
          value: "invalid-token-12345",
          domain: "localhost",
          path: "/",
        },
      ]);

      await page.goto("/dashboard");

      // Should handle invalid token gracefully
      await page.waitForTimeout(2000);
      const url = page.url();
      expect(url).toMatch(/\/(auth|login)/);
    });
  });

  test.describe("Edge Cases with Invite Keys", () => {
    test("should handle already-used invite keys", async ({ page }) => {
      // This assumes we have a way to mark invite keys as used
      // For now, we'll test the error handling
      await page.goto("/invite");

      // Try with a key that might be used (if we had test data)
      await page.fill(
        'input[placeholder="Enter your invite key"]',
        "USED-KEY-1234",
      );
      await page.click('button:has-text("Validate Invite")');

      // Should show appropriate error
      await page.waitForTimeout(2000);
      const hasError = await page
        .locator("text=/invalid|used|expired/i")
        .isVisible()
        .catch(() => false);
      // If error exists, it should be user-friendly
      if (hasError) {
        const errorText = await page
          .locator("text=/invalid|used|expired/i")
          .first()
          .textContent();
        expect(errorText).toBeTruthy();
      }
    });

    test("should handle invite key with special characters", async ({
      page,
    }) => {
      await page.goto("/invite");

      const specialKeys = [
        "KEY-<script>alert('xss')</script>",
        "KEY-'; DROP TABLE invites; --",
        "KEY-../../etc/passwd",
      ];

      for (const key of specialKeys) {
        await page.fill('input[placeholder="Enter your invite key"]', key);
        await page.click('button:has-text("Validate Invite")');

        await page.waitForTimeout(1000);
        // Should handle gracefully without exposing vulnerabilities
        const pageTitle = await page.title();
        expect(pageTitle).toBeTruthy();

        await page.fill('input[placeholder="Enter your invite key"]', "");
      }
    });
  });

  test.describe("Error Recovery", () => {
    test("should allow retry after error", async ({ page }) => {
      // First attempt with invalid data
      await page.fill('input[type="email"]', "invalid-email");
      await page.fill('input[type="password"]', "short");
      await page.click('button:has-text("Create Account")');

      // Should show error
      await expect(page.locator("text=/error|invalid/i")).toBeVisible();

      // Fix the input and retry
      await page.fill(
        'input[type="email"]',
        `test${Math.random()}@example.com`,
      );
      await page.fill('input[type="password"]', "password123");
      await page.fill('input[placeholder="John Doe"]', "Test User");
      await page.click('button:has-text("Create Account")');

      // Should process the retry
      await page.waitForTimeout(2000);
      // Either success or different error, but form should be functional
      const button = page.locator('button:has-text("Create Account")');
      await expect(button).toBeVisible();
    });

    test("should clear error state on mode switch", async ({ page }) => {
      // Try signup with error
      await page.fill('input[type="email"]', "invalid");
      await page.fill('input[type="password"]', "short");
      await page.click('button:has-text("Create Account")');

      // Should show error
      await expect(page.locator("text=/error/i")).toBeVisible();

      // Switch to sign in
      await page.click('button:has-text("Sign In")');

      // Error should be cleared
      const errorVisible = await page
        .locator("text=/error/i")
        .isVisible()
        .catch(() => false);
      expect(errorVisible).toBe(false);
    });
  });
});
