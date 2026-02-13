"""Neo4j database connection management for feed engine with Apache AGE support."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session
from .age_adapter import get_age_connection

class Neo4jConnection:
    """Manages Neo4j database connections or Apache AGE fallback."""

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
        
        self.use_age = os.getenv("CONVERGE_POSTGRES", "false").lower() == "true"
        if self.use_age:
            self.age = get_age_connection()
            self.uri = "postgres://archive_postgres:5432"
            return

        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self._driver: Optional[Driver] = None

    def _load_environment(self) -> None:
        load_dotenv(self.env_path, override=False)

    def connect(self) -> Driver:
        if self.use_age:
            return None
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self._driver.verify_connectivity()
        return self._driver

    def execute_query(self, query: str, parameters: Optional[dict] = None) -> List[Dict]:
        if self.use_age:
            return self.age.execute_query(query, parameters)
        with self.connect().session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def execute_write(self, query: str, parameters: Optional[dict] = None) -> List[Dict]:
        if self.use_age:
            return self.age.execute_write(query, parameters)
        with self.connect().session() as session:
            return session.execute_write(lambda tx: [dict(r) for r in tx.run(query, parameters or {})])

    def execute_read(self, query: str, parameters: Optional[dict] = None) -> List[Dict]:
        if self.use_age:
            return self.age.execute_read(query, parameters)
        with self.connect().session() as session:
            return session.execute_read(lambda tx: [dict(r) for r in tx.run(query, parameters or {})])

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Global instance
_connection: Optional[Neo4jConnection] = None

def get_connection(env_path: Optional[Path] = None) -> Neo4jConnection:
    global _connection
    if _connection is None:
        _connection = Neo4jConnection(env_path)
    return _connection
