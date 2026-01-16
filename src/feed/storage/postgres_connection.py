"""PostgreSQL database connection management for task scheduler."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool


class PostgresConnection:
    """Manages PostgreSQL database connections using environment variables."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize PostgreSQL connection.

        Args:
            env_path: Path to .env file. Defaults to auto-detected location
        """
        # Support both Docker container and local development
        if env_path:
            self.env_path = env_path
        elif Path("/home/jovyan/workspaces/.env").exists():
            self.env_path = Path("/home/jovyan/workspaces/.env")
        elif Path(".env").exists():
            self.env_path = Path(".env").absolute()
        else:
            self.env_path = Path.home() / "Workspace" / "jupyter" / ".env"

        self._load_environment()

        self.url = os.getenv("POSTGRES_URL")

        if not self.url:
            raise ValueError("POSTGRES_URL is missing! Check the .env file path.")

        self._pool: Optional[SimpleConnectionPool] = None

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        load_dotenv(self.env_path, override=False)

    def connect(self) -> SimpleConnectionPool:
        """
        Create and return a PostgreSQL connection pool.

        Returns:
            PostgreSQL SimpleConnectionPool instance
        """
        if self._pool is None:
            self._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.url
            )
            # Test connection
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            finally:
                self._pool.putconn(conn)

        return self._pool

    def get_conn(self):
        """
        Get a connection from the pool.

        Returns:
            psycopg2 connection
        """
        pool = self.connect()
        return pool.getconn()

    def return_conn(self, conn) -> None:
        """Return a connection to the pool."""
        if self._pool:
            self._pool.putconn(conn)

    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string
            parameters: Query parameters
            fetch: Whether to fetch results

        Returns:
            List of result dictionaries
        """
        conn = self.get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, parameters or {})
                if fetch:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                conn.commit()
                return []
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.return_conn(conn)

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a write transaction and return RETURNING clause result.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            First row from RETURNING clause if present
        """
        conn = self.get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, parameters or {})
                conn.commit()
                if cursor.description:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.return_conn(conn)

    def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a read-only query.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            List of result dictionaries
        """
        conn = self.get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, parameters or {})
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            raise e
        finally:
            self.return_conn(conn)

    def execute_batch(
        self,
        query: str,
        parameters_list: List[Dict[str, Any]]
    ) -> None:
        """
        Execute a batch of write operations in a single transaction.

        Args:
            query: SQL query string
            parameters_list: List of parameter dictionaries
        """
        conn = self.get_conn()
        try:
            with conn.cursor() as cursor:
                for parameters in parameters_list:
                    cursor.execute(query, parameters)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.return_conn(conn)

    # Task scheduler specific query helpers

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a scheduled task by ID."""
        query = """
        SELECT * FROM scheduled_tasks
        WHERE id = %(task_id)s
        LIMIT 1
        """
        results = self.execute_read(query, {"task_id": task_id})
        return results[0] if results else None

    def list_tasks(
        self,
        enabled_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List scheduled tasks with pagination."""
        where_clause = "WHERE enabled = true" if enabled_only else ""
        query = f"""
        SELECT * FROM scheduled_tasks
        {where_clause}
        ORDER BY next_run_at ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        return self.execute_read(query, {"limit": limit, "offset": offset})

    def get_task_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a task run by ID."""
        query = """
        SELECT * FROM task_runs
        WHERE id = %(run_id)s
        LIMIT 1
        """
        results = self.execute_read(query, {"run_id": run_id})
        return results[0] if results else None

    def list_task_runs(
        self,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List task runs with filtering."""
        where_clauses = []
        params: Dict[str, Any] = {"limit": limit}

        if task_id:
            where_clauses.append("task_id = %(task_id)s")
            params["task_id"] = task_id

        if status:
            where_clauses.append("status = %(status)s")
            params["status"] = status

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
        SELECT * FROM task_runs
        {where_clause}
        ORDER BY started_at DESC
        LIMIT %(limit)s
        """
        return self.execute_read(query, params)

    def get_nix_environment(self, hash: str) -> Optional[Dict[str, Any]]:
        """Get a nix environment by hash."""
        query = """
        SELECT * FROM nix_environments
        WHERE hash = %(hash)s
        LIMIT 1
        """
        results = self.execute_read(query, {"hash": hash})
        return results[0] if results else None

    def update_nix_environment_usage(self, hash: str) -> None:
        """Update nix environment usage statistics."""
        query = """
        UPDATE nix_environments
        SET use_count = use_count + 1,
            last_used_at = NOW()
        WHERE hash = %(hash)s
        """
        self.execute_write(query, {"hash": hash})


# Global connection instance (singleton pattern)
_connection: Optional[PostgresConnection] = None


def get_postgres_connection(env_path: Optional[Path] = None) -> PostgresConnection:
    """
    Get or create a global PostgreSQL connection instance.

    Args:
        env_path: Path to .env file

    Returns:
        PostgresConnection instance
    """
    global _connection
    if _connection is None:
        _connection = PostgresConnection(env_path)
    return _connection
