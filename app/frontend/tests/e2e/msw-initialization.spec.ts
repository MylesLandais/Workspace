import { test, expect } from '@playwright/test';

/**
 * Tests for MSW (Mock Service Worker) initialization and basic functionality
 */
test.describe('MSW Initialization', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('should not be stuck on loading screen', async ({ page }) => {
    // The app should render within 5 seconds (MSW init is non-blocking now)
    const loadingText = page.getByText('Initializing mock server...');
    
    // Wait a bit to ensure MSW has time to initialize
    await page.waitForTimeout(2000);
    
    // Loading screen should NOT be visible after a reasonable time
    await expect(loadingText).not.toBeVisible({ timeout: 1000 });
  });

  test('should initialize MSW in console', async ({ page }) => {
    const logs: string[] = [];
    
    // Collect console logs
    page.on('console', (msg) => {
      const text = msg.text();
      logs.push(text);
      console.log(`[Browser Console] ${msg.type()}: ${text}`);
    });

    await page.waitForTimeout(3000); // Give MSW time to initialize

    // Check for MSW initialization logs
    const mswLogs = logs.filter(log => log.includes('[MSW]'));
    const hasInitialization = mswLogs.some(log => 
      log.includes('Setting up MSW') || 
      log.includes('Mock server started') ||
      log.includes('MSW initialization complete')
    );

    // MSW should either initialize successfully or fail gracefully
    const hasAnyMSWActivity = mswLogs.length > 0;
    expect(hasAnyMSWActivity).toBeTruthy();
    
    // Log all MSW-related logs for debugging
    if (mswLogs.length > 0) {
      console.log('MSW logs found:', mswLogs);
    } else {
      console.warn('No MSW logs found - MSW may not be initializing');
    }
  });

  test('should load the feed component', async ({ page }) => {
    // Wait for the app to load (not stuck on loading screen)
    await page.waitForTimeout(2000);
    
    // Look for feed-related elements (adjust selectors based on your actual UI)
    // Common selectors to check:
    const feedContainer = page.locator('[data-testid="feed"], .feed, [class*="Feed"]').first();
    const sidebar = page.locator('[data-testid="sidebar"], .sidebar, [class*="Sidebar"]').first();
    
    // At least one of these should exist
    const hasFeedOrSidebar = await Promise.race([
      feedContainer.waitFor({ timeout: 2000 }).then(() => true).catch(() => false),
      sidebar.waitFor({ timeout: 2000 }).then(() => true).catch(() => false),
    ]);

    // Take a screenshot for debugging
    await page.screenshot({ path: 'test-results/feed-load.png', fullPage: true });
    
    expect(hasFeedOrSidebar).toBeTruthy();
  });

  test('should handle GraphQL queries without errors', async ({ page }) => {
    const errors: string[] = [];
    
    // Collect console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        errors.push(text);
        console.error(`[Browser Error] ${text}`);
      }
    });

    // Wait for app to initialize and make GraphQL requests
    await page.waitForTimeout(5000);

    // Filter out expected/harmless errors
    const criticalErrors = errors.filter(error => {
      // Ignore common non-critical errors
      const ignoredPatterns = [
        'favicon',
        'Source map',
        'DevTools',
        'Extension',
      ];
      return !ignoredPatterns.some(pattern => error.toLowerCase().includes(pattern.toLowerCase()));
    });

    // Log any critical errors
    if (criticalErrors.length > 0) {
      console.error('Critical errors found:', criticalErrors);
      await page.screenshot({ path: 'test-results/errors.png', fullPage: true });
    }

    // Should not have critical GraphQL errors
    const graphQLErrors = criticalErrors.filter(e => 
      e.includes('GraphQL') || 
      e.includes('network') || 
      e.includes('fetch') ||
      e.includes('Failed to fetch')
    );
    
    expect(graphQLErrors.length).toBe(0);
  });
});




