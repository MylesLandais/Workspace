"""Convenience wrappers for database access."""

from typing import Optional

from infra.psql.connection import PostgresConnection, get_connection
from infra.psql.age import AGEAdapter, get_age


def get_db() -> PostgresConnection:
    """Get the shared PostgresConnection instance."""
    return get_connection()


def get_graph(graph_name: str = "archive_graph") -> AGEAdapter:
    """Get the shared AGEAdapter instance."""
    return get_age(graph_name=graph_name)
