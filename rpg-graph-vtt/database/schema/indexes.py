"""Neo4j index definitions."""

from typing import List, Tuple


def get_indexes() -> List[Tuple[str, str, str]]:
    """
    Get all indexes as (label, property, description) tuples.
    
    Returns:
        List of index definitions
    """
    return [
        ("Character", "name", "Index for character name lookups"),
        ("Character", "level", "Index for character level queries"),
        ("Spell", "level", "Index for spell level filtering"),
        ("Spell", "school", "Index for spell school filtering"),
        ("Item", "type", "Index for item type filtering"),
        ("Item", "rarity", "Index for item rarity filtering"),
    ]


def generate_index_cypher(label: str, property_name: str) -> str:
    """
    Generate Cypher statement for creating an index.
    
    Args:
        label: Node label
        property_name: Property name
        
    Returns:
        Cypher CREATE INDEX statement
    """
    index_name = f"{label.lower()}_{property_name}"
    return (
        f"CREATE INDEX {index_name} IF NOT EXISTS "
        f"FOR (n:{label}) ON (n.{property_name});"
    )


def generate_all_indexes_cypher() -> str:
    """Generate all index creation statements."""
    statements = []
    for label, property_name, _ in get_indexes():
        statements.append(generate_index_cypher(label, property_name))
    return "\n".join(statements)

