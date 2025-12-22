"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, MagicMock

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_neo4j_connection():
    """Mock Neo4j connection for unit tests."""
    mock_conn = Mock()
    mock_conn.execute_read = Mock(return_value=[])
    mock_conn.execute_write = Mock(return_value=None)
    return mock_conn


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Character",
        "level": 5,
        "hit_points": 45,
        "hit_points_max": 45,
        "armor_class": 16,
        "proficiency_bonus": 3,
        "ability_scores": {
            "str": 16,
            "dex": 14,
            "con": 15,
            "int": 12,
            "wis": 13,
            "cha": 10,
        },
        "ability_modifiers": {
            "str": 3,
            "dex": 2,
            "con": 2,
            "int": 1,
            "wis": 1,
            "cha": 0,
        },
        "saving_throws": {
            "str": True,
            "dex": False,
            "con": True,
            "int": False,
            "wis": False,
            "cha": False,
        },
        "skills": {
            "athletics": True,
            "perception": False,
        },
    }


@pytest.fixture
def sample_party_data():
    """Sample party data for testing."""
    return {
        "name": "Test Party",
        "description": "A test party for unit tests",
    }


@pytest.fixture
def sample_class_data():
    """Sample class data for testing."""
    return {
        "name": "Fighter",
        "hit_die": 10,
        "primary_ability": "str",
        "saving_throw_proficiencies": ["str", "con"],
        "skill_proficiencies_count": 2,
        "available_skills": [
            "acrobatics",
            "animal_handling",
            "athletics",
            "history",
            "insight",
            "intimidation",
            "perception",
            "survival",
        ],
        "spellcasting_ability": None,
        "subclasses": ["Champion", "Battle Master", "Eldritch Knight"],
    }

