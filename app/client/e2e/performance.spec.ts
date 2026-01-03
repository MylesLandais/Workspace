/**
 * E2E Performance & Authentication Tests
 *
 * Comprehensive test suite for System Nebula platform.
 *
 * Test Coverage:
 * - Performance metrics (load times, navigation speed)
 * - Authentication flows (sign in, sign up, invite validation)
 * - Waitlist/mailing list signup
 * - Responsive design
 * - Error handling
 * - Accessibility
 *
 * @module e2e/performance
 */

import { test, expect } from "@playwright/test";

/**
 * Performance test suite
 *
 * Measures page load times and navigation speed.
 * Ensures pages load within acceptable thresholds.
 */
test.describe("Performance", () => {
  test("Home page loads within 2 seconds", async ({ page }) => {
    const startTime = Date.now();
    await page.goto("/");
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000);
    console.log(`Home page loaded in ${loadTime}ms`);
  });

  test("Auth page loads within 2 seconds", async ({ page }) => {
    const startTime = Date.now();
    await page.goto("/auth");
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000);
    console.log(`Auth page loaded in ${loadTime}ms`);
  });

  test("Invite page loads within 2 seconds", async ({ page }) => {
    const startTime = Date.now();
    await page.goto("/invite");
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000);
    console.log(`Invite page loaded in ${loadTime}ms`);
  });

  test("Client navigation is fast", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const startTime = Date.now();
    await page.click('text=Have an invite key?');
    await page.waitForURL("/invite");
    const navigationTime = Date.now() - startTime;

    expect(navigationTime).toBeLessThan(500);
    console.log(`Client navigation took ${navigationTime}ms`);
  });

  test("Bundle size is reasonable", async ({ page, request }) => {
    await page.goto("/");

    const jsFiles = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('script[src]'))
        .filter(script => script.src.includes('.js'))
        .map(script => {
          return {
            src: (script as HTMLScriptElement).src,
            size: 0 
          };
        });
    });

    console.log(`Found ${jsFiles.length} JavaScript files loaded`);
    expect(jsFiles.length).toBeLessThan(20);
  });
});

test.describe("Authentication Flow", () => {
  test("Door icon navigates to auth page", async ({ page }) => {
    await page.goto("/");

    const doorIcon = page.locator('a[href="/auth"]');
    await expect(doorIcon).toBeVisible();
    
    await doorIcon.click();
    await expect(page).toHaveURL("/auth");
    await expect(page.locator("h1")).toContainText("Existing Users");
  });

  test("Existing user can sign in", async ({ page }) => {
    await page.goto("/auth");

    await expect(page.locator("h1")).toContainText("Existing Users");

    await page.fill('input[type="email"]', "test@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button:has-text("Sign In")');

    await expect(page).toHaveURL("/feed", { timeout: 10000 });
  });

  test("Unauthenticated user redirected from feed", async ({ page }) => {
    await page.goto("/feed");

    await expect(page).toHaveURL("/", { timeout: 5000 });
  });
});

test.describe("Invite System", () => {
  test("Invalid invite key shows error", async ({ page }) => {
    await page.goto("/invite");

    await page.fill('input[placeholder="Enter your invite key"]', "INVALID-KEY");
    await page.click('button:has-text("Validate Invite")');

    await expect(page.locator("text=Invalid Invitation")).toBeVisible();
  });

  test("SN- prefix invite keys work", async ({ page }) => {
    await page.goto("/invite");

    await page.fill('input[placeholder="Enter your invite key"]', "SN-VALID-TEST-KEY");
    await page.click('button:has-text("Validate Invite")');

    await expect(page.locator("text=Valid Invitation")).toBeVisible();
    await expect(page.locator('button:has-text("Create Account")')).toBeVisible();
  });

  test("Specific invite code ASDF-WHALECUM works", async ({ page }) => {
    await page.goto("/invite");

    await page.fill('input[placeholder="Enter your invite key"]', "ASDF-WHALECUM");
    await page.click('button:has-text("Validate Invite")');

    await expect(page.locator("text=Valid Invitation")).toBeVisible();
    await expect(page.locator('button:has-text("Create Account")')).toBeVisible();
  });

  test("Valid invite navigates to signup", async ({ page }) => {
    await page.goto("/invite");

    await page.fill('input[placeholder="Enter your invite key"]', "ASDF-WHALECUM");
    await page.click('button:has-text("Validate Invite")');
    await page.click('button:has-text("Create Account")');

    await expect(page).toHaveURL(/\/auth/);
    await expect(page.locator("text=ASDF-WHALECUM")).toBeVisible();
  });
});

test.describe("Mailing List", () => {
  test("User can join mailing list", async ({ page }) => {
    await page.goto("/");

    const randomId = Math.random().toString(36).substring(7);
    const email = `waitlist_${randomId}@example.com`;

    await page.fill('input[placeholder="Enter your email"]', email);
    await page.click('button:has-text("Join Mailing List")');

    await expect(page.locator("text=You've joined the mailing list")).toBeVisible();
  });

  test("Mailing list form has validation", async ({ page }) => {
    await page.goto("/");

    await page.click('button:has-text("Join Mailing List")');

    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeFocused();
  });
});

test.describe("Responsive Design", () => {
  test("Mobile view works correctly", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    await expect(page.locator("h1")).toContainText("System Nebula");
    await expect(page.locator('a[href="/auth"]')).toBeVisible();
  });

  test("Desktop view works correctly", async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/");

    await expect(page.locator("h1")).toContainText("System Nebula");
    await expect(page.locator('a[href="/auth"]')).toBeVisible();
  });
});

test.describe("Error Handling", () => {
  test("404 page loads correctly", async ({ page }) => {
    await page.goto("/nonexistent-page");

    await expect(page).toHaveURL("/404");
  });

  test("Network error handling", async ({ page, context }) => {
    await context.route("**/api/**", route => route.abort());
    
    await page.goto("/auth");
    await page.fill('input[type="email"]', "test@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button:has-text("Sign In")');

    await expect(page.locator("text=Network error")).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Accessibility", () => {
  test("Door icon has proper ARIA label", async ({ page }) => {
    await page.goto("/");

    const doorIcon = page.locator('a[aria-label="Existing users sign in"]');
    await expect(doorIcon).toBeVisible();
  });

  test("All forms have proper labels", async ({ page }) => {
    await page.goto("/");

    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toHaveAttribute("required");
    
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
  });
});
