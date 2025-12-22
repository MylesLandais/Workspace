"""Neo4j database connection management."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session


class Neo4jConnection:
    """Manages Neo4j database connections using environment variables."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize Neo4j connection.
        
        Args:
            env_path: Path to .env file. Defaults to ~/workspace/.env
        """
        # Support both Docker container and local development
        # Docker: /home/jovyan/workspaces/.env (note: plural "workspaces")
        # Local: ~/Workspace/jupyter/.env or current directory
        if env_path:
            self.env_path = env_path
        elif Path("/home/jovyan/workspaces/.env").exists():
            # Docker container path
            self.env_path = Path("/home/jovyan/workspaces/.env")
        elif Path(".env").exists():
            # Current directory
            self.env_path = Path(".env").absolute()
        else:
            # Local development fallback
            self.env_path = Path.home() / "Workspace" / "jupyter" / ".env"
        self._load_environment()
        
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.uri:
            raise ValueError("NEO4J_URI is missing! Check the .env file path.")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD is missing! Check the .env file path.")
        
        self._driver: Optional[Driver] = None

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        load_dotenv(self.env_path, override=True)
        print(f"Loading Neo4j config from: {self.env_path}")

    def connect(self) -> Driver:
        """
        Create and return a Neo4j driver instance.
        
        Returns:
            Neo4j Driver instance
        """
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Verify connection
            self._driver.verify_connectivity()
            print(f"Connected to Neo4j: {self.uri}")
        return self._driver

    def get_session(self, **kwargs) -> Session:
        """
        Get a Neo4j session.
        
        Args:
            **kwargs: Additional session parameters (e.g., database="neo4j")
        
        Returns:
            Neo4j Session instance
        """
        driver = self.connect()
        return driver.session(**kwargs)

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            print("Neo4j connection closed")

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
        parameters: Optional[dict] = None,
        database: str = "neo4j"
    ) -> list:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (default: "neo4j")
        
        Returns:
            List of result records
        """
        with self.get_session(database=database) as session:
            result = session.run(query, parameters or {})
            return [record for record in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[dict] = None,
        database: str = "neo4j"
    ) -> list:
        """
        Execute a write transaction.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (default: "neo4j")
        
        Returns:
            List of result records
        """
        with self.get_session(database=database) as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return result

    def execute_read(
        self,
        query: str,
        parameters: Optional[dict] = None,
        database: str = "neo4j"
    ) -> list:
        """
        Execute a read transaction.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (default: "neo4j")
        
        Returns:
            List of result records
        """
        with self.get_session(database=database) as session:
            result = session.execute_read(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return result


# Global connection instance (singleton pattern)
_connection: Optional[Neo4jConnection] = None


def get_connection(env_path: Optional[Path] = None) -> Neo4jConnection:
    """
    Get or create a global Neo4j connection instance.
    
    Args:
        env_path: Path to .env file
    
    Returns:
        Neo4jConnection instance
    """
    global _connection
    if _connection is None:
        _connection = Neo4jConnection(env_path)
    return _connection

