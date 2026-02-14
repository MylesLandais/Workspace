import { trace } from "@opentelemetry/api";
import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { resourceFromAttributes } from "@opentelemetry/resources";
import {
  SimpleSpanProcessor,
  ConsoleSpanExporter,
  BatchSpanProcessor,
} from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import {
  ATTR_SERVICE_NAME,
  ATTR_SERVICE_VERSION,
} from "@opentelemetry/semantic-conventions";

let isInitialized = false;

export function initBrowserTracing() {
  if (typeof window === "undefined" || isInitialized) {
    return;
  }

  isInitialized = true;

  try {
    const resource = resourceFromAttributes({
      [ATTR_SERVICE_NAME]: "bunny-client",
      [ATTR_SERVICE_VERSION]: "0.1.0",
      environment: "browser",
    });

    // Use console exporter in dev, OTLP exporter in production
    const useConsoleExporter =
      process.env.NODE_ENV === "development" ||
      process.env.OTEL_EXPORT_CONSOLE === "true";

    const otlpEndpoint =
      process.env.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT ||
      "http://localhost:4318/v1/traces";

    const consoleExporter = new ConsoleSpanExporter();
    const otlpExporter = new OTLPTraceExporter({
      url: otlpEndpoint,
    });

    const spanProcessors = useConsoleExporter
      ? [new SimpleSpanProcessor(consoleExporter)]
      : [
          new SimpleSpanProcessor(consoleExporter),
          new BatchSpanProcessor(otlpExporter),
        ];

    const provider = new WebTracerProvider({
      resource,
      spanProcessors,
    });

    provider.register();

    const tracer = trace.getTracer("bunny-client", "0.1.0");

    if (typeof console !== "undefined") {
      console.log("[Browser Tracing] OpenTelemetry initialized", {
        service: "bunny-client",
        exporter: useConsoleExporter ? "console" : "console+otlp",
        otlpEndpoint: useConsoleExporter ? "N/A" : otlpEndpoint,
      });
    }
  } catch (error) {
    console.warn(
      "[Browser Tracing] Failed to initialize (continuing without tracing):",
      error,
    );
    // Don't throw - allow the app to continue without tracing
  }
}
