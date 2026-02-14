"""OpenTelemetry instrumentation: tracing, metrics, span helpers."""

from .tracing import get_tracer, setup_tracing
from .metrics import get_meter, setup_metrics
from .spans import traced
