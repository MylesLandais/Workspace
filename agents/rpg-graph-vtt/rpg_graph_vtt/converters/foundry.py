"""Foundry VTT JSON import/export converters."""

from typing import Dict, Optional
from uuid import UUID
from ..models.character import Character, AbilityScores


class FoundryConverter:
    """Converter for Foundry VTT actor JSON format."""

    @staticmethod
    def from_foundry_json(foundry_data: Dict) -> Character:
        """
        Convert Foundry VTT actor JSON to Character model.
        
        Args:
            foundry_data: Foundry VTT actor JSON dictionary
        
        Returns:
            Character model instance
        """
        # Extract basic info
        name = foundry_data.get("name", "Unnamed")
        uuid = UUID(foundry_data.get("_id", ""))
        
        # Extract system data
        system = foundry_data.get("data", {}).get("system", {})
        
        # Level
        level = system.get("details", {}).get("level", {}).get("value", 1)
        
        # Hit points
        hp = system.get("attributes", {}).get("hp", {})
        hit_points = hp.get("value", 0)
        hit_points_max = hp.get("max", 1)
        
        # Armor class
        armor_class = system.get("attributes", {}).get("ac", {}).get("value", 10)
        
        # Ability scores
        abilities = system.get("abilities", {})
        ability_scores = AbilityScores(
            strength=abilities.get("str", {}).get("value", 10),
            dexterity=abilities.get("dex", {}).get("value", 10),
            constitution=abilities.get("con", {}).get("value", 10),
            intelligence=abilities.get("int", {}).get("value", 10),
            wisdom=abilities.get("wis", {}).get("value", 10),
            charisma=abilities.get("cha", {}).get("value", 10),
        )
        
        # Calculate modifiers
        modifiers = ability_scores.get_modifiers()
        
        # Proficiency bonus
        proficiency_bonus = system.get("attributes", {}).get("prof", 2)
        
        # Saving throws (extract from system)
        saving_throws = {}
        saves = system.get("attributes", {}).get("saves", {})
        for ability in ["str", "dex", "con", "int", "wis", "cha"]:
            saving_throws[ability] = saves.get(ability, {}).get("proficient", False)
        
        # Skills (extract from system)
        skills = {}
        skill_data = system.get("skills", {})
        for skill_name, skill_info in skill_data.items():
            if isinstance(skill_info, dict):
                skills[skill_name] = skill_info.get("proficient", False)
        
        # Create character
        character = Character(
            uuid=uuid,
            name=name,
            level=level,
            hit_points=hit_points,
            hit_points_max=hit_points_max,
            armor_class=armor_class,
            proficiency_bonus=proficiency_bonus,
            ability_scores=ability_scores,
            ability_modifiers=modifiers,
            saving_throws=saving_throws,
            skills=skills,
        )
        
        return character

    @staticmethod
    def to_foundry_json(character: Character) -> Dict:
        """
        Convert Character model to Foundry VTT actor JSON format.
        
        Args:
            character: Character model instance
        
        Returns:
            Foundry VTT actor JSON dictionary
        """
        # Build Foundry VTT structure
        foundry_data = {
            "_id": str(character.uuid),
            "name": character.name,
            "type": "character",
            "data": {
                "system": {
                    "details": {
                        "level": {
                            "value": character.level
                        }
                    },
                    "attributes": {
                        "hp": {
                            "value": character.hit_points,
                            "max": character.hit_points_max
                        },
                        "ac": {
                            "value": character.armor_class
                        },
                        "prof": character.proficiency_bonus,
                        "abilities": {
                            "str": {
                                "value": character.ability_scores.strength,
                                "mod": character.ability_modifiers.get("str", 0)
                            },
                            "dex": {
                                "value": character.ability_scores.dexterity,
                                "mod": character.ability_modifiers.get("dex", 0)
                            },
                            "con": {
                                "value": character.ability_scores.constitution,
                                "mod": character.ability_modifiers.get("con", 0)
                            },
                            "int": {
                                "value": character.ability_scores.intelligence,
                                "mod": character.ability_modifiers.get("int", 0)
                            },
                            "wis": {
                                "value": character.ability_scores.wisdom,
                                "mod": character.ability_modifiers.get("wis", 0)
                            },
                            "cha": {
                                "value": character.ability_scores.charisma,
                                "mod": character.ability_modifiers.get("cha", 0)
                            }
                        },
                        "saves": {
                            ability: {"proficient": character.saving_throws.get(ability, False)}
                            for ability in ["str", "dex", "con", "int", "wis", "cha"]
                        }
                    },
                    "skills": {
                        skill_name: {"proficient": proficient}
                        for skill_name, proficient in character.skills.items()
                    }
                }
            }
        }
        
        return foundry_data



