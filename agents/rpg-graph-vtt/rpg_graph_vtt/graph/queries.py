"""Cypher query builders for character and party operations."""

from typing import Dict, List, Optional
from uuid import UUID
from .connection import Neo4jConnection
from ..models.character import Character
from ..models.party import Party, PartyView
from ..models.game_system import Class, Race, Background, Spell, Item


class CharacterQueries:
    """Query builders for character operations."""

    @staticmethod
    def create_character(character_data: Dict, connection: Neo4jConnection) -> UUID:
        """
        Create a character node in Neo4j.
        
        Args:
            character_data: Character data dictionary
            connection: Neo4j connection
        
        Returns:
            Character UUID
        """
        uuid = character_data["uuid"]
        
        query = """
        CREATE (c:Character {
            uuid: $uuid,
            name: $name,
            level: $level,
            hit_points: $hit_points,
            hit_points_max: $hit_points_max,
            armor_class: $armor_class,
            proficiency_bonus: $proficiency_bonus,
            ability_scores: $ability_scores,
            ability_modifiers: $ability_modifiers,
            saving_throws: $saving_throws,
            skills: $skills,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN c.uuid AS uuid
        """
        
        result = connection.execute_write(query, character_data)
        if result:
            return UUID(result[0]["uuid"])
        raise Exception("Failed to create character")

    @staticmethod
    def get_character(uuid: UUID, connection: Neo4jConnection) -> Optional[Dict]:
        """
        Retrieve a character by UUID.
        
        Args:
            uuid: Character UUID
            connection: Neo4j connection
        
        Returns:
            Character data dictionary or None
        """
        query = """
        MATCH (c:Character {uuid: $uuid})
        RETURN c
        """
        
        result = connection.execute_read(query, {"uuid": str(uuid)})
        if result:
            return dict(result[0]["c"])
        return None

    @staticmethod
    def update_character(uuid: UUID, updates: Dict, connection: Neo4jConnection) -> bool:
        """
        Update character properties.
        
        Args:
            uuid: Character UUID
            updates: Dictionary of properties to update
            connection: Neo4j connection
        
        Returns:
            True if successful
        """
        # Build SET clause dynamically
        set_clauses = []
        params = {"uuid": str(uuid)}
        
        for key, value in updates.items():
            if key != "uuid":  # Don't allow UUID updates
                param_key = f"val_{key}"
                set_clauses.append(f"c.{key} = ${param_key}")
                params[param_key] = value
        
        if not set_clauses:
            return False
        
        set_clauses.append("c.updated_at = datetime()")
        
        query = f"""
        MATCH (c:Character {{uuid: $uuid}})
        SET {', '.join(set_clauses)}
        RETURN c.uuid AS uuid
        """
        
        result = connection.execute_write(query, params)
        return len(result) > 0

    @staticmethod
    def delete_character(uuid: UUID, connection: Neo4jConnection) -> bool:
        """
        Delete a character and all relationships.
        
        Args:
            uuid: Character UUID
            connection: Neo4j connection
        
        Returns:
            True if successful
        """
        query = """
        MATCH (c:Character {uuid: $uuid})
        DETACH DELETE c
        RETURN count(c) AS deleted
        """
        
        result = connection.execute_write(query, {"uuid": str(uuid)})
        return result[0]["deleted"] > 0 if result else False

    @staticmethod
    def link_character_to_class(
        character_uuid: UUID,
        class_name: str,
        level: int,
        connection: Neo4jConnection
    ) -> bool:
        """Link character to a class with level."""
        query = """
        MATCH (c:Character {uuid: $character_uuid})
        MATCH (class:Class {name: $class_name})
        MERGE (c)-[r:HAS_CLASS {level: $level}]->(class)
        RETURN r
        """
        
        result = connection.execute_write(query, {
            "character_uuid": str(character_uuid),
            "class_name": class_name,
            "level": level
        })
        return len(result) > 0

    @staticmethod
    def link_character_to_race(
        character_uuid: UUID,
        race_name: str,
        connection: Neo4jConnection
    ) -> bool:
        """Link character to a race."""
        query = """
        MATCH (c:Character {uuid: $character_uuid})
        MATCH (r:Race {name: $race_name})
        MERGE (c)-[:HAS_RACE]->(r)
        RETURN r
        """
        
        result = connection.execute_write(query, {
            "character_uuid": str(character_uuid),
            "race_name": race_name
        })
        return len(result) > 0

    @staticmethod
    def link_character_to_background(
        character_uuid: UUID,
        background_name: str,
        connection: Neo4jConnection
    ) -> bool:
        """Link character to a background."""
        query = """
        MATCH (c:Character {uuid: $character_uuid})
        MATCH (b:Background {name: $background_name})
        MERGE (c)-[:HAS_BACKGROUND]->(b)
        RETURN b
        """
        
        result = connection.execute_write(query, {
            "character_uuid": str(character_uuid),
            "background_name": background_name
        })
        return len(result) > 0

    @staticmethod
    def add_item_to_character(
        character_uuid: UUID,
        item_name: str,
        equipped: bool = False,
        quantity: int = 1,
        connection: Neo4jConnection = None
    ) -> bool:
        """Add an item to character inventory."""
        query = """
        MATCH (c:Character {uuid: $character_uuid})
        MATCH (i:Item {name: $item_name})
        MERGE (c)-[r:OWNS {equipped: $equipped, quantity: $quantity}]->(i)
        RETURN r
        """
        
        result = connection.execute_write(query, {
            "character_uuid": str(character_uuid),
            "item_name": item_name,
            "equipped": equipped,
            "quantity": quantity
        })
        return len(result) > 0

    @staticmethod
    def get_character_with_relationships(
        uuid: UUID,
        connection: Neo4jConnection
    ) -> Optional[Dict]:
        """Get character with all related nodes."""
        query = """
        MATCH (c:Character {uuid: $uuid})
        OPTIONAL MATCH (c)-[:HAS_CLASS]->(class:Class)
        OPTIONAL MATCH (c)-[:HAS_RACE]->(race:Race)
        OPTIONAL MATCH (c)-[:HAS_BACKGROUND]->(bg:Background)
        OPTIONAL MATCH (c)-[:OWNS]->(item:Item)
        OPTIONAL MATCH (c)-[:KNOWS_SPELL]->(spell:Spell)
        RETURN c,
               collect(DISTINCT class) AS classes,
               collect(DISTINCT race) AS races,
               collect(DISTINCT bg) AS backgrounds,
               collect(DISTINCT item) AS items,
               collect(DISTINCT spell) AS spells
        """
        
        result = connection.execute_read(query, {"uuid": str(uuid)})
        if result:
            record = result[0]
            data = dict(record["c"])
            data["classes"] = [dict(c) for c in record["classes"] if c]
            data["races"] = [dict(r) for r in record["races"] if r]
            data["backgrounds"] = [dict(b) for b in record["backgrounds"] if b]
            data["items"] = [dict(i) for i in record["items"] if i]
            data["spells"] = [dict(s) for s in record["spells"] if s]
            return data
        return None


class PartyQueries:
    """Query builders for party operations."""

    @staticmethod
    def create_party(party_data: Dict, connection: Neo4jConnection) -> str:
        """Create a party node."""
        query = """
        CREATE (p:Party {
            name: $name,
            created_at: datetime(),
            description: $description
        })
        RETURN p.name AS name
        """
        
        result = connection.execute_write(query, party_data)
        if result:
            return result[0]["name"]
        raise Exception("Failed to create party")

    @staticmethod
    def add_character_to_party(
        character_uuid: UUID,
        party_name: str,
        connection: Neo4jConnection
    ) -> bool:
        """Add a character to a party."""
        query = """
        MATCH (c:Character {uuid: $character_uuid})
        MATCH (p:Party {name: $party_name})
        MERGE (c)-[:BELONGS_TO_PARTY]->(p)
        RETURN p.name AS name
        """
        
        result = connection.execute_write(query, {
            "character_uuid": str(character_uuid),
            "party_name": party_name
        })
        return len(result) > 0

    @staticmethod
    def get_party_characters(
        party_name: str,
        connection: Neo4jConnection
    ) -> List[Dict]:
        """Get all characters in a party with full details."""
        query = """
        MATCH (p:Party {name: $party_name})<-[:BELONGS_TO_PARTY]-(c:Character)
        OPTIONAL MATCH (c)-[:HAS_CLASS]->(class:Class)
        OPTIONAL MATCH (c)-[:HAS_RACE]->(race:Race)
        OPTIONAL MATCH (c)-[:HAS_BACKGROUND]->(bg:Background)
        OPTIONAL MATCH (c)-[:OWNS]->(item:Item)
        RETURN c,
               collect(DISTINCT class) AS classes,
               collect(DISTINCT race) AS races,
               collect(DISTINCT bg) AS backgrounds,
               collect(DISTINCT item) AS items
        ORDER BY c.name
        """
        
        result = connection.execute_read(query, {"party_name": party_name})
        characters = []
        
        for record in result:
            char_data = dict(record["c"])
            char_data["classes"] = [dict(c) for c in record["classes"] if c]
            char_data["races"] = [dict(r) for r in record["races"] if r]
            char_data["backgrounds"] = [dict(b) for b in record["backgrounds"] if b]
            char_data["items"] = [dict(i) for i in record["items"] if i]
            characters.append(char_data)
        
        return characters

    @staticmethod
    def get_all_parties(connection: Neo4jConnection) -> List[Dict]:
        """Get all parties."""
        query = """
        MATCH (p:Party)
        OPTIONAL MATCH (p)<-[:BELONGS_TO_PARTY]-(c:Character)
        RETURN p,
               count(c) AS character_count,
               collect(c.name) AS character_names
        ORDER BY p.name
        """
        
        result = connection.execute_read(query)
        parties = []
        
        for record in result:
            party_data = dict(record["p"])
            party_data["character_count"] = record["character_count"]
            party_data["character_names"] = record["character_names"]
            parties.append(party_data)
        
        return parties


class GameSystemQueries:
    """Query builders for game system data (classes, races, spells, etc.)."""

    @staticmethod
    def get_class(class_name: str, connection: Neo4jConnection) -> Optional[Dict]:
        """Get a class by name."""
        query = """
        MATCH (c:Class {name: $class_name})
        RETURN c
        """
        
        result = connection.execute_read(query, {"class_name": class_name})
        if result:
            return dict(result[0]["c"])
        return None

    @staticmethod
    def get_all_classes(connection: Neo4jConnection) -> List[Dict]:
        """Get all classes."""
        query = """
        MATCH (c:Class)
        RETURN c
        ORDER BY c.name
        """
        
        result = connection.execute_read(query)
        return [dict(record["c"]) for record in result]

    @staticmethod
    def get_race(race_name: str, connection: Neo4jConnection) -> Optional[Dict]:
        """Get a race by name."""
        query = """
        MATCH (r:Race {name: $race_name})
        RETURN r
        """
        
        result = connection.execute_read(query, {"race_name": race_name})
        if result:
            return dict(result[0]["r"])
        return None

    @staticmethod
    def get_all_races(connection: Neo4jConnection) -> List[Dict]:
        """Get all races."""
        query = """
        MATCH (r:Race)
        RETURN r
        ORDER BY r.name
        """
        
        result = connection.execute_read(query)
        return [dict(record["r"]) for record in result]

    @staticmethod
    def get_available_spells(
        class_name: str,
        level: int,
        connection: Neo4jConnection
    ) -> List[Dict]:
        """Get spells available to a class at a given level."""
        query = """
        MATCH (c:Class {name: $class_name})-[:CAN_LEARN_SPELL]->(s:Spell)
        WHERE s.level <= $level
        RETURN s
        ORDER BY s.level, s.name
        """
        
        result = connection.execute_read(query, {
            "class_name": class_name,
            "level": level
        })
        return [dict(record["s"]) for record in result]

    @staticmethod
    def find_characters_by_class(
        class_name: str,
        connection: Neo4jConnection
    ) -> List[Dict]:
        """Find all characters of a specific class."""
        query = """
        MATCH (c:Character)-[:HAS_CLASS]->(class:Class {name: $class_name})
        RETURN c
        ORDER BY c.name
        """
        
        result = connection.execute_read(query, {"class_name": class_name})
        return [dict(record["c"]) for record in result]



