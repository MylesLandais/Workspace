"""OpenTelemetry metrics initialization for imageboard crawler monitoring."""

import os
import logging
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize meter provider
def setup_meter_provider():
    """Set up OTEL meter provider with Prometheus exporter."""
    try:
        reader = PrometheusMetricReader(prefix="imageboard_")
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        logger.info("OTEL MeterProvider initialized with Prometheus exporter")
        return metrics.get_meter("imageboard_monitor")
    except Exception as e:
        logger.error(f"Failed to initialize OTEL MeterProvider: {e}")
        return None

meter = setup_meter_provider()

if meter is None:
    logger.warning("Metrics collection disabled due to initialization failure")
else:
    # System Metrics (Gauge - Current resource usage)
    orchestrator_cpu_percent = meter.create_gauge(
        "orchestrator_cpu_percent",
        "Orchestrator CPU usage percentage"
    )
    orchestrator_memory_percent = meter.create_gauge(
        "orchestrator_memory_percent",
        "Orchestrator memory usage percentage"
    )
    worker_cpu_percent = meter.create_gauge(
        "worker_cpu_percent",
        "Worker CPU usage percentage"
    )
    worker_memory_percent = meter.create_gauge(
        "worker_memory_percent",
        "Worker memory usage percentage"
    )

    # Orchestrator Metrics
    catalog_polls_total = meter.create_counter(
        "catalog_polls_total",
        "Total catalog polls performed"
    )
    catalog_polls_success = meter.create_counter(
        "catalog_polls_success",
        "Successful catalog polls"
    )
    catalog_polls_failed = meter.create_counter(
        "catalog_polls_failed",
        "Failed catalog polls"
    )
    threads_discovered_total = meter.create_counter(
        "threads_discovered_total",
        "Total threads discovered"
    )
    threads_queued_total = meter.create_counter(
        "threads_queued_total",
        "Total threads queued for monitoring"
    )
    catalog_fetch_duration_seconds = meter.create_histogram(
        "catalog_fetch_duration_seconds",
        "Catalog fetch time in seconds",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    )

    # Worker Metrics
    jobs_processed_total = meter.create_counter(
        "jobs_processed_total",
        "Total jobs processed by worker"
    )
    jobs_success_total = meter.create_counter(
        "jobs_success_total",
        "Successful jobs"
    )
    jobs_failed_total = meter.create_counter(
        "jobs_failed_total",
        "Failed jobs"
    )
    queue_depth = meter.create_gauge(
        "queue_depth",
        "Current number of threads in queue"
    )
    active_monitors = meter.create_gauge(
        "active_monitors",
        "Number of active thread monitors"
    )
    job_processing_duration_seconds = meter.create_histogram(
        "job_processing_duration_seconds",
        "Job processing time in seconds",
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    )

    # Thread-Level Metrics
    thread_posts_collected = meter.create_counter(
        "thread_posts_collected_total",
        "Total posts collected per thread",
        ["board", "thread_id", "subject"]
    )
    thread_images_downloaded = meter.create_counter(
        "thread_images_downloaded_total",
        "Total images downloaded per thread",
        ["board", "thread_id", "subject"]
    )
    thread_duplicates_found = meter.create_counter(
        "thread_duplicates_found_total",
        "Duplicate images found per thread",
        ["board", "thread_id", "subject"]
    )
    thread_moderated_posts = meter.create_counter(
        "thread_moderated_posts_total",
        "Moderated posts per thread",
        ["board", "thread_id", "subject"]
    )
    thread_fetch_duration_seconds = meter.create_histogram(
        "thread_fetch_duration_seconds",
        "Thread fetch time in seconds",
        ["board", "thread_id"],
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
    )
    thread_last_fetch_timestamp = meter.create_gauge(
        "thread_last_fetch_timestamp_seconds",
        "Unix timestamp of last fetch",
        ["board", "thread_id"]
    )

    # Error Metrics
    errors_total = meter.create_counter(
        "errors_total",
        "Total errors by type",
        ["error_type", "component"]
    )
