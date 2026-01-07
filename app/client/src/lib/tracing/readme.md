# OpenTelemetry Tracing

Performance monitoring and distributed tracing for System Nebula.

## Features

- HTTP request tracing
- Custom span creation for performance tracking
- Slow request detection (>1s)
- Console or OTLP export

## Configuration

### Console Export (Development)

```bash
export OTEL_EXPORT_CONSOLE=true
docker compose restart client
```

### OTLP Export (Production)

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
docker compose restart client
```

## Usage

### Tracing API Routes

```typescript
import { withSpan } from '@/lib/tracing/tracer';

export async function GET(request: NextRequest) {
  return withSpan('api.user.profile', async (span) => {
    span.setAttributes({
      'user.id': session.user.id,
    });

    const profile = await fetchProfile();

    span.addEvent('profile_fetched', {
      'profile.fields': Object.keys(profile).length,
    });

    return NextResponse.json(profile);
  });
}
```

### Tracing Database Queries

```typescript
import { withSpan } from '@/lib/tracing/tracer';

const users = await withSpan('db.query.users', async (span) => {
  span.setAttributes({
    'db.system': 'mysql',
    'db.operation': 'select',
  });

  return db.select().from(user).limit(10);
});
```

### Manual Span Control

```typescript
import { startSpan, endSpan } from '@/lib/tracing/tracer';

const span = startSpan('custom.operation', {
  attributes: { 'operation.type': 'batch' }
});

try {
  await doWork();
  endSpan(span);
} catch (error) {
  endSpan(span, error);
}
```

## Viewing Traces

### Console Output

When `OTEL_EXPORT_CONSOLE=true`, traces print to docker logs:

```bash
docker compose logs client -f | grep Tracing
```

### Jaeger (Optional)

Run Jaeger locally:

```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

View UI at http://localhost:16686

## Performance Monitoring

Slow requests (>1000ms) automatically trigger events in spans. Filter for `slow_request` events to find bottlenecks.
