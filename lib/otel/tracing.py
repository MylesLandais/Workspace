"""OpenTelemetry tracing setup with OTLP exporter."""

import os
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_initialized = False


def setup_tracing(service_name: str = None) -> None:
    """Initialize TracerProvider with OTLP exporter if endpoint is configured."""
    global _initialized
    if _initialized:
        return

    svc = service_name or os.getenv("OTEL_SERVICE_NAME", "jupyter")
    resource = Resource.create({"service.name": svc})
    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = OTLPSpanExporter(endpoint=endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP trace exporter configured: %s", endpoint)
        except ImportError:
            logger.warning("OTLP exporter not installed, tracing is local-only")

    trace.set_tracer_provider(provider)
    _initialized = True


def get_tracer(name: str = "jupyter") -> trace.Tracer:
    """Get a named tracer instance."""
    return trace.get_tracer(name)
