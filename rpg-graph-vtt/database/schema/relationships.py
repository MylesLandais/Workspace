"""Neo4j relationship type definitions."""

from typing import Dict, List, Tuple


def get_relationship_types() -> Dict[str, Dict[str, any]]:
    """
    Get all relationship type definitions.
    
    Returns:
        Dictionary mapping relationship types to their metadata
    """
    return {
        # Character relationships
        "HAS_CLASS": {
            "from": "Character",
            "to": "Class",
            "properties": ["level"],
            "description": "Character's class and level in that class",
        },
        "HAS_SUBCLASS": {
            "from": "Character",
            "to": "Subclass",
            "properties": [],
            "description": "Character's chosen subclass",
        },
        "HAS_RACE": {
            "from": "Character",
            "to": "Race",
            "properties": [],
            "description": "Character's race",
        },
        "HAS_BACKGROUND": {
            "from": "Character",
            "to": "Background",
            "properties": [],
            "description": "Character's background",
        },
        "OWNS": {
            "from": "Character",
            "to": "Item",
            "properties": ["equipped", "quantity"],
            "description": "Character inventory items",
        },
        "KNOWS_SPELL": {
            "from": "Character",
            "to": "Spell",
            "properties": ["prepared", "source"],
            "description": "Character's known/prepared spells",
        },
        "HAS_FEATURE": {
            "from": "Character",
            "to": "Feature",
            "properties": [],
            "description": "Character's features",
        },
        "HAS_FEAT": {
            "from": "Character",
            "to": "Feat",
            "properties": [],
            "description": "Character's feats",
        },
        "BELONGS_TO_PARTY": {
            "from": "Character",
            "to": "Party",
            "properties": [],
            "description": "Character membership in party",
        },
        # Game system relationships
        "GRANTS_FEATURE": {
            "from": ["Class", "Subclass", "Race", "Background"],
            "to": "Feature",
            "properties": ["level"],
            "description": "Features granted by class/race/background",
        },
        "CAN_LEARN_SPELL": {
            "from": "Class",
            "to": "Spell",
            "properties": [],
            "description": "Spells available to a class",
        },
        "REQUIRES_CLASS": {
            "from": "Spell",
            "to": "Class",
            "properties": [],
            "description": "Class requirements for spells",
        },
        "REQUIRES_ATTUNEMENT": {
            "from": "Item",
            "to": "Character",
            "properties": [],
            "description": "Item attunement requirements",
        },
        # Campaign relationships
        "HAS_CAMPAIGN": {
            "from": "Party",
            "to": "Campaign",
            "properties": [],
            "description": "Party's campaign",
        },
    }


def get_relationships_by_node(label: str) -> List[Tuple[str, str, str]]:
    """
    Get all relationships for a given node label.
    
    Args:
        label: Node label
        
    Returns:
        List of (relationship_type, direction, target_label) tuples
    """
    relationships = []
    for rel_type, metadata in get_relationship_types().items():
        from_labels = (
            metadata["from"] if isinstance(metadata["from"], list) else [metadata["from"]]
        )
        to_label = metadata["to"]
        
        if label in from_labels:
            relationships.append((rel_type, "outgoing", to_label))
        if label == to_label:
            relationships.append((rel_type, "incoming", from_labels[0]))
    
    return relationships

