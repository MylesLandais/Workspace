import { NextRequest, NextResponse } from 'next/server';
import { withSpan } from './tracer';

export async function traceMiddleware(
  request: NextRequest,
  handler: () => Promise<NextResponse>
): Promise<NextResponse> {
  const path = new URL(request.url).pathname;

  return withSpan(
    `HTTP ${request.method} ${path}`,
    async (span) => {
      span.setAttributes({
        'http.method': request.method,
        'http.url': request.url,
        'http.path': path,
        'http.user_agent': request.headers.get('user-agent') || 'unknown',
      });

      const startTime = Date.now();
      const response = await handler();
      const duration = Date.now() - startTime;

      span.setAttributes({
        'http.status_code': response.status,
        'http.duration_ms': duration,
      });

      if (duration > 1000) {
        span.addEvent('slow_request', {
          duration_ms: duration,
          threshold_ms: 1000,
        });
      }

      return response;
    },
    {
      kind: 'server',
    }
  );
}
