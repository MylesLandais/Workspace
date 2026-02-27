"""Task scheduler package for Celery-based job orchestration.

Provides distributed task execution with PostgreSQL persistence and nix-shell
environment isolation for reproducible Python script execution.
"""

from .celery_app import app as celery_app

__all__ = ["celery_app"]
