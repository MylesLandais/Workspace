"""Celery configuration module with RedBeat scheduler setup."""

import os
from kombu import Exchange, Queue

# Broker and result backend
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Task configuration
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
timezone = os.getenv("TASK_SCHEDULER_TIMEZONE", "UTC")
enable_utc = True

# Result backend settings
result_expires = 3600  # 1 hour retention for task results
result_backend_transport_options = {
    "master_name": "mymaster",
    "retry_on_timeout": True,
}

# Task execution settings
task_track_started = True
task_send_sent_event = True
worker_send_task_events = True

# RedBeat scheduler configuration
beat_scheduler = "redbeat.RedBeatScheduler"
redbeat_redis_url = broker_url
redbeat_key_prefix = "redbeat"

# Queues - Define routing for different task types
default_exchange = Exchange("celery", type="direct")
default_queue = Queue("default", exchange=default_exchange, routing_key="default")

task_queues = (
    # Default queue for miscellaneous tasks
    Queue("default", exchange=default_exchange, routing_key="default"),
    # Reddit polling - higher priority
    Queue("reddit", exchange=default_exchange, routing_key="reddit"),
    # Deduplication - lower priority, can be batched
    Queue("dedup", exchange=default_exchange, routing_key="dedup"),
    # Imageboards - high priority for real-time
    Queue("imageboards", exchange=default_exchange, routing_key="imageboards"),
    # Background maintenance tasks
    Queue("maintenance", exchange=default_exchange, routing_key="maintenance"),
)

# Task routing - map task names to specific queues
task_routes = {
    "src.feed.scheduler.tasks.poll_reddit_task": {"queue": "reddit"},
    "src.feed.scheduler.tasks.dedup_task": {"queue": "dedup"},
    "src.feed.scheduler.tasks.poll_imageboard_catalog": {"queue": "imageboards"},
    "src.feed.scheduler.tasks.process_imageboard_thread": {"queue": "imageboards"},
    "src.feed.scheduler.tasks.cleanup_nix_environments": {"queue": "maintenance"},
}

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
worker_disable_rate_limits = False

# Task defaults
task_default_retry_delay = 60  # Retry after 1 minute
task_default_max_retries = 3
task_default_rate_limit = "100/m"  # Rate limit to 100 tasks per minute

# Logging
worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
worker_task_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
)
