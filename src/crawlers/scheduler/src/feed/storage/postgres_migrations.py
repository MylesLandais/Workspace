#!/usr/bin/env python3
"""PostgreSQL migration runner for task scheduler schema.

Applies numbered SQL migration files from migrations/postgres/ directory.
Call this at application startup or via CLI to ensure schema is up to date.

Usage:
    python -m src.feed.storage.postgres_migrations
    python src/feed/storage/postgres_migrations.py
"""

import os
import glob
from pathlib import Path
from .postgres_connection import get_postgres_connection


def get_migration_files() -> list[tuple[int, str]]:
    """Get sorted list of migration files with their sequence numbers.

    Returns list of (sequence_num, filepath) tuples sorted by sequence.
    """
    migrations_dir = Path(__file__).parent / "migrations" / "postgres"

    if not migrations_dir.exists():
        return []

    migrations = []
    for filepath in sorted(migrations_dir.glob("*.sql")):
        # Parse sequence number from filename (e.g., "001_scheduler_schema.sql")
        try:
            seq_num = int(filepath.stem.split("_")[0])
            migrations.append((seq_num, str(filepath)))
        except (ValueError, IndexError):
            continue

    return migrations


def get_applied_migrations(pg) -> set[int]:
    """Get set of sequence numbers for already-applied migrations.

    Queries the schema_migrations table to find which migrations have run.
    Creates the table if it doesn't exist.
    """
    try:
        # Create migrations tracking table if it doesn't exist
        pg.execute_write("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                sequence_num INTEGER PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        # Query applied migrations
        result = pg.execute_read("SELECT sequence_num FROM schema_migrations ORDER BY sequence_num;")
        return {row[0] for row in (result or [])}
    except Exception as e:
        print(f"Warning: Could not query schema_migrations: {e}")
        return set()


def apply_migration(pg, seq_num: int, filepath: str) -> bool:
    """Apply a single migration file.

    Executes SQL file in a transaction. Marks migration as applied on success.

    Returns True if successful, False otherwise.
    """
    try:
        # Read migration file
        with open(filepath, "r") as f:
            sql = f.read()

        # Execute migration in transaction
        pg.execute_write(sql)

        # Record migration as applied
        pg.execute_write(
            "INSERT INTO schema_migrations (sequence_num) VALUES (%s) ON CONFLICT DO NOTHING;",
            (seq_num,)
        )

        return True
    except Exception as e:
        print(f"Error applying migration {seq_num}: {e}")
        return False


def run_migrations() -> dict:
    """Run all pending migrations.

    Applies SQL migration files in sequence order.
    Skips already-applied migrations.

    Returns dict with results:
    {
        "total": int,
        "applied": int,
        "skipped": int,
        "failed": int,
        "migrations": list of (seq_num, filename, status)
    }
    """
    pg = get_postgres_connection()
    migrations = get_migration_files()
    applied = get_applied_migrations(pg)

    results = {
        "total": len(migrations),
        "applied": 0,
        "skipped": 0,
        "failed": 0,
        "migrations": []
    }

    for seq_num, filepath in migrations:
        filename = Path(filepath).name

        if seq_num in applied:
            results["skipped"] += 1
            results["migrations"].append((seq_num, filename, "skipped"))
            continue

        print(f"Applying migration {seq_num}: {filename}...")

        if apply_migration(pg, seq_num, filepath):
            results["applied"] += 1
            results["migrations"].append((seq_num, filename, "applied"))
            print(f"  ✓ Applied")
        else:
            results["failed"] += 1
            results["migrations"].append((seq_num, filename, "failed"))
            print(f"  ✗ Failed")

    return results


def print_results(results: dict):
    """Print migration results in human-readable format."""
    print(f"\nMigration Summary:")
    print(f"  Total:   {results['total']}")
    print(f"  Applied: {results['applied']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Failed:  {results['failed']}")

    if results['migrations']:
        print(f"\nDetails:")
        for seq_num, filename, status in results['migrations']:
            icon = "✓" if status == "applied" else "◌" if status == "skipped" else "✗"
            print(f"  {icon} {seq_num:03d} {filename} ({status})")


if __name__ == "__main__":
    import sys

    print("PostgreSQL Migration Runner")
    print("-" * 50)

    results = run_migrations()
    print_results(results)

    # Exit with error if any migrations failed
    sys.exit(1 if results["failed"] > 0 else 0)
