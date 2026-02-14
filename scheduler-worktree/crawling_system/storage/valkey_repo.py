"""Valkey/Redis connection management for Crawler system."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import redis


class ValkeyRepository:
    """Manages Valkey/Redis connections using environment variables."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize Valkey/Redis connection.

        Args:
            env_path: Path to .env file. Defaults to workspace root.
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

        valkey_uri = os.getenv("VALKEY_URI", "redis://valkey:6379")
        valkey_password = os.getenv("VALKEY_PASSWORD")

        # Parse Redis URI
        if valkey_uri.startswith("redis://"):
            valkey_uri = valkey_uri.replace("redis://", "")

        if ":" in valkey_uri:
            host, port = valkey_uri.split(":", 1)
            port = int(port)
        else:
            host = valkey_uri
            port = 6379

        self.host = host
        self.port = port
        self.password = valkey_password
        self._client: Optional[redis.Redis] = None

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        load_dotenv(self.env_path, override=True)

    def connect(self) -> redis.Redis:
        """
        Create and return a Redis client instance.

        Returns:
            Redis client instance
        """
        if self._client is None:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Verify connection
            self._client.ping()
        return self._client

    def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client, connecting if necessary."""
        if self._client is None:
            self.connect()
        return self._client


# Global connection instance (singleton pattern)
_valkey_connection: Optional[ValkeyRepository] = None


def get_connection(env_path: Optional[Path] = None) -> ValkeyRepository:
    """
    Get or create a global Valkey connection instance.

    Args:
        env_path: Path to .env file

    Returns:
        ValkeyRepository instance
    """
    global _valkey_connection
    if _valkey_connection is None:
        _valkey_connection = ValkeyRepository(env_path)
    return _valkey_connection
