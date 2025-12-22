"""Neo4j unique constraints definitions."""

from typing import List, Tuple


def get_constraints() -> List[Tuple[str, str, str]]:
    """
    Get all unique constraints as (label, property, description) tuples.
    
    Returns:
        List of constraint definitions
    """
    return [
        ("Character", "uuid", "Unique identifier for characters"),
        ("Class", "name", "Unique class name"),
        ("Race", "name", "Unique race name"),
        ("Background", "name", "Unique background name"),
        ("Spell", "name", "Unique spell name"),
        ("Feat", "name", "Unique feat name"),
        ("Party", "name", "Unique party name"),
        ("Campaign", "name", "Unique campaign name"),
    ]


def generate_constraint_cypher(label: str, property_name: str) -> str:
    """
    Generate Cypher statement for creating a unique constraint.
    
    Args:
        label: Node label
        property_name: Property name
        
    Returns:
        Cypher CREATE CONSTRAINT statement
    """
    constraint_name = f"{label.lower()}_{property_name}"
    return (
        f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
        f"FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE;"
    )


def generate_all_constraints_cypher() -> str:
    """Generate all constraint creation statements."""
    statements = []
    for label, property_name, _ in get_constraints():
        statements.append(generate_constraint_cypher(label, property_name))
    return "\n".join(statements)

