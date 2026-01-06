# System Nebula Testing Methodology

This document outlines the comprehensive testing strategy for the Bunny/System Nebula platform, including unit tests, E2E tests, health checks, and monitoring.

## Overview

The testing system consists of multiple layers:
- Unit Tests (Bun test runner)
- E2E Tests (Playwright)
- Health Checks (automated service monitoring)
- Metrics Collection (system statistics)

## Health Check Architecture

### Client Health Endpoint (`/api/health`)

Checks the health of the frontend application and its database connection.

Response:
```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "database": true
  },
  "timestamp": "2025-01-05T12:00:00.000Z",
  "responseTime": 45,
  "uptime": 3600
}
```

Status codes:
- 200: All systems healthy
- 503: One or more services degraded/unhealthy

### Server Health Endpoint (`/health`)

Checks the GraphQL server and its dependencies (Neo4j, Valkey).

Response:
```json
{
  "status": "healthy|degraded",
  "timestamp": "2025-01-05T12:00:00.000Z",
  "uptime": 3600,
  "responseTime": 45,
  "checks": {
    "neo4j": { "status": "healthy|unhealthy", "error": "..." },
    "valkey": { "status": "healthy|unhealthy", "error": "..." }
  }
}
```

### Metrics Endpoint (`/api/metrics`)

Provides system statistics including waitlist and user counts.

Response:
```json
{
  "status": "success|error",
  "timestamp": "2025-01-05T12:00:00.000Z",
  "stats": {
    "waitlistCount": 150,
    "userCount": 25,
    "waitlistByStatus": {
      "pending": 140,
      "invited": 8,
      "joined": 2
    }
  },
  "responseTime": 120
}
```

## Docker Compose Health Checks

### Client Container
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 15s
```

The client waits for database and cache to be healthy before starting.

### Server Container
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:4002/health"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 15s
```

The server waits for Valkey and Qdrant to be healthy before starting.

### Dependency Services
- MySQL: Health check on port 3306
- Redis: Health check on port 6379
- Valkey: Health check on port 6379
- Browserless: Health check on port 3000

## E2E Testing with Playwright

### Setup

E2E tests run in a separate Playwright container (`playwright-tester`) that:
1. Waits for the client application to be fully ready
2. Connects to Browserless Chrome via WebSocket
3. Runs the Playwright test suite automatically
4. Reports results with HTML report output

### Test Configuration (`playwright.config.ts`)

- Browser: Chromium (Desktop Chrome)
- Base URL: `http://client:3000` (within Docker) or `http://127.0.0.1:3000` (local)
- Service URL: Browserless Chrome via WebSocket
- Reporter: HTML report with trace recording

### Available Tests

#### Waitlist Tests (`e2e/waitlist.spec.ts`)

1. **Form Display**: Verifies the waitlist form renders correctly
2. **Successful Submission**: Tests valid email submission and success message
3. **Invalid Email Format**: Tests email validation error handling
4. **Duplicate Email**: Tests rejection of duplicate submissions
5. **Required Field**: Confirms email field is mandatory
6. **Loading State**: Verifies loading state during submission
7. **Form Clearing**: Checks that form clears after successful submission
8. **API Error Handling**: Tests graceful error handling when API fails

#### Other E2E Tests

- **Authentication** (`e2e/auth.spec.ts`): Login, signup, session management
- **Performance** (`e2e/performance.spec.ts`): Load times, performance metrics
- **Smoke Tests** (`e2e/simple.spec.ts`): Basic navigation and rendering

### Running Tests Locally

```bash
# From app/client directory
bun run test:e2e
```

### Running Tests in Docker

```bash
# From project root
docker-compose -f app/client/docker-compose.yml up

# The playwright-tester container will automatically run tests
# View HTML report in app/client/playwright-report/
```

### Test Output

Tests generate:
- **HTML Report**: `app/client/playwright-report/index.html`
- **Traces**: Recorded for failed tests for debugging
- **Videos**: Optional browser recordings

## Waitlist API Testing

### Submit to Waitlist

```bash
curl -X POST http://localhost:3000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "source": "landing"
  }'
```

Response (201 Created):
```json
{
  "message": "Successfully joined the waitlist",
  "id": "uuid-string"
}
```

### Check Waitlist Status

```bash
curl http://localhost:3000/api/waitlist?email=user@example.com
```

Response (200 OK):
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "status": "pending",
  "createdAt": "2025-01-05T12:00:00.000Z"
}
```

## Unit Testing

### Client Unit Tests

```bash
cd app/client
bun run test
```

Tests use Bun's native test runner.

### Server Unit Tests

Currently minimal. To add:

```bash
cd app/server
bun run test
```

## Docker Compose Usage

### Start All Services

```bash
# From project root - Start client stack
docker-compose -f app/client/docker-compose.yml up

# In another terminal - Start server stack
docker-compose -f app/server/docker-compose.yml up
```

### Monitor Services

```bash
# View logs for a specific service
docker-compose -f app/client/docker-compose.yml logs client -f
docker-compose -f app/server/docker-compose.yml logs server -f

# Check service status
docker-compose -f app/client/docker-compose.yml ps
docker-compose -f app/server/docker-compose.yml ps
```

### Tear Down

```bash
docker-compose -f app/client/docker-compose.yml down
docker-compose -f app/server/docker-compose.yml down
```

## Monitoring and Observability

### Health Check Dashboard (Development)

Visit `http://localhost:3000/api/health` and `http://localhost:4002/health` to check service status.

### Metrics

Visit `http://localhost:3000/api/metrics` to view system statistics.

### Container Status

Services report health via Docker health checks:
- `healthy`: All checks passed
- `starting`: Service initializing
- `unhealthy`: Health check failed
- `none`: No health check configured

## Troubleshooting

### Client Container Not Starting

1. Check MySQL is healthy: `docker-compose ps mysql`
2. Check Redis is healthy: `docker-compose ps redis`
3. View client logs: `docker-compose logs client`
4. Verify database schema: `docker-compose exec mysql mysql -u root -pbetterauth bunny_auth -e "SHOW TABLES;"`

### Server Container Not Starting

1. Check Valkey is healthy: `docker-compose ps valkey`
2. Check Qdrant is healthy: `docker-compose ps qdrant`
3. View server logs: `docker-compose logs server`

### E2E Tests Failing

1. Ensure client is fully healthy: `curl http://localhost:3000/api/health`
2. Check Browserless is running: `curl http://localhost:3001/health`
3. View Playwright report: Open `app/client/playwright-report/index.html`
4. Check test traces for debugging

## SMTP Configuration

The email service uses Upyo for SMTP. Configure via environment variables:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
SMTP_FROM_EMAIL=noreply@systemnebula.com
APP_URL=https://systemnebula.com
```

Without configuration, email service logs warnings but doesn't crash.

## Database Migrations

### Add New Migration

```bash
cd app/client

# Generate migration
bun run db:generate

# Push to database
bun run db:push

# View schema in Drizzle Studio
bun run db:studio
```

## Continuous Improvements

### Future Enhancements

1. Add performance benchmarking to E2E tests
2. Implement load testing with k6 or Artillery
3. Add API contract testing
4. Implement integration tests for GraphQL resolvers
5. Add security testing (OWASP top 10)
6. Implement visual regression testing
7. Add accessibility (a11y) testing with Axe

### Metrics to Track

- API response times (p50, p95, p99)
- Error rates and error types
- Database query performance
- Cache hit rates
- E2E test pass/fail rates
- Service availability uptime
