"""Character test fixtures."""

from uuid import UUID
from datetime import datetime

# Sample character data for testing
SAMPLE_CHARACTER_1 = {
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Aragorn",
    "level": 10,
    "hit_points": 85,
    "hit_points_max": 85,
    "armor_class": 18,
    "proficiency_bonus": 4,
    "ability_scores": {
        "str": 18,
        "dex": 16,
        "con": 17,
        "int": 14,
        "wis": 15,
        "cha": 13,
    },
    "ability_modifiers": {
        "str": 4,
        "dex": 3,
        "con": 3,
        "int": 2,
        "wis": 2,
        "cha": 1,
    },
    "saving_throws": {
        "str": True,
        "dex": False,
        "con": True,
        "int": False,
        "wis": True,
        "cha": False,
    },
    "skills": {
        "athletics": True,
        "perception": True,
        "survival": True,
    },
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
}

SAMPLE_CHARACTER_2 = {
    "uuid": "223e4567-e89b-12d3-a456-426614174001",
    "name": "Gandalf",
    "level": 15,
    "hit_points": 120,
    "hit_points_max": 120,
    "armor_class": 15,
    "proficiency_bonus": 5,
    "ability_scores": {
        "str": 10,
        "dex": 12,
        "con": 14,
        "int": 20,
        "wis": 18,
        "cha": 16,
    },
    "ability_modifiers": {
        "str": 0,
        "dex": 1,
        "con": 2,
        "int": 5,
        "wis": 4,
        "cha": 3,
    },
    "saving_throws": {
        "str": False,
        "dex": False,
        "con": True,
        "int": True,
        "wis": True,
        "cha": True,
    },
    "skills": {
        "arcana": True,
        "history": True,
        "investigation": True,
        "religion": True,
    },
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
}

