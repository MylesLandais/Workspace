# E2E Tests with Playwright

End-to-end tests for the frontend application, including MSW initialization and mock data loading.

## Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Debug tests
npm run test:e2e:debug

# Run specific test file
npx playwright test tests/e2e/msw-initialization.spec.ts
```

## Test Files

- **`msw-initialization.spec.ts`** - Tests MSW initialization, loading screen behavior, console logs
- **`mock-data-loading.spec.ts`** - Tests mock data loading from `/temp/mock_data/`
- **`feed-display.spec.ts`** - Tests feed display and error handling

## What These Tests Catch

✅ MSW initialization hanging or failing  
✅ App stuck on loading screen  
✅ GraphQL queries failing  
✅ Mock data not loading  
✅ Console errors and exceptions  
✅ Network request issues  

## Test Results

Test results and screenshots are saved to `test-results/` directory.

View HTML report:
```bash
npx playwright show-report
```

## CI/CD

Tests run automatically on push/PR via GitHub Actions. See `.github/workflows/playwright.yml`.




