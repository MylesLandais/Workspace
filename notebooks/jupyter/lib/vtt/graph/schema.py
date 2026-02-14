"""Neo4j graph schema definitions and validation."""

from typing import Dict, List, Optional
from datetime import datetime


class GraphSchema:
    """Defines the Neo4j graph schema for D&D 5e character management."""

    # Node labels
    CHARACTER = "Character"
    CLASS = "Class"
    SUBCLASS = "Subclass"
    RACE = "Race"
    BACKGROUND = "Background"
    SPELL = "Spell"
    ITEM = "Item"
    FEATURE = "Feature"
    FEAT = "Feat"
    PARTY = "Party"
    CAMPAIGN = "Campaign"

    # Relationship types
    HAS_CLASS = "HAS_CLASS"
    HAS_SUBCLASS = "HAS_SUBCLASS"
    HAS_RACE = "HAS_RACE"
    HAS_BACKGROUND = "HAS_BACKGROUND"
    OWNS = "OWNS"
    KNOWS_SPELL = "KNOWS_SPELL"
    HAS_FEATURE = "HAS_FEATURE"
    HAS_FEAT = "HAS_FEAT"
    BELONGS_TO_PARTY = "BELONGS_TO_PARTY"
    GRANTS_FEATURE = "GRANTS_FEATURE"
    CAN_LEARN_SPELL = "CAN_LEARN_SPELL"
    REQUIRES_CLASS = "REQUIRES_CLASS"
    REQUIRES_ATTUNEMENT = "REQUIRES_ATTUNEMENT"
    HAS_CAMPAIGN = "HAS_CAMPAIGN"

    @staticmethod
    def get_character_properties() -> Dict[str, str]:
        """Return expected properties for Character nodes."""
        return {
            "uuid": "String (unique)",
            "name": "String",
            "level": "Integer (1-20)",
            "hit_points": "Integer",
            "hit_points_max": "Integer",
            "armor_class": "Integer",
            "proficiency_bonus": "Integer",
            "ability_scores": "Map {str, dex, con, int, wis, cha}",
            "ability_modifiers": "Map {str, dex, con, int, wis, cha}",
            "saving_throws": "Map {ability: Boolean}",
            "skills": "Map {skill_name: Boolean}",
            "created_at": "DateTime",
            "updated_at": "DateTime",
        }

    @staticmethod
    def get_class_properties() -> Dict[str, str]:
        """Return expected properties for Class nodes."""
        return {
            "name": "String (unique)",
            "hit_die": "Integer",
            "primary_ability": "String",
            "saving_throw_proficiencies": "List[String]",
            "skill_proficiencies_count": "Integer",
            "available_skills": "List[String]",
            "spellcasting_ability": "String (nullable)",
            "subclasses": "List[String]",
        }

    @staticmethod
    def get_race_properties() -> Dict[str, str]:
        """Return expected properties for Race nodes."""
        return {
            "name": "String (unique)",
            "ability_score_increases": "Map {ability: Integer}",
            "size": "String",
            "speed": "Integer",
            "traits": "List[String]",
        }

    @staticmethod
    def get_spell_properties() -> Dict[str, str]:
        """Return expected properties for Spell nodes."""
        return {
            "name": "String (unique)",
            "level": "Integer (0-9)",
            "school": "String",
            "casting_time": "String",
            "range": "String",
            "components": "String",
            "material_components": "String (nullable)",
            "duration": "String",
            "description": "String",
            "higher_levels": "String (nullable)",
            "ritual": "Boolean",
            "concentration": "Boolean",
        }

    @staticmethod
    def validate_character_data(data: Dict) -> List[str]:
        """Validate character data against schema. Returns list of errors."""
        errors = []
        required = ["uuid", "name", "level", "hit_points", "hit_points_max", "armor_class"]
        
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "level" in data and (data["level"] < 1 or data["level"] > 20):
            errors.append("Level must be between 1 and 20")
        
        if "ability_scores" in data:
            abilities = ["str", "dex", "con", "int", "wis", "cha"]
            for ability in abilities:
                if ability not in data["ability_scores"]:
                    errors.append(f"Missing ability score: {ability}")
                elif data["ability_scores"][ability] < 1 or data["ability_scores"][ability] > 30:
                    errors.append(f"Ability score {ability} must be between 1 and 30")
        
        return errors

