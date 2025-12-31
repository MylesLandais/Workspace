# Quick Start: Running Tests in Docker

## One-Time Setup

```bash
cd app/frontend

# 1. Rebuild container (includes test dependencies)
docker-compose build

# 2. Start container
docker-compose up -d

# 3. Install Playwright browsers (one-time)
docker exec frontend-frontend-1 npx playwright install --with-deps chromium
```

## Run Tests (Before Committing)

```bash
# Run all tests
make test-e2e

# OR directly
docker exec frontend-frontend-1 npm run test:e2e

# View results
docker exec frontend-frontend-1 npx playwright show-report
# Or on host machine:
cd app/frontend && npx playwright show-report
```

## What Gets Tested

✅ MSW doesn't hang initialization  
✅ App doesn't get stuck on loading screen  
✅ Mock data loads from `/temp/mock_data/`  
✅ GraphQL queries work  
✅ Feed displays correctly  

## Quick Test (Just Check MSW)

```bash
docker exec frontend-frontend-1 npx playwright test tests/e2e/msw-initialization.spec.ts
```

This runs the fastest test to verify MSW is working.




