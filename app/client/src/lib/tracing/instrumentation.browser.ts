import { trace } from "@opentelemetry/api";
import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { resourceFromAttributes } from "@opentelemetry/resources";
import {
  SimpleSpanProcessor,
  ConsoleSpanExporter,
} from "@opentelemetry/sdk-trace-base";
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

    const provider = new WebTracerProvider({
      resource,
      spanProcessors: [new SimpleSpanProcessor(new ConsoleSpanExporter())],
    });

    provider.register();

    const tracer = trace.getTracer("bunny-client", "0.1.0");

    if (typeof console !== "undefined") {
      console.log("[Browser Tracing] OpenTelemetry initialized", {
        service: "bunny-client",
        exporter: "console",
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
