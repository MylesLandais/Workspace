"""Unit tests for Character model."""

import pytest
from uuid import UUID
from datetime import datetime

from rpg_graph_vtt.models.character import Character, AbilityScores


class TestAbilityScores:
    """Tests for AbilityScores model."""

    def test_valid_ability_scores(self):
        """Test creating valid ability scores."""
        scores = AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=12,
            wisdom=13,
            charisma=10,
        )
        assert scores.strength == 16
        assert scores.dexterity == 14

    def test_ability_score_bounds(self):
        """Test ability score validation bounds."""
        # Minimum value
        scores = AbilityScores(
            strength=1,
            dexterity=1,
            constitution=1,
            intelligence=1,
            wisdom=1,
            charisma=1,
        )
        assert scores.strength == 1

        # Maximum value
        scores = AbilityScores(
            strength=30,
            dexterity=30,
            constitution=30,
            intelligence=30,
            wisdom=30,
            charisma=30,
        )
        assert scores.strength == 30

    def test_invalid_ability_score_too_low(self):
        """Test that ability scores below 1 are rejected."""
        with pytest.raises(Exception):  # Pydantic validation error
            AbilityScores(
                strength=0,
                dexterity=14,
                constitution=15,
                intelligence=12,
                wisdom=13,
                charisma=10,
            )

    def test_invalid_ability_score_too_high(self):
        """Test that ability scores above 30 are rejected."""
        with pytest.raises(Exception):  # Pydantic validation error
            AbilityScores(
                strength=31,
                dexterity=14,
                constitution=15,
                intelligence=12,
                wisdom=13,
                charisma=10,
            )


class TestCharacter:
    """Tests for Character model."""

    def test_create_character(self, sample_character_data):
        """Test creating a character with valid data."""
        char = Character(
            uuid=UUID(sample_character_data["uuid"]),
            name=sample_character_data["name"],
            level=sample_character_data["level"],
            hit_points=sample_character_data["hit_points"],
            hit_points_max=sample_character_data["hit_points_max"],
            armor_class=sample_character_data["armor_class"],
            proficiency_bonus=sample_character_data["proficiency_bonus"],
            ability_scores=AbilityScores(**sample_character_data["ability_scores"]),
            ability_modifiers=sample_character_data["ability_modifiers"],
            saving_throws=sample_character_data["saving_throws"],
            skills=sample_character_data["skills"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert char.name == "Test Character"
        assert char.level == 5

    def test_character_level_bounds(self):
        """Test character level validation."""
        # Valid levels
        for level in [1, 10, 20]:
            char = Character(
                uuid=UUID("123e4567-e89b-12d3-a456-426614174000"),
                name="Test",
                level=level,
                hit_points=10,
                hit_points_max=10,
                armor_class=10,
                proficiency_bonus=2,
                ability_scores=AbilityScores(
                    strength=10,
                    dexterity=10,
                    constitution=10,
                    intelligence=10,
                    wisdom=10,
                    charisma=10,
                ),
                ability_modifiers={},
                saving_throws={},
                skills={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            assert char.level == level

