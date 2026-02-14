"""PostgreSQL database connection management for converged archiver."""

import os
from pathlib import Path
from typing import Optional, Any
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class PostgresConnection:
    """Manages PostgreSQL connections using environment variables."""

    def __init__(self, env_path: Optional[Path] = None):
        if env_path:
            self.env_path = env_path
        elif Path("/home/warby/Workspace/jupyter/.env").exists():
            self.env_path = Path("/home/warby/Workspace/jupyter/.env")
        elif Path(".env").exists():
            self.env_path = Path(".env").absolute()
        else:
            self.env_path = Path.home() / "Workspace" / "jupyter" / ".env"
        
        self._load_environment()
        
        self.host = os.getenv("POSTGRES_HOST", "archive_postgres")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "secret")
        self.dbname = os.getenv("POSTGRES_DB", "archive_system")
        
        self.conn_str = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        self._engine = None
        self._SessionLocal = None

    def _load_environment(self) -> None:
        load_dotenv(self.env_path, override=False)

    def get_raw_connection(self):
        """Get a raw psycopg2 connection."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname
        )

    def get_engine(self):
        if self._engine is None:
            self._engine = create_engine(self.conn_str)
        return self._engine

    def get_session(self) -> Session:
        if self._SessionLocal is None:
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.get_engine())
        return self._SessionLocal()

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

# Singleton pattern
_pg_connection = None

def get_postgres_connection(env_path: Optional[Path] = None) -> PostgresConnection:
    global _pg_connection
    if _pg_connection is None:
        _pg_connection = PostgresConnection(env_path)
    return _pg_connection
