"""Celery application factory with signal handlers for task lifecycle management."""

from celery import Celery, signals
from celery.utils.log import get_task_logger
import os
from datetime import datetime, timezone as tz

# Create Celery app
app = Celery("jupyter_scheduler")

# Load configuration
app.config_from_object("src.feed.scheduler.celeryconfig")

# Auto-discover tasks from this package and src.feed package
app.autodiscover_tasks([
    "src.feed.scheduler",  # Scheduler tasks
])

# Get logger
logger = get_task_logger(__name__)


@signals.task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **signal_kwargs):
    """Handle task pre-execution - update database status to running."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()

        # Update task_runs status to 'running' with start time
        pg.execute_write(
            """
            UPDATE task_runs
            SET status = 'running', started_at = %s
            WHERE celery_task_id = %s
            """,
            (datetime.now(tz.utc), task_id)
        )
        logger.info(f"Task {task.name} (ID: {task_id}) started")
    except Exception as e:
        logger.error(f"Error in task_prerun handler: {e}", exc_info=True)


@signals.task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **signal_kwargs):
    """Handle task post-execution - record success and duration."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()

        # Get the task run to calculate duration
        run = pg.execute_read(
            "SELECT started_at FROM task_runs WHERE celery_task_id = %s",
            (task_id,)
        )

        if run:
            started_at = run[0][0]
            duration_ms = int((datetime.now(tz.utc) - started_at).total_seconds() * 1000)

            # Update with success status and duration
            pg.execute_write(
                """
                UPDATE task_runs
                SET status = 'success', completed_at = %s, duration_ms = %s
                WHERE celery_task_id = %s
                """,
                (datetime.now(tz.utc), duration_ms, task_id)
            )
            logger.info(
                f"Task {task.name} (ID: {task_id}) completed successfully in {duration_ms}ms"
            )
    except Exception as e:
        logger.error(f"Error in task_postrun handler: {e}", exc_info=True)


@signals.task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **signal_kwargs):
    """Handle task failure - record error and status."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()

        # Get the task run to calculate duration
        run = pg.execute_read(
            "SELECT started_at FROM task_runs WHERE celery_task_id = %s",
            (task_id,)
        )

        if run:
            started_at = run[0][0]
            duration_ms = int((datetime.now(tz.utc) - started_at).total_seconds() * 1000)

            # Update with failed status, error, and duration
            pg.execute_write(
                """
                UPDATE task_runs
                SET status = 'failed', completed_at = %s, duration_ms = %s,
                    error_message = %s, exit_code = 1
                WHERE celery_task_id = %s
                """,
                (datetime.now(tz.utc), duration_ms, str(exception), task_id)
            )
            logger.error(
                f"Task {task_id} failed after {duration_ms}ms: {exception}",
                exc_info=einfo
            )
    except Exception as e:
        logger.error(f"Error in task_failure handler: {e}", exc_info=True)


@signals.task_retry.connect
def task_retry_handler(task_id, reason, einfo, **signal_kwargs):
    """Handle task retry - update retry count."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()

        # Record retry in task_runs (we'll create a new run record on retry)
        logger.warning(f"Task {task_id} being retried: {reason}")
    except Exception as e:
        logger.error(f"Error in task_retry handler: {e}", exc_info=True)


if __name__ == "__main__":
    app.start()
