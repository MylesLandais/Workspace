import { trace, Span, SpanStatusCode, context } from '@opentelemetry/api';

const tracer = trace.getTracer('bunny-client', '0.1.0');

export interface SpanOptions {
  attributes?: Record<string, string | number | boolean>;
  kind?: 'server' | 'client' | 'internal';
}

export async function withSpan<T>(
  name: string,
  fn: (span: Span) => Promise<T>,
  options?: SpanOptions
): Promise<T> {
  return tracer.startActiveSpan(name, async (span) => {
    try {
      if (options?.attributes) {
        span.setAttributes(options.attributes);
      }

      const result = await fn(span);

      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error instanceof Error ? error.message : 'Unknown error',
      });

      if (error instanceof Error) {
        span.recordException(error);
      }

      throw error;
    } finally {
      span.end();
    }
  });
}

export function startSpan(name: string, options?: SpanOptions): Span {
  const span = tracer.startSpan(name);

  if (options?.attributes) {
    span.setAttributes(options.attributes);
  }

  return span;
}

export function endSpan(span: Span, error?: Error) {
  if (error) {
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
    span.recordException(error);
  } else {
    span.setStatus({ code: SpanStatusCode.OK });
  }

  span.end();
}

export function addSpanEvent(span: Span, name: string, attributes?: Record<string, string | number>) {
  span.addEvent(name, attributes);
}

export { tracer, context };
