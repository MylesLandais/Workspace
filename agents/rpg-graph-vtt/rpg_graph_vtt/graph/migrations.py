"""Neo4j schema migration utilities."""

from pathlib import Path
from typing import Optional
from .connection import Neo4jConnection, get_connection


def run_migration(
    migration_file: Path,
    connection: Optional[Neo4jConnection] = None
) -> bool:
    """
    Run a Cypher migration file.
    
    Args:
        migration_file: Path to .cypher migration file
        connection: Neo4j connection (uses global if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    if connection is None:
        connection = get_connection()
    
    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    print(f"Running migration: {migration_file.name}")
    
    with open(migration_file, "r") as f:
        cypher_script = f.read()
    
    try:
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in cypher_script.split(";") if s.strip()]
        
        for statement in statements:
            if statement:
                connection.execute_write(statement)
        
        print(f"✓ Migration completed: {migration_file.name}")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


def run_all_migrations(
    migrations_dir: Optional[Path] = None,
    connection: Optional[Neo4jConnection] = None
) -> bool:
    """
    Run all migration files in order.
    
    Args:
        migrations_dir: Directory containing migration files
        connection: Neo4j connection (uses global if not provided)
    
    Returns:
        True if all migrations successful, False otherwise
    """
    if migrations_dir is None:
        migrations_dir = Path(__file__).parent.parent.parent / "neo4j" / "migrations"
    
    if connection is None:
        connection = get_connection()
    
    # Get all .cypher files and sort by name
    migration_files = sorted(migrations_dir.glob("*.cypher"))
    
    if not migration_files:
        print("No migration files found")
        return False
    
    print(f"Found {len(migration_files)} migration(s)")
    
    for migration_file in migration_files:
        if not run_migration(migration_file, connection):
            return False
    
    return True



