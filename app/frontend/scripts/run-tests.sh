#!/bin/bash
# Run Playwright tests in Docker container

set -e

echo "🧪 Running Playwright E2E tests in container..."

# Ensure test directories exist
mkdir -p test-results playwright-report

# Run tests
npm run test:e2e

echo "✅ Tests complete! Check test-results/ for screenshots and playwright-report/ for HTML report"




