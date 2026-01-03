import { test, expect } from "@playwright/test";

test("User can sign up and sign out", async ({ page }) => {
  // 1. Go to home page
  await page.goto("/");

  // 2. Click "Sign Up" toggle
  await page.click("text=Sign Up");

  // 3. Fill out the form
  const randomId = Math.random().toString(36).substring(7);
  const email = `testuser_${randomId}@example.com`;
  const password = "password123";
  const name = `Test User ${randomId}`;

  await page.fill('input[placeholder="John Doe"]', name);
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  // 4. Submit
  await page.click('button:has-text("Create Account")');

  // 5. Expect redirect to /feed
  await expect(page).toHaveURL("/feed", { timeout: 10000 });

  // 6. Verify User Menu is present (using the avatar/button selector)
  const userMenuButton = page.locator("button.rounded-full.border.border-white\\/10");
  await expect(userMenuButton).toBeVisible();

  // 7. Click User Menu to open dropdown
  await userMenuButton.click();

  // 8. Click Sign Out
  await page.click("text=Sign Out");

  // 9. Expect redirect back to home /
  await expect(page).toHaveURL("/");
});
