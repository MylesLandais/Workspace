import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { SimpleSpanProcessor, ConsoleSpanExporter, BatchSpanProcessor } from '@opentelemetry/sdk-trace-node';

const resource = resourceFromAttributes({
  [ATTR_SERVICE_NAME]: 'bunny-client',
  [ATTR_SERVICE_VERSION]: '0.1.0',
  environment: process.env.NODE_ENV || 'development',
});

const useConsoleExporter = process.env.OTEL_EXPORT_CONSOLE === 'true';
const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces';

const traceExporter = useConsoleExporter
  ? new ConsoleSpanExporter()
  : new OTLPTraceExporter({
      url: otlpEndpoint,
    });

const sdk = new NodeSDK({
  resource: resource,
  spanProcessors: [
    useConsoleExporter
      ? new SimpleSpanProcessor(traceExporter)
      : new BatchSpanProcessor(traceExporter),
  ],
  instrumentations: [
    new HttpInstrumentation({
      ignoreIncomingPaths: [
        '/_next',
        '/static',
        '/favicon.ico',
        '/api/health',
      ],
    }),
  ],
});

sdk.start();

console.log('[Tracing] OpenTelemetry instrumentation started', {
  service: 'bunny-client',
  exporter: useConsoleExporter ? 'console' : 'otlp',
  endpoint: useConsoleExporter ? 'N/A' : otlpEndpoint,
});

process.on('SIGTERM', () => {
  sdk
    .shutdown()
    .then(() => console.log('[Tracing] SDK shut down successfully'))
    .catch((error) => console.error('[Tracing] Error shutting down SDK', error))
    .finally(() => process.exit(0));
});
