# Running Tests in Docker Container

Tests can be run directly in the Docker container, which ensures consistency with the development environment.

## Quick Start

```bash
# 1. Rebuild container with test dependencies (if Dockerfile changed)
cd app/frontend
docker-compose build

# 2. Make sure container is running
docker-compose up -d

# 3. Install Playwright browsers (first time only, after container is running)
docker exec frontend-frontend-1 npx playwright install --with-deps chromium

# 4. Run all E2E tests
make test-e2e
# OR
docker exec frontend-frontend-1 npm run test:e2e

# 5. View results
docker exec frontend-frontend-1 npx playwright show-report
# OR view on host machine (volumes are mounted)
cd app/frontend && npx playwright show-report

# Run specific test file
docker exec frontend-frontend-1 npx playwright test tests/e2e/msw-initialization.spec.ts
```

## Viewing Test Results

Test results are saved to `test-results/` and `playwright-report/` directories, which are mounted as volumes, so you can view them on your host machine:

```bash
# View HTML report (on host machine)
cd app/frontend
npx playwright show-report

# Or just open the HTML file
open playwright-report/index.html
```

## Running Tests Before Commit

Add to your git pre-commit hook or just run manually:

```bash
make test-e2e
```

If tests fail, check:
1. `test-results/` for screenshots
2. Console output for error messages
3. `playwright-report/` for detailed HTML report

## Test Commands

```bash
# Run all tests
make test-e2e

# Run quick test (just MSW init)
make test-quick

# Run specific test file
docker exec frontend-frontend-1 npx playwright test tests/e2e/mock-data-loading.spec.ts

# Run in UI mode (requires X11 forwarding or VNC - not recommended in Docker)
# Better to run locally: npm run test:e2e:ui
```

## Troubleshooting

**Tests fail with "browser not found":**
```bash
make install-test-deps
```

**Tests timeout:**
- Check that dev server is running on port 4321
- Increase timeout in `playwright.config.ts`

**Can't see test results:**
- Ensure volumes are mounted in docker-compose.yml
- Check `test-results/` and `playwright-report/` directories exist

