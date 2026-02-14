"""Task management service layer for scheduler.

Provides CRUD operations, RRule scheduling, and RedBeat integration
for task lifecycle management.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone as tz
from dateutil import rrule
import json
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """Business logic for scheduled task management."""

    def __init__(self, postgres_connection):
        """Initialize with PostgreSQL connection.

        Args:
            postgres_connection: PostgresConnection instance for database access
        """
        self.pg = postgres_connection

    def create_task(
        self,
        name: str,
        script_path: str,
        schedule_rrule: str,
        nix_packages: List[str],
        description: str = "",
        timezone: str = "UTC",
        break_into_steps: bool = False,
        max_concurrent: int = 1,
        retry_max: int = 3,
        retry_backoff: str = "exponential",
        timeout_seconds: int = 7200,
    ) -> Dict[str, Any]:
        """Create a new scheduled task.

        Validates RRule, calculates next_run_at, and stores task definition.

        Args:
            name: Human-readable task name
            script_path: Path to Python script to execute
            schedule_rrule: RFC 5545 RRule string (e.g., "FREQ=DAILY;BYHOUR=2")
            nix_packages: List of nix packages to include in environment
            description: Optional task description
            timezone: Timezone for schedule (default "UTC")
            break_into_steps: Whether to break into sub-tasks (default False)
            max_concurrent: Maximum concurrent executions (default 1)
            retry_max: Maximum retry attempts (default 3)
            retry_backoff: Retry strategy ("exponential", "linear", "fixed") (default "exponential")
            timeout_seconds: Task timeout in seconds (default 7200 = 2 hours)

        Returns:
            Dict with created task:
            {
                "id": str,
                "name": str,
                "script_path": str,
                "schedule_rrule": str,
                "nix_packages": list,
                "next_run_at": datetime,
                "enabled": bool,
                "created_at": datetime,
            }

        Raises:
            ValueError: If RRule is invalid
            RuntimeError: If database operation fails
        """
        # Validate RRule
        try:
            rrule_obj = rrule.rrulestr(schedule_rrule, dtstart=datetime.now(tz.utc))
        except Exception as e:
            raise ValueError(f"Invalid RRule '{schedule_rrule}': {e}")

        # Calculate next run time
        next_run_at = rrule_obj._dtstart
        if next_run_at <= datetime.now(tz.utc):
            # Get next occurrence
            next_run_at = rrule_obj.after(datetime.now(tz.utc))

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Insert into database
        try:
            self.pg.execute_write(
                """
                INSERT INTO scheduled_tasks (
                    id, name, description, task_type, script_path, nix_packages,
                    schedule_rrule, timezone, enabled, break_into_steps,
                    max_concurrent, retry_max, retry_backoff, timeout_seconds,
                    next_run_at, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    task_id,
                    name,
                    description,
                    "python_script",  # task_type
                    script_path,
                    json.dumps(nix_packages),
                    schedule_rrule,
                    timezone,
                    True,  # enabled
                    break_into_steps,
                    max_concurrent,
                    retry_max,
                    retry_backoff,
                    timeout_seconds,
                    next_run_at,
                    datetime.now(tz.utc),
                    datetime.now(tz.utc),
                )
            )

            logger.info(f"Created task {task_id}: {name} (next run: {next_run_at})")

            return {
                "id": task_id,
                "name": name,
                "script_path": script_path,
                "schedule_rrule": schedule_rrule,
                "nix_packages": nix_packages,
                "next_run_at": next_run_at,
                "enabled": True,
                "created_at": datetime.now(tz.utc),
            }

        except Exception as e:
            logger.error(f"Failed to create task {name}: {e}")
            raise RuntimeError(f"Database error creating task: {e}")

    def list_tasks(
        self,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List scheduled tasks.

        Args:
            enabled_only: If True, only return enabled tasks (default False)
            limit: Maximum results (default 100)
            offset: Pagination offset (default 0)

        Returns:
            List of task dicts with all fields
        """
        query = "SELECT * FROM scheduled_tasks"
        params = []

        if enabled_only:
            query += " WHERE enabled = true"

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        try:
            results = self.pg.execute_read(query, params)
            tasks = []
            for row in results:
                tasks.append(self._row_to_task_dict(row))
            logger.debug(f"Retrieved {len(tasks)} tasks")
            return tasks
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID.

        Args:
            task_id: UUID of task

        Returns:
            Task dict or None if not found
        """
        try:
            result = self.pg.execute_read(
                "SELECT * FROM scheduled_tasks WHERE id = %s",
                (task_id,)
            )
            if result:
                return self._row_to_task_dict(result[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    def update_task(self, task_id: str, **fields) -> Optional[Dict[str, Any]]:
        """Update task fields.

        Args:
            task_id: UUID of task
            **fields: Field names and values to update

        Returns:
            Updated task dict or None if not found
        """
        allowed_fields = {
            "name", "description", "schedule_rrule", "timezone",
            "enabled", "max_concurrent", "retry_max", "retry_backoff",
            "timeout_seconds",
        }
        fields = {k: v for k, v in fields.items() if k in allowed_fields}

        if not fields:
            logger.warning(f"No valid fields to update for task {task_id}")
            return self.get_task(task_id)

        # Handle RRule recalculation if schedule changed
        if "schedule_rrule" in fields:
            try:
                rrule_obj = rrule.rrulestr(
                    fields["schedule_rrule"],
                    dtstart=datetime.now(tz.utc)
                )
                next_run = rrule_obj.after(datetime.now(tz.utc))
                fields["next_run_at"] = next_run
            except Exception as e:
                logger.error(f"Invalid RRule in update: {e}")
                return None

        fields["updated_at"] = datetime.now(tz.utc)

        # Build update query
        set_clause = ", ".join(f"{k} = %s" for k in fields.keys())
        params = list(fields.values()) + [task_id]

        try:
            self.pg.execute_write(
                f"UPDATE scheduled_tasks SET {set_clause} WHERE id = %s",
                params
            )
            logger.info(f"Updated task {task_id}")
            return self.get_task(task_id)
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return None

    def enable_task(self, task_id: str) -> bool:
        """Enable a task.

        Args:
            task_id: UUID of task

        Returns:
            True if successful, False otherwise
        """
        try:
            self.pg.execute_write(
                """
                UPDATE scheduled_tasks
                SET enabled = true, updated_at = %s
                WHERE id = %s
                """,
                (datetime.now(tz.utc), task_id)
            )
            logger.info(f"Enabled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable task {task_id}: {e}")
            return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a task.

        Args:
            task_id: UUID of task

        Returns:
            True if successful, False otherwise
        """
        try:
            self.pg.execute_write(
                """
                UPDATE scheduled_tasks
                SET enabled = false, updated_at = %s
                WHERE id = %s
                """,
                (datetime.now(tz.utc), task_id)
            )
            logger.info(f"Disabled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to disable task {task_id}: {e}")
            return False

    def trigger_task_now(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Trigger a task to run immediately.

        Creates a task_run record and enqueues execution via Celery.

        Args:
            task_id: UUID of task

        Returns:
            Dict with task_run info or None if failed
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return None

        run_id = str(uuid.uuid4())

        try:
            # Create task_run record
            self.pg.execute_write(
                """
                INSERT INTO task_runs (
                    id, task_id, status, started_at
                ) VALUES (
                    %s, %s, %s, %s
                )
                """,
                (run_id, task_id, "queued", datetime.now(tz.utc))
            )

            # Enqueue task via Celery
            from src.feed.scheduler.celery_app import app

            # Map task_type to Celery task name
            task_map = {
                "reddit_poll": "src.feed.scheduler.tasks.poll_reddit_task",
                "deduplication": "src.feed.scheduler.tasks.dedup_task",
                "imageboard_poll": "src.feed.scheduler.tasks.poll_imageboard_catalog",
            }

            # Determine task type from script_path or metadata
            task_type = task.get("task_type", "python_script")
            celery_task_name = task_map.get(task_type, "src.feed.scheduler.tasks.execute_generic_task")

            # Enqueue
            celery_result = app.send_task(
                celery_task_name,
                kwargs={
                    "task_id": task_id,
                    "run_id": run_id,
                }
            )

            logger.info(f"Triggered task {task_id} (run: {run_id}, celery: {celery_result.id})")

            return {
                "id": run_id,
                "task_id": task_id,
                "status": "queued",
                "started_at": datetime.now(tz.utc),
            }

        except Exception as e:
            logger.error(f"Failed to trigger task {task_id}: {e}", exc_info=True)
            return None

    def list_runs(
        self,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List task runs with optional filtering.

        Args:
            task_id: Filter by specific task (optional)
            status: Filter by status (optional: pending, running, success, failed)
            limit: Maximum results (default 20)
            offset: Pagination offset (default 0)

        Returns:
            List of task_run dicts
        """
        query = "SELECT * FROM task_runs WHERE 1=1"
        params = []

        if task_id:
            query += " AND task_id = %s"
            params.append(task_id)

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY started_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        try:
            results = self.pg.execute_read(query, params)
            runs = []
            for row in results:
                runs.append(self._row_to_run_dict(row))
            return runs
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []

    def get_task_stats(self) -> Dict[str, Any]:
        """Get overall task statistics.

        Returns:
            Dict with stats:
            {
                "total_tasks": int,
                "enabled_tasks": int,
                "total_runs": int,
                "successful_runs": int,
                "failed_runs": int,
                "average_duration_ms": float,
            }
        """
        try:
            stats = self.pg.execute_read(
                """
                SELECT
                    (SELECT COUNT(*) FROM scheduled_tasks) as total_tasks,
                    (SELECT COUNT(*) FROM scheduled_tasks WHERE enabled = true) as enabled_tasks,
                    (SELECT COUNT(*) FROM task_runs) as total_runs,
                    (SELECT COUNT(*) FROM task_runs WHERE status = 'success') as successful_runs,
                    (SELECT COUNT(*) FROM task_runs WHERE status = 'failed') as failed_runs,
                    (SELECT AVG(duration_ms) FROM task_runs WHERE status = 'success') as avg_duration
                """
            )

            if stats:
                row = stats[0]
                return {
                    "total_tasks": row[0],
                    "enabled_tasks": row[1],
                    "total_runs": row[2],
                    "successful_runs": row[3],
                    "failed_runs": row[4],
                    "average_duration_ms": row[5] or 0,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get task stats: {e}")
            return {}

    @staticmethod
    def _row_to_task_dict(row) -> Dict[str, Any]:
        """Convert database row to task dict."""
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "task_type": row[3],
            "script_path": row[4],
            "nix_packages": json.loads(row[5]) if isinstance(row[5], str) else row[5],
            "schedule_rrule": row[6],
            "timezone": row[7],
            "enabled": row[8],
            "break_into_steps": row[9],
            "max_concurrent": row[10],
            "retry_max": row[11],
            "retry_backoff": row[12],
            "timeout_seconds": row[13],
            "next_run_at": row[14],
            "last_run_at": row[15],
            "created_at": row[16],
            "updated_at": row[17],
        }

    @staticmethod
    def _row_to_run_dict(row) -> Dict[str, Any]:
        """Convert database row to task_run dict."""
        return {
            "id": row[0],
            "task_id": row[1],
            "status": row[2],
            "started_at": row[3],
            "completed_at": row[4],
            "duration_ms": row[5],
            "exit_code": row[6],
            "stdout_log": row[7],
            "stderr_log": row[8],
            "error_message": row[9],
            "celery_task_id": row[10],
            "nix_env_hash": row[11],
        }
