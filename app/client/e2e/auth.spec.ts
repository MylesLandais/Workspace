import { test, expect } from "@playwright/test";

test("Home page displays correctly and collects emails", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("h1")).toContainText("System Nebula");
  await expect(page.locator("text=Under Construction")).toBeVisible();
  await expect(page.locator("text=Community pages coming soon")).toBeVisible();

  const randomId = Math.random().toString(36).substring(7);
  const email = `waitlist_${randomId}@example.com`;

  await page.fill('input[placeholder="Enter your email"]', email);
  await page.click('button:has-text("Join Mailing List")');

  await expect(page.locator("text=You've joined the mailing list")).toBeVisible();
});

test("Invite key validation flow", async ({ page }) => {
  await page.goto("/");

  await page.click("text=Have an invite key?");

  await expect(page).toHaveURL("/invite");
  await expect(page.locator("h1")).toContainText("Have an invite key?");

  const invalidKey = "INVALID-KEY-1234";
  await page.fill('input[placeholder="Enter your invite key"]', invalidKey);
  await page.click('button:has-text("Validate Invite")');

  await expect(page.locator("text=Invalid Invitation")).toBeVisible();
  await page.click('button:has-text("Try Again")');

  await page.fill('input[placeholder="Enter your invite key"]', "SN-TEST-1234-ABCD");
  await page.click('button:has-text("Validate Invite")');

  await expect(page.locator("text=Valid Invitation")).toBeVisible();
  await expect(page.locator("button:has-text('Create Account')")).toBeVisible();
});

test("User can sign up with invite key and sign out", async ({ page }) => {
  await page.goto("/invite");

  await page.fill('input[placeholder="Enter your invite key"]', "ASDF-WHALECUM");
  await page.click('button:has-text("Validate Invite")');
  await page.click('button:has-text("Create Account")');

  await expect(page).toHaveURL(/\/auth/);
  await expect(page.locator("text=ASDF-WHALECUM")).toBeVisible();

  const randomId = Math.random().toString(36).substring(7);
  const email = `testuser_${randomId}@example.com`;
  const password = "password123";
  const name = `Test User ${randomId}`;

  await page.fill('input[placeholder="John Doe"]', name);
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  await page.click('button:has-text("Create Account")');

  await expect(page).toHaveURL("/feed", { timeout: 10000 });

  const userMenuButton = page.locator("button.rounded-full.border.border-white\\/10");
  await expect(userMenuButton).toBeVisible();

  await userMenuButton.click();
  await page.click("text=Sign Out");

  await expect(page).toHaveURL("/");
});

test("Existing user can sign in via door icon", async ({ page }) => {
  await page.goto("/");

  const doorIcon = page.locator('a[href="/auth"]');
  await expect(doorIcon).toBeVisible();
  await doorIcon.click();

  await expect(page).toHaveURL("/auth");
  await expect(page.locator("h1")).toContainText("Existing Users");
});
