# Resilience Testing and Tracing Guide

## Overview

This guide covers the comprehensive resilience testing and tracing infrastructure we've set up to handle edge cases and create a resilient application.

## Components

### 1. Circuit Breaker Pattern

**Location:** `src/lib/resilience/circuit-breaker.ts`

Prevents cascading failures by stopping requests to failing services.

**Usage:**

```typescript
import { createCircuitBreaker } from "@/lib/resilience/circuit-breaker";

const breaker = createCircuitBreaker("my-service", {
  failureThreshold: 5, // Open after 5 failures
  resetTimeout: 60000, // Wait 1 minute before retry
  timeout: 30000, // 30 second request timeout
});

// Use with fallback
const result = await breaker.execute(
  async () => await myService.call(),
  async () => ({ data: "fallback response" }), // Fallback
);
```

**States:**

- `CLOSED`: Normal operation
- `OPEN`: Circuit is open, failing fast
- `HALF_OPEN`: Testing if service recovered

### 2. Retry Logic with Exponential Backoff

**Location:** `src/lib/resilience/retry.ts`

Automatically retries failed operations with exponential backoff.

**Usage:**

```typescript
import { retry, retryWithJitter } from "@/lib/resilience/retry";

// Basic retry
const result = await retry(async () => await apiCall(), {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  isRetryable: (error) => {
    // Only retry on network errors
    return error.message.includes("network");
  },
});

// Retry with jitter (prevents thundering herd)
const result = await retryWithJitter(async () => await apiCall(), {
  maxAttempts: 3,
  initialDelay: 1000,
});
```

### 3. Error Boundaries

**Location:** `src/lib/resilience/error-boundary.tsx`

Catches React component errors and provides graceful error handling.

**Usage:**

```typescript
import { ErrorBoundary } from "@/lib/resilience/error-boundary";

function App() {
  return (
    <ErrorBoundary
      fallback={<CustomErrorUI />}
      onError={(error, errorInfo) => {
        // Custom error handling
      }}
      resetKeys={[userId]} // Reset when userId changes
    >
      <YourApp />
    </ErrorBoundary>
  );
}
```

### 4. Resilience Monitoring

**Location:** `src/lib/resilience/monitoring.ts`

Tracks metrics and health for resilience patterns.

**Usage:**

```typescript
import { resilienceMonitor } from "@/lib/resilience/monitoring";

// Register circuit breakers
resilienceMonitor.registerCircuitBreaker("my-service", breaker);

// Record retry attempts
resilienceMonitor.recordRetry(true); // success
resilienceMonitor.recordRetry(false); // failure

// Record errors
resilienceMonitor.recordError(new Error("Something failed"));

// Get metrics
const metrics = resilienceMonitor.getMetrics();

// Report to Sentry (automatic every 5 minutes)
await resilienceMonitor.reportMetrics();
```

## Testing Infrastructure

### Edge Case Tests

**Location:** `e2e/auth-edge-cases.spec.ts`

Comprehensive edge case tests covering:

- **Input Validation:**
  - Empty inputs
  - Invalid email formats
  - Extremely long inputs
  - Special characters
  - SQL injection attempts
  - XSS attempts

- **Network Failures:**
  - Timeouts
  - 500 errors
  - 429 rate limiting
  - Malformed responses
  - Offline scenarios

- **Concurrent Requests:**
  - Rapid multiple submissions
  - Duplicate prevention

- **Session Management:**
  - Expired sessions
  - Invalid tokens

- **Error Recovery:**
  - Retry after error
  - State clearing

**Run tests:**

```bash
cd app/client && bun run test:e2e e2e/auth-edge-cases.spec.ts
```

### Integration Tests

**Location:** `tests/integration/resilience.test.ts`

Tests for resilience patterns:

- Circuit breaker state transitions
- Retry logic with exponential backoff
- Error recovery scenarios
- Timeout handling
- Fallback mechanisms

**Run tests:**

```bash
cd app/client && bun test tests/integration/resilience.test.ts
```

### Performance Tests

**Location:** `tests/performance/load.test.ts`

Tests for:

- Rapid sequential requests
- Concurrent request handling
- Memory efficiency
- Burst traffic
- Sustained load

**Run tests:**

```bash
cd app/client && bun test tests/performance/load.test.ts
```

### Test Utilities

**Location:** `tests/utils/test-helpers.ts`

Common utilities for testing:

```typescript
import {
  generateTestEmail,
  generateTestPassword,
  simulateSlowNetwork,
  simulateOffline,
  mockApiResponse,
  waitForErrorMessage,
  measurePerformance,
  retryAction,
} from "@/tests/utils/test-helpers";
```

## Enhanced Tracing

### OpenTelemetry Integration

Tracing is automatically integrated via:

- `src/lib/tracing/tracer.ts` - Core tracing utilities
- `src/lib/tracing/instrumentation.node.ts` - Node.js instrumentation
- `src/lib/tracing/instrumentation.browser.ts` - Browser instrumentation

**Usage:**

```typescript
import { withSpan, addSpanEvent } from "@/lib/tracing/tracer";

await withSpan("my.operation", async (span) => {
  span.setAttributes({
    "user.id": userId,
    "operation.type": "create",
  });

  addSpanEvent(span, "operation.start");

  // Your code here

  addSpanEvent(span, "operation.complete");
});
```

### Sentry Integration

Sentry automatically captures:

- Errors with full context
- Performance metrics
- User context
- Breadcrumbs

**Resilience metrics are automatically reported every 5 minutes.**

## Resilient Auth Client

**Location:** `src/lib/auth-client-resilient.ts`

Pre-configured resilient auth client with:

- Circuit breakers for sign in/up
- Automatic retry on network errors
- Fallback responses
- Error monitoring

**Usage:**

```typescript
import { resilientSignIn, resilientSignUp } from "@/lib/auth-client-resilient";

// Automatically handles retries and circuit breaking
const result = await resilientSignIn({
  email: "user@example.com",
  password: "password",
  callbackURL: "/dashboard",
});
```

## Best Practices

### 1. Always Use Circuit Breakers for External Services

```typescript
const apiBreaker = createCircuitBreaker("external-api", {
  failureThreshold: 5,
  resetTimeout: 60000,
});

const result = await apiBreaker.execute(
  async () => await externalApi.call(),
  async () => ({ data: "fallback" }),
);
```

### 2. Retry Transient Errors

```typescript
const result = await retry(async () => await apiCall(), {
  maxAttempts: 3,
  initialDelay: 1000,
  isRetryable: (error) => {
    // Only retry network/5xx errors
    return error.status >= 500 || error.message.includes("network");
  },
});
```

### 3. Wrap Components with Error Boundaries

```typescript
import { ErrorBoundary } from "@/lib/resilience/error-boundary";

<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

### 4. Monitor Resilience Metrics

```typescript
import { resilienceMonitor } from "@/lib/resilience/monitoring";

// Register services
resilienceMonitor.registerCircuitBreaker("my-service", breaker);

// Metrics are automatically reported to Sentry
```

### 5. Test Edge Cases

Always test:

- Invalid inputs
- Network failures
- Timeouts
- Concurrent requests
- Error recovery

## Running All Tests

```bash
# Unit tests
cd app/client && bun test

# Integration tests
cd app/client && bun test tests/integration/

# E2E tests
cd app/client && bun run test:e2e

# Performance tests
cd app/client && bun test tests/performance/
```

## Monitoring in Production

1. **Sentry Dashboard:**
   - View errors with full context
   - See resilience metrics
   - Track performance

2. **OpenTelemetry:**
   - View traces in your OTEL collector
   - Analyze performance bottlenecks
   - Track service dependencies

3. **Console Logs:**
   - Circuit breaker state changes
   - Retry attempts
   - Error details

## Troubleshooting

### Circuit Breaker Stuck Open

1. Check failure threshold
2. Verify reset timeout
3. Check service health
4. Manually reset if needed: `breaker.reset()`

### Too Many Retries

1. Adjust `maxAttempts`
2. Improve `isRetryable` logic
3. Check network conditions
4. Verify service availability

### Errors Not Being Caught

1. Ensure ErrorBoundary wraps components
2. Check Sentry initialization
3. Verify error logging setup
4. Check browser console for errors

## Next Steps

1. **Add More Circuit Breakers:**
   - Database operations
   - External APIs
   - File uploads

2. **Enhance Monitoring:**
   - Custom dashboards
   - Alerting rules
   - Performance budgets

3. **Expand Test Coverage:**
   - More edge cases
   - Chaos engineering
   - Load testing

4. **Improve Error Messages:**
   - User-friendly messages
   - Recovery suggestions
   - Support contact info
