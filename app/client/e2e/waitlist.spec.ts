import { test, expect } from "@playwright/test";

test.describe("Waitlist Form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display waitlist form on landing page", async ({ page }) => {
    const form = page.locator("form");
    const emailInput = page.locator('input[id="email"]');
    const nameInput = page.locator('input[id="name"]');
    const submitButton = page.locator('button[type="submit"]');

    await expect(form).toBeVisible();
    await expect(emailInput).toBeVisible();
    await expect(nameInput).toBeVisible();
    await expect(submitButton).toBeVisible();
  });

  test("should submit waitlist form successfully", async ({ page }) => {
    const testEmail = `test-${Date.now()}@example.com`;
    const testName = "Test User";

    const nameInput = page.locator('input[id="name"]');
    const emailInput = page.locator('input[id="email"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill(testName);
    await emailInput.fill(testEmail);

    await submitButton.click();

    await expect(
      page.locator("text=Success! We'll notify you when access is available.")
    ).toBeVisible({ timeout: 5000 });
  });

  test("should handle invalid email format", async ({ page }) => {
    const emailInput = page.locator('input[id="email"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill("invalid-email");
    await submitButton.click();

    await expect(page.locator("text=Invalid email")).toBeVisible({
      timeout: 5000,
    });
  });

  test("should reject duplicate email submission", async ({ page }) => {
    const testEmail = `duplicate-${Date.now()}@example.com`;

    const emailInput = page.locator('input[id="email"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill(testEmail);
    await submitButton.click();

    await expect(
      page.locator("text=Success! We'll notify you when access is available.")
    ).toBeVisible({ timeout: 5000 });

    const emailInput2 = page.locator('input[id="email"]');
    const submitButton2 = page.locator('button[type="submit"]');

    await emailInput2.fill(testEmail);
    await submitButton2.click();

    await expect(
      page.locator("text=You are already on the waitlist")
    ).toBeVisible({ timeout: 5000 });
  });

  test("should require email field", async ({ page }) => {
    const nameInput = page.locator('input[id="name"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill("Test User");

    const emailInput = page.locator('input[id="email"]');
    const isRequired = await emailInput.evaluate(
      (el: HTMLInputElement) => el.required
    );
    expect(isRequired).toBe(true);
  });

  test("should show loading state during submission", async ({ page }) => {
    const emailInput = page.locator('input[id="email"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill(`test-${Date.now()}@example.com`);

    await submitButton.click();

    await expect(submitButton).toContainText("Joining");
  });

  test("should clear form after successful submission", async ({ page }) => {
    const testEmail = `clear-test-${Date.now()}@example.com`;

    const nameInput = page.locator('input[id="name"]');
    const emailInput = page.locator('input[id="email"]');
    const submitButton = page.locator('button[type="submit"]');

    await nameInput.fill("Test User");
    await emailInput.fill(testEmail);
    await submitButton.click();

    await expect(
      page.locator("text=Success! We'll notify you when access is available.")
    ).toBeVisible({ timeout: 5000 });

    await expect(emailInput).toHaveValue("");
    await expect(nameInput).toHaveValue("");
  });

  test("should handle API errors gracefully", async ({ page }) => {
    const testEmail = `error-test-${Date.now()}@example.com`;

    await page.route("**/api/waitlist", (route) => {
      route.abort("failed");
    });

    const emailInput = page.locator('input[id="email"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill(testEmail);
    await submitButton.click();

    await expect(
      page.locator("text=An error occurred. Please try again.")
    ).toBeVisible({ timeout: 5000 });
  });
});
