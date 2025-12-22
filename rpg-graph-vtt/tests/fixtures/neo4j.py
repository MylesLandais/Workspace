"""Neo4j test database fixtures."""

import pytest
from rpg_graph_vtt.graph.connection import Neo4jConnection


@pytest.fixture(scope="session")
def test_neo4j_connection():
    """
    Create a Neo4j connection for integration tests.
    
    Note: This requires a test Neo4j instance to be running.
    Set NEO4J_URI_TEST environment variable to use a separate test database.
    """
    import os
    from pathlib import Path
    
    # Check for test-specific environment
    test_env_path = Path(".env.test")
    if test_env_path.exists():
        return Neo4jConnection(env_path=test_env_path)
    
    # Otherwise, use default connection (may point to test DB)
    return Neo4jConnection()


@pytest.fixture(scope="function")
def clean_test_database(test_neo4j_connection):
    """
    Clean test database before each test.
    
    WARNING: This deletes all data in the database!
    Only use with a dedicated test database.
    """
    # Delete all nodes and relationships
    test_neo4j_connection.execute_write(
        "MATCH (n) DETACH DELETE n"
    )
    yield
    # Cleanup after test
    test_neo4j_connection.execute_write(
        "MATCH (n) DETACH DELETE n"
    )

