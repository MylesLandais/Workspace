"""PostgreSQL connection management. Env-var-only config, no hardcoded paths."""

import os
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class PostgresConnection:
    """Manages PostgreSQL connections using environment variables."""

    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "")
        self.dbname = os.getenv("POSTGRES_DB", "postgres")
        self.conn_str = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.dbname}"
        )
        self._engine = None
        self._session_factory = None

    def get_raw_connection(self):
        """Get a raw psycopg2 connection."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
        )

    def get_engine(self):
        """Get or create a SQLAlchemy engine (cached)."""
        if self._engine is None:
            self._engine = create_engine(self.conn_str)
        return self._engine

    def get_session(self) -> Session:
        """Get a new SQLAlchemy session."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=self.get_engine()
            )
        return self._session_factory()

    def execute_query(self, query: str, parameters: Optional[dict] = None) -> list:
        """Execute a raw SQL query and return results as dicts."""
        conn = self.get_raw_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, parameters or {})
                if cur.description:
                    return cur.fetchall()
                conn.commit()
                return []
        finally:
            conn.close()


_connection: Optional[PostgresConnection] = None


def get_connection() -> PostgresConnection:
    """Get the singleton PostgresConnection instance."""
    global _connection
    if _connection is None:
        _connection = PostgresConnection()
    return _connection
