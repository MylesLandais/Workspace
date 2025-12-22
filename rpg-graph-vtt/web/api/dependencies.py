"""Shared dependencies for API routes."""

from rpg_graph_vtt.graph.connection import Neo4jConnection, get_connection


def get_db_connection() -> Neo4jConnection:
    """Dependency to get Neo4j database connection."""
    return get_connection()

