.PHONY: test test-e2e test-all docker-test install-test-deps

# Run E2E tests in Docker container
docker-test:
	@echo "🧪 Running E2E tests in Docker container..."
	docker exec frontend-frontend-1 npm run test:e2e

# Install test dependencies in container
install-test-deps:
	@echo "📦 Installing Playwright browsers in container..."
	docker exec frontend-frontend-1 npx playwright install --with-deps chromium

# Run all tests
test-all: test-e2e

# Run E2E tests
test-e2e: docker-test

# Quick test (just MSW initialization)
test-quick:
	docker exec frontend-frontend-1 npx playwright test tests/e2e/msw-initialization.spec.ts




