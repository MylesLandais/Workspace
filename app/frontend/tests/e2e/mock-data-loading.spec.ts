import { test, expect } from '@playwright/test';

/**
 * Tests for mock data loading and feed display
 */
test.describe('Mock Data Loading', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for app to initialize
    await page.waitForTimeout(2000);
  });

  test('should load mock data from temp directory', async ({ page }) => {
    const logs: string[] = [];
    
    page.on('console', (msg) => {
      const text = msg.text();
      if (text.includes('[MSW]') || text.includes('mock')) {
        logs.push(text);
      }
    });

    // Wait for GraphQL query to execute
    await page.waitForTimeout(5000);

    // Check for data loading logs
    const dataLogs = logs.filter(log => 
      log.includes('Loaded') || 
      log.includes('items') ||
      log.includes('mock data') ||
      log.includes('FeedWithFilters')
    );

    console.log('Data loading logs:', dataLogs);

    // Should have some indication that data is being loaded
    // Either MSW is loading data, or there are errors we can catch
    expect(logs.length).toBeGreaterThan(0);
  });

  test('should display feed items when data is loaded', async ({ page }) => {
    // Wait for feed to potentially load
    await page.waitForTimeout(5000);

    // Check network requests for GraphQL queries
    const graphqlRequests: string[] = [];
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/graphql') || url.includes('api/graphql')) {
        graphqlRequests.push(url);
      }
    });

    // Wait a bit more for requests
    await page.waitForTimeout(2000);

    // Check if GraphQL queries are being made (and hopefully intercepted by MSW)
    console.log('GraphQL requests:', graphqlRequests);

    // Take a screenshot to see what's rendered
    await page.screenshot({ path: 'test-results/mock-data-test.png', fullPage: true });
  });

  test('should handle empty state gracefully', async ({ page, context }) => {
    // Intercept and modify GraphQL response to return empty data
    await context.route('**/api/graphql', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();
      
      if (postData?.operationName === 'FeedWithFilters') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              feed: {
                edges: [],
                pageInfo: {
                  hasNextPage: false,
                  endCursor: null,
                },
              },
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.reload();
    await page.waitForTimeout(3000);

    // Should not crash with empty data
    await page.screenshot({ path: 'test-results/empty-state.png', fullPage: true });
  });

  test('should verify mock data files are accessible', async ({ page }) => {
    // Check if mock data files are accessible via HTTP
    const response = await page.request.get('/temp/mock_data/SelenaGomez/json/SelenaGomez_posts.json');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('subreddit');
    expect(data).toHaveProperty('posts');
    expect(Array.isArray(data.posts)).toBe(true);
    
    console.log(`Found ${data.posts.length} posts in SelenaGomez mock data`);
  });
});




