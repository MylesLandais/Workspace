import { test, expect } from "@playwright/test";

test("landing page renders with auth form", async ({ page }) => {
  await page.goto("/");
  
  // Check for the main heading
  await expect(page.getByText("Bunny Project", { exact: false })).toBeVisible();
  
  // Check for the sign in form
  await expect(page.getByRole("heading", { name: "Access Bunny" })).toBeVisible();
});

test("can toggle to sign up and attempt registration", async ({ page }) => {
  await page.goto("/");
  
  await page.getByRole("button", { name: "Sign Up" }).click();
  
  await expect(page.getByRole("heading", { name: "Create Account" })).toBeVisible();
  
  await page.getByPlaceholder("John Doe").fill("Test User");
  await page.getByPlaceholder("name@example.com").fill(`test-${Date.now()}@example.com`);
  await page.getByPlaceholder("••••••••").fill("password123");
  
  await page.getByRole("button", { name: "Create Account", exact: true }).click();
  
  // Wait for redirect to feed
  await page.waitForURL("**/feed", { timeout: 10000 });
  await expect(page).toHaveURL(/.*feed/);
});
