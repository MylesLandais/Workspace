"""Command-line interface for task scheduler management.

Simple Typer-based CLI for creating, managing, and monitoring scheduled tasks.
"""

import typer
from typing import Optional, List
from datetime import datetime, timezone as tz
from tabulate import tabulate
import json

app = typer.Typer()


# ============================================================================
# Task Management Commands
# ============================================================================

@app.command()
def create(
    name: str = typer.Argument(..., help="Task name"),
    script_path: str = typer.Argument(..., help="Path to Python script"),
    schedule_rrule: str = typer.Argument(..., help='RRule schedule (e.g., "FREQ=DAILY;BYHOUR=2")'),
    nix_packages: str = typer.Option(
        "python3",
        "--packages",
        "-p",
        help="Comma-separated nix packages (e.g., 'python3,python3Packages.praw')"
    ),
    description: str = typer.Option("", "--description", "-d", help="Task description"),
    timezone: str = typer.Option("UTC", "--timezone", "-z", help="Timezone for schedule"),
    break_into_steps: bool = typer.Option(
        False,
        "--steps",
        help="Break into sub-tasks"
    ),
    max_concurrent: int = typer.Option(1, "--concurrent", "-c", help="Max concurrent runs"),
    retry_max: int = typer.Option(3, "--retries", "-r", help="Max retry attempts"),
    timeout_seconds: int = typer.Option(
        7200,
        "--timeout",
        "-t",
        help="Task timeout in seconds"
    ),
):
    """Create a new scheduled task."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        packages = [p.strip() for p in nix_packages.split(",")]

        task = service.create_task(
            name=name,
            description=description,
            script_path=script_path,
            nix_packages=packages,
            schedule_rrule=schedule_rrule,
            timezone=timezone,
            break_into_steps=break_into_steps,
            max_concurrent=max_concurrent,
            retry_max=retry_max,
            timeout_seconds=timeout_seconds,
        )

        typer.echo(typer.style("✓ Task created:", fg=typer.colors.GREEN, bold=True))
        typer.echo(f"  ID: {task['id']}")
        typer.echo(f"  Name: {task['name']}")
        typer.echo(f"  Next run: {task['next_run_at']}")
        typer.echo(f"  Packages: {', '.join(task['nix_packages'])}")

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def list(
    enabled_only: bool = typer.Option(
        False,
        "--enabled",
        "-e",
        help="Show only enabled tasks"
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    offset: int = typer.Option(0, "--offset", "-o", help="Pagination offset"),
):
    """List all scheduled tasks."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        tasks = service.list_tasks(enabled_only=enabled_only, limit=limit, offset=offset)

        if not tasks:
            typer.echo("No tasks found")
            return

        # Format for table display
        rows = []
        for task in tasks:
            status = "enabled" if task["enabled"] else "disabled"
            next_run = task["next_run_at"].strftime("%Y-%m-%d %H:%M:%S") if task["next_run_at"] else "N/A"
            rows.append([
                task["id"][:8],
                task["name"],
                status,
                next_run,
                task["script_path"],
            ])

        headers = ["ID", "Name", "Status", "Next Run", "Script"]
        typer.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def show(
    task_id: str = typer.Argument(..., help="Task ID or ID prefix")
):
    """Show task details."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        task = service.get_task(task_id)
        if not task:
            typer.echo(typer.style(f"✗ Task not found: {task_id}", fg=typer.colors.RED), err=True)
            raise typer.Exit(1)

        typer.echo(typer.style(f"Task: {task['name']}", bold=True))
        typer.echo(f"  ID: {task['id']}")
        typer.echo(f"  Status: {'enabled' if task['enabled'] else 'disabled'}")
        typer.echo(f"  Script: {task['script_path']}")
        typer.echo(f"  Schedule: {task['schedule_rrule']}")
        typer.echo(f"  Timezone: {task['timezone']}")
        typer.echo(f"  Next run: {task['next_run_at']}")
        typer.echo(f"  Last run: {task['last_run_at'] or 'Never'}")
        typer.echo(f"  Packages: {', '.join(task['nix_packages'])}")
        typer.echo(f"  Max concurrent: {task['max_concurrent']}")
        typer.echo(f"  Retries: {task['retry_max']} ({task['retry_backoff']})")
        typer.echo(f"  Timeout: {task['timeout_seconds']}s")
        if task['description']:
            typer.echo(f"  Description: {task['description']}")

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def enable(
    task_id: str = typer.Argument(..., help="Task ID")
):
    """Enable a task."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        if service.enable_task(task_id):
            typer.echo(typer.style(f"✓ Enabled task {task_id[:8]}", fg=typer.colors.GREEN))
        else:
            typer.echo(typer.style(f"✗ Failed to enable task", fg=typer.colors.RED), err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def disable(
    task_id: str = typer.Argument(..., help="Task ID")
):
    """Disable a task."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        if service.disable_task(task_id):
            typer.echo(typer.style(f"✓ Disabled task {task_id[:8]}", fg=typer.colors.GREEN))
        else:
            typer.echo(typer.style(f"✗ Failed to disable task", fg=typer.colors.RED), err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def trigger(
    task_id: str = typer.Argument(..., help="Task ID")
):
    """Trigger a task to run immediately."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        run = service.trigger_task_now(task_id)
        if run:
            typer.echo(typer.style(f"✓ Task triggered:", fg=typer.colors.GREEN, bold=True))
            typer.echo(f"  Run ID: {run['id']}")
            typer.echo(f"  Status: {run['status']}")
        else:
            typer.echo(typer.style(f"✗ Failed to trigger task", fg=typer.colors.RED), err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="Task ID"),
    confirm: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a task (and all its runs)."""
    try:
        if not confirm:
            if not typer.confirm(f"Delete task {task_id[:8]}?"):
                typer.echo("Cancelled")
                return

        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()
        pg.execute_write(
            "DELETE FROM scheduled_tasks WHERE id = %s",
            (task_id,)
        )

        typer.echo(typer.style(f"✓ Deleted task {task_id[:8]}", fg=typer.colors.GREEN))

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


# ============================================================================
# Task Run/History Commands
# ============================================================================

@app.command()
def runs(
    task_id: Optional[str] = typer.Option(None, "--task", "-t", help="Filter by task ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    offset: int = typer.Option(0, "--offset", "-o", help="Pagination offset"),
):
    """List task runs."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService

        pg = get_postgres_connection()
        service = TaskService(pg)

        run_records = service.list_runs(task_id=task_id, status=status, limit=limit, offset=offset)

        if not run_records:
            typer.echo("No runs found")
            return

        # Format for table display
        rows = []
        for run in run_records:
            status_icon = "✓" if run["status"] == "success" else "✗" if run["status"] == "failed" else "⋯"
            duration = f"{run['duration_ms']}ms" if run["duration_ms"] else "—"
            started = run["started_at"].strftime("%Y-%m-%d %H:%M:%S") if run["started_at"] else "—"
            rows.append([
                status_icon,
                run["id"][:8],
                run["status"],
                started,
                duration,
                run["exit_code"] or "—",
            ])

        headers = ["", "ID", "Status", "Started", "Duration", "Exit"]
        typer.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def logs(
    run_id: str = typer.Argument(..., help="Run ID"),
    stderr: bool = typer.Option(False, "--stderr", "-e", help="Show stderr instead"),
):
    """Show logs for a task run."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()

        # Query database for run
        result = pg.execute_read(
            """
            SELECT stdout_log, stderr_log, error_message FROM task_runs WHERE id = %s
            """,
            (run_id,)
        )

        if not result:
            typer.echo(typer.style(f"✗ Run not found: {run_id}", fg=typer.colors.RED), err=True)
            raise typer.Exit(1)

        stdout, stderr_log, error_msg = result[0]

        if stderr:
            typer.echo(typer.style("STDERR:", bold=True))
            typer.echo(stderr_log or "(empty)")
            if error_msg:
                typer.echo("\nERROR:")
                typer.echo(error_msg)
        else:
            typer.echo(typer.style("STDOUT:", bold=True))
            typer.echo(stdout or "(empty)")

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


# ============================================================================
# Statistics Commands
# ============================================================================

@app.command()
def stats():
    """Show overall task statistics."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.task_service import TaskService
        from src.feed.services.nix_env_service import NixEnvironmentService

        pg = get_postgres_connection()
        task_service = TaskService(pg)
        env_service = NixEnvironmentService(pg)

        task_stats = task_service.get_task_stats()
        env_stats = env_service.get_environment_stats()

        typer.echo(typer.style("Task Statistics:", bold=True))
        typer.echo(f"  Total tasks: {task_stats.get('total_tasks', 0)}")
        typer.echo(f"  Enabled: {task_stats.get('enabled_tasks', 0)}")
        typer.echo(f"  Total runs: {task_stats.get('total_runs', 0)}")
        typer.echo(f"  Successful: {task_stats.get('successful_runs', 0)}")
        typer.echo(f"  Failed: {task_stats.get('failed_runs', 0)}")

        if task_stats.get('total_runs', 0) > 0:
            success_rate = (task_stats.get('successful_runs', 0) / task_stats.get('total_runs', 0)) * 100
            typer.echo(f"  Success rate: {success_rate:.1f}%")
            typer.echo(f"  Avg duration: {task_stats.get('average_duration_ms', 0):.0f}ms")

        typer.echo()
        typer.echo(typer.style("Nix Environment Cache:", bold=True))
        typer.echo(f"  Total environments: {env_stats.get('total_environments', 0)}")
        typer.echo(f"  Total uses: {env_stats.get('total_uses', 0)}")
        if env_stats.get('total_environments', 0) > 0:
            typer.echo(f"  Average uses: {env_stats.get('average_uses', 0):.1f}")

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


@app.command()
def envs(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    sort_by: str = typer.Option("uses", "--sort", "-s", help="Sort by: uses, last, date"),
):
    """Show cached nix environments."""
    try:
        from src.feed.storage.postgres_connection import get_postgres_connection
        from src.feed.services.nix_env_service import NixEnvironmentService

        pg = get_postgres_connection()
        service = NixEnvironmentService(pg)

        if sort_by == "uses":
            envs = service.get_most_used_environments(limit=limit)
        else:
            envs = service.list_environments(limit=limit, order_by="last_used_at")

        if not envs:
            typer.echo("No environments found")
            return

        # Format for table display
        rows = []
        for env in envs:
            use_count = env.get("use_count", 0)
            package_count = len(env.get("packages", []))
            last_used = env.get("last_used_at", "").strftime("%Y-%m-%d %H:%M:%S") if env.get("last_used_at") else "—"
            rows.append([
                env["hash"][:8],
                package_count,
                use_count,
                last_used,
            ])

        headers = ["Hash", "Packages", "Uses", "Last Used"]
        typer.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    except Exception as e:
        typer.echo(
            typer.style(f"✗ Error: {e}", fg=typer.colors.RED, bold=True),
            err=True
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
