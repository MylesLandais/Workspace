"""Tools for AI agents to interact with Neo4j graph."""

from typing import List, Dict, Optional
from uuid import UUID
from .graph.connection import get_connection
from .graph.queries import CharacterQueries, PartyQueries, GameSystemQueries


def query_character_info(character_name: str) -> Dict:
    """
    Query character information by name.
    
    Args:
        character_name: Name of the character
    
    Returns:
        Character information dictionary
    """
    conn = get_connection()
    query = """
    MATCH (c:Character {name: $name})
    OPTIONAL MATCH (c)-[:HAS_CLASS]->(class:Class)
    OPTIONAL MATCH (c)-[:HAS_RACE]->(race:Race)
    RETURN c, collect(DISTINCT class) AS classes, collect(DISTINCT race) AS races
    """
    
    result = conn.execute_read(query, {"name": character_name})
    if result:
        record = result[0]
        return {
            "character": dict(record["c"]),
            "classes": [dict(c) for c in record["classes"] if c],
            "races": [dict(r) for r in record["races"] if r],
        }
    return {}


def query_available_spells(class_name: str, level: int) -> List[Dict]:
    """
    Query spells available to a class at a given level.
    
    Args:
        class_name: Name of the class
        level: Character level
    
    Returns:
        List of available spells
    """
    conn = get_connection()
    return GameSystemQueries.get_available_spells(class_name, level, conn)


def query_class_features(class_name: str, level: int) -> List[Dict]:
    """
    Query features available to a class at a given level.
    
    Args:
        class_name: Name of the class
        level: Character level
    
    Returns:
        List of features
    """
    conn = get_connection()
    query = """
    MATCH (c:Class {name: $class_name})-[:GRANTS_FEATURE {level: $level}]->(f:Feature)
    RETURN f
    ORDER BY f.name
    """
    
    result = conn.execute_read(query, {"class_name": class_name, "level": level})
    return [dict(record["f"]) for record in result]


def query_multiclass_prerequisites(class_name: str) -> Dict:
    """
    Query multiclass prerequisites for a class.
    
    Args:
        class_name: Name of the class
    
    Returns:
        Prerequisites dictionary
    """
    conn = get_connection()
    query = """
    MATCH (c:Class {name: $class_name})
    RETURN c.primary_ability AS primary_ability,
           c.saving_throw_proficiencies AS saving_throws
    """
    
    result = conn.execute_read(query, {"class_name": class_name})
    if result:
        return dict(result[0])
    return {}


def query_party_characters(party_name: str) -> List[Dict]:
    """
    Query all characters in a party.
    
    Args:
        party_name: Name of the party
    
    Returns:
        List of character dictionaries
    """
    conn = get_connection()
    return PartyQueries.get_party_characters(party_name, conn)


def validate_character_build(
    class_name: str,
    race_name: str,
    ability_scores: Dict[str, int]
) -> Dict[str, any]:
    """
    Validate a character build against D&D 5e rules.
    
    Args:
        class_name: Desired class
        race_name: Desired race
        ability_scores: Dictionary of ability scores
    
    Returns:
        Validation result with errors/warnings
    """
    conn = get_connection()
    errors = []
    warnings = []
    
    # Check if class exists
    class_data = GameSystemQueries.get_class(class_name, conn)
    if not class_data:
        errors.append(f"Class '{class_name}' not found")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check if race exists
    race_data = GameSystemQueries.get_race(race_name, conn)
    if not race_data:
        errors.append(f"Race '{race_name}' not found")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check primary ability score
    primary_ability = class_data.get("primary_ability", "").lower()
    if primary_ability in ability_scores:
        score = ability_scores[primary_ability]
        if score < 13:
            warnings.append(f"Low {primary_ability.upper()} score ({score}) for {class_name}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }



