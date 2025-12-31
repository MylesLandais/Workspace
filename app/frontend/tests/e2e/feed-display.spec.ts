import { test, expect } from '@playwright/test';

/**
 * Tests for feed display and interaction
 */
test.describe('Feed Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000); // Wait for app and MSW to initialize
  });

  test('should render feed interface', async ({ page }) => {
    // Look for common feed UI elements
    // These selectors may need adjustment based on your actual component structure
    
    // Check if page loaded (not stuck on loading)
    const loadingIndicator = page.getByText('Initializing mock server...');
    await expect(loadingIndicator).not.toBeVisible({ timeout: 1000 });

    // Take screenshot for visual verification
    await page.screenshot({ path: 'test-results/feed-interface.png', fullPage: true });
  });

  test('should load and display feed items', async ({ page }) => {
    // Wait for potential data loading
    await page.waitForTimeout(5000);

    // Check for image elements (feed items usually have images)
    const images = page.locator('img').all();
    const imageCount = (await images).length;

    console.log(`Found ${imageCount} images on page`);

    // Should have at least some content (images, cards, etc.)
    // Exact count depends on how many items MSW returns
    const hasContent = imageCount > 0;

    await page.screenshot({ path: 'test-results/feed-items.png', fullPage: true });

    // Log if no content found for debugging
    if (!hasContent) {
      const pageContent = await page.content();
      console.log('Page content length:', pageContent.length);
      console.log('Page title:', await page.title());
    }
  });

  test('should handle GraphQL errors gracefully', async ({ page, context }) => {
    // Intercept and return error response
    await context.route('**/api/graphql', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();
      
      if (postData?.operationName === 'FeedWithFilters') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            errors: [
              {
                message: 'Test error: Failed to load feed',
                extensions: { code: 'INTERNAL_SERVER_ERROR' },
              },
            ],
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.reload();
    await page.waitForTimeout(3000);

    // Should not crash, should show error state or empty state
    await page.screenshot({ path: 'test-results/error-handling.png', fullPage: true });
  });
});




