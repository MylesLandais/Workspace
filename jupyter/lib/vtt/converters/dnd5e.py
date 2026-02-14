"""D&D 5e schema converter utilities."""

from typing import Dict, Any
from ..models.character import Character


class DnD5eConverter:
    """Converter for standard D&D 5e JSON schema."""

    @staticmethod
    def validate_dnd5e_schema(data: Dict[str, Any]) -> bool:
        """
        Validate that data conforms to D&D 5e schema.
        
        Args:
            data: Data dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "level"]
        return all(field in data for field in required_fields)

    @staticmethod
    def from_dnd5e_json(dnd5e_data: Dict[str, Any]) -> Character:
        """
        Convert D&D 5e JSON to Character model.
        
        Args:
            dnd5e_data: D&D 5e character JSON
        
        Returns:
            Character model instance
        """
        # This is a placeholder - actual implementation would depend on
        # the specific D&D 5e schema format being used
        from uuid import uuid4
        from ..models.character import AbilityScores
        
        name = dnd5e_data.get("name", "Unnamed")
        level = dnd5e_data.get("level", 1)
        
        # Extract ability scores
        abilities = dnd5e_data.get("abilities", {})
        ability_scores = AbilityScores(
            strength=abilities.get("strength", 10),
            dexterity=abilities.get("dexterity", 10),
            constitution=abilities.get("constitution", 10),
            intelligence=abilities.get("intelligence", 10),
            wisdom=abilities.get("wisdom", 10),
            charisma=abilities.get("charisma", 10),
        )
        
        # Create character with defaults
        character = Character(
            uuid=uuid4(),
            name=name,
            level=level,
            hit_points=dnd5e_data.get("hit_points", 10),
            hit_points_max=dnd5e_data.get("hit_points_max", 10),
            armor_class=dnd5e_data.get("armor_class", 10),
            proficiency_bonus=(level - 1) // 4 + 2,
            ability_scores=ability_scores,
        )
        
        return character

    @staticmethod
    def to_dnd5e_json(character: Character) -> Dict[str, Any]:
        """
        Convert Character model to D&D 5e JSON format.
        
        Args:
            character: Character model instance
        
        Returns:
            D&D 5e character JSON dictionary
        """
        return {
            "name": character.name,
            "level": character.level,
            "hit_points": character.hit_points,
            "hit_points_max": character.hit_points_max,
            "armor_class": character.armor_class,
            "proficiency_bonus": character.proficiency_bonus,
            "abilities": {
                "strength": character.ability_scores.strength,
                "dexterity": character.ability_scores.dexterity,
                "constitution": character.ability_scores.constitution,
                "intelligence": character.ability_scores.intelligence,
                "wisdom": character.ability_scores.wisdom,
                "charisma": character.ability_scores.charisma,
            },
            "ability_modifiers": character.ability_modifiers,
            "saving_throws": character.saving_throws,
            "skills": character.skills,
        }

