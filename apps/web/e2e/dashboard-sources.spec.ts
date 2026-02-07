import { test, expect } from "@playwright/test";

test.describe("Dashboard Sources Integration", () => {
  test.beforeEach(async ({ page }) => {
    // Listen for console errors
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        console.log(`Browser Error: ${msg.text()}`);
      }
    });

    // Listen for page errors
    page.on("pageerror", (error) => {
      console.log(`Page Error: ${error.message}`);
      console.log(error.stack);
    });
  });

  test("should load dashboard without errors", async ({ page }) => {
    await page.goto("http://localhost:3000/dashboard");

    // Wait for page to be ready
    await page.waitForLoadState("networkidle", { timeout: 10000 });

    // Check for page title
    await expect(page).toHaveTitle(/System Nebula/);

    // Check that the page doesn't show connection error
    const errorText = await page.textContent("body");
    expect(errorText).not.toContain("Unable to connect");
  });

  test("should load sources in sidebar", async ({ page }) => {
    await page.goto("http://localhost:3000/dashboard");

    // Wait for initial render
    await page.waitForLoadState("networkidle", { timeout: 10000 });

    // Check for loading indicator or content
    const hasLoadingIndicator = await page
      .locator("text=Loading sources")
      .isVisible()
      .catch(() => false);

    if (hasLoadingIndicator) {
      // Wait for loading to finish
      await page.waitForSelector("text=Loading sources", {
        state: "hidden",
        timeout: 10000,
      });
    }

    // Check that feed groups are present
    const feedGroups = await page
      .locator('[role="tree"], .feed-tree, text=/Default Feeds|feeds/i')
      .count();
    expect(feedGroups).toBeGreaterThan(0);
  });

  test("GraphQL server should be accessible", async ({ request }) => {
    const response = await request.post("http://localhost:4002/api/graphql", {
      data: {
        query:
          '{ getUserSources(filters: {userId: "LoscoY4CicovyvejTvAMHPzpkXSqnGHx"}) { id name } }',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.errors).toBeUndefined();
    expect(data.data.getUserSources).toBeDefined();
    expect(data.data.getUserSources.length).toBeGreaterThan(1000);
  });
});
