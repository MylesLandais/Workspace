import { test, expect } from "@playwright/test";
test("simple test", async ({ page }) => {
  await page.goto("about:blank");
  expect(true).toBe(true);
});
