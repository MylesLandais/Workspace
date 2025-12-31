# Testing Guide

## E2E Tests with Playwright

Playwright tests catch common issues with MSW initialization, mock data loading, and feed display.

### Quick Start

```bash
# Install dependencies (if not already done)
npm install

# Install Playwright browsers
npx playwright install

# Run all E2E tests
npm run test:e2e

# Run in UI mode (interactive)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed
```

### Test Coverage

#### MSW Initialization Tests (`msw-initialization.spec.ts`)
- ✅ App doesn't get stuck on loading screen
- ✅ MSW initializes correctly (console logs)
- ✅ Feed component loads
- ✅ No critical GraphQL errors

#### Mock Data Loading Tests (`mock-data-loading.spec.ts`)
- ✅ Mock data files accessible via HTTP
- ✅ Data loading logs appear
- ✅ Empty state handled gracefully
- ✅ Feed items display when data loads

#### Feed Display Tests (`feed-display.spec.ts`)
- ✅ Feed interface renders
- ✅ Feed items display correctly
- ✅ Error states handled gracefully

### Running Tests in Docker

If you need to run tests against the containerized app:

```bash
# Start the container first
docker-compose up -d

# Run tests (they'll use the running container)
npm run test:e2e
```

### Debugging Failed Tests

1. **View test report:**
   ```bash
   npx playwright show-report
   ```

2. **Check screenshots:**
   Screenshots are saved to `test-results/` directory

3. **Run in debug mode:**
   ```bash
   npm run test:e2e:debug
   ```

4. **Run single test:**
   ```bash
   npx playwright test tests/e2e/msw-initialization.spec.ts
   ```

### Common Issues

**Tests fail because MSW isn't initializing:**
- Check browser console logs in test output
- Verify `PUBLIC_GRAPHQL_MOCK=true` in environment
- Check that `mockServiceWorker.js` exists in `public/`

**Tests timeout:**
- Increase timeout in `playwright.config.ts`
- Check if dev server is running on port 4321

**Mock data not loading:**
- Verify `/temp/mock_data/` is accessible
- Check network requests in test output
- Ensure mock data JSON files are valid

### CI/CD Integration

Tests run automatically on push/PR via GitHub Actions (`.github/workflows/playwright.yml`).

To run tests locally in CI mode:
```bash
CI=true npm run test:e2e
```
