"""API response models for FastAPI endpoints."""

from typing import List

from pydantic import BaseModel


class CharacterResponse(BaseModel):
    """Character response model with all relationships."""

    uuid: str
    name: str
    level: int
    hit_points: int
    hit_points_max: int
    armor_class: int
    proficiency_bonus: int
    ability_scores: dict
    ability_modifiers: dict
    saving_throws: dict
    skills: dict
    classes: List[dict] = []
    races: List[dict] = []
    backgrounds: List[dict] = []
    items: List[dict] = []


class PartyResponse(BaseModel):
    """Party response model with character list."""

    name: str
    characters: List[CharacterResponse]

