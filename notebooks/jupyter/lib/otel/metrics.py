"""OpenTelemetry metrics setup with Prometheus exporter."""

import os
import logging

from opentelemetry import metrics as metrics_api
from opentelemetry.sdk.metrics import MeterProvider

logger = logging.getLogger(__name__)

_initialized = False


def setup_metrics(prefix: str = "jupyter_") -> None:
    """Initialize MeterProvider with Prometheus exporter if available."""
    global _initialized
    if _initialized:
        return

    readers = []
    try:
        from opentelemetry.exporter.prometheus import PrometheusMetricReader

        readers.append(PrometheusMetricReader())
        logger.info("Prometheus metric reader configured")
    except ImportError:
        logger.warning("Prometheus exporter not installed, metrics are local-only")

    provider = MeterProvider(metric_readers=readers)
    metrics_api.set_meter_provider(provider)
    _initialized = True


def get_meter(name: str = "jupyter") -> metrics_api.Meter:
    """Get a named meter instance."""
    return metrics_api.get_meter(name)
