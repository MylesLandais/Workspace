"""Game system data models (Class, Race, Background, Spell, Item, Feature)."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class Class(BaseModel):
    """D&D 5e character class."""
    name: str = Field(..., description="Class name")
    hit_die: int = Field(..., ge=4, le=12, description="Hit die size")
    primary_ability: str = Field(..., description="Primary ability score")
    saving_throw_proficiencies: List[str] = Field(default_factory=list, description="Saving throw proficiencies")
    skill_proficiencies_count: int = Field(default=0, ge=0, description="Number of skill proficiencies to choose")
    available_skills: List[str] = Field(default_factory=list, description="Available skill choices")
    spellcasting_ability: Optional[str] = Field(None, description="Spellcasting ability (if applicable)")
    subclasses: List[str] = Field(default_factory=list, description="Available subclasses")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "hit_die": self.hit_die,
            "primary_ability": self.primary_ability,
            "saving_throw_proficiencies": self.saving_throw_proficiencies,
            "skill_proficiencies_count": self.skill_proficiencies_count,
            "available_skills": self.available_skills,
            "spellcasting_ability": self.spellcasting_ability,
            "subclasses": self.subclasses,
        }


class Race(BaseModel):
    """D&D 5e character race."""
    name: str = Field(..., description="Race name")
    ability_score_increases: Dict[str, int] = Field(default_factory=dict, description="Ability score bonuses")
    size: str = Field(..., description="Creature size")
    speed: int = Field(..., ge=0, description="Base walking speed in feet")
    traits: List[str] = Field(default_factory=list, description="Racial traits")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "ability_score_increases": self.ability_score_increases,
            "size": self.size,
            "speed": self.speed,
            "traits": self.traits,
        }


class Background(BaseModel):
    """D&D 5e character background."""
    name: str = Field(..., description="Background name")
    skill_proficiencies: List[str] = Field(default_factory=list, description="Granted skill proficiencies")
    tool_proficiencies: List[str] = Field(default_factory=list, description="Granted tool proficiencies")
    languages: List[str] = Field(default_factory=list, description="Additional languages")
    equipment: List[str] = Field(default_factory=list, description="Starting equipment")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "skill_proficiencies": self.skill_proficiencies,
            "tool_proficiencies": self.tool_proficiencies,
            "languages": self.languages,
            "equipment": self.equipment,
        }


class Spell(BaseModel):
    """D&D 5e spell."""
    name: str = Field(..., description="Spell name")
    level: int = Field(..., ge=0, le=9, description="Spell level (0=cantrip)")
    school: str = Field(..., description="Magic school")
    casting_time: str = Field(..., description="Casting time")
    range: str = Field(..., description="Spell range")
    components: str = Field(..., description="Components (V, S, M)")
    material_components: Optional[str] = Field(None, description="Material components description")
    duration: str = Field(..., description="Spell duration")
    description: str = Field(..., description="Spell description")
    higher_levels: Optional[str] = Field(None, description="Effects at higher levels")
    ritual: bool = Field(default=False, description="Can be cast as ritual")
    concentration: bool = Field(default=False, description="Requires concentration")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "level": self.level,
            "school": self.school,
            "casting_time": self.casting_time,
            "range": self.range,
            "components": self.components,
            "material_components": self.material_components,
            "duration": self.duration,
            "description": self.description,
            "higher_levels": self.higher_levels,
            "ritual": self.ritual,
            "concentration": self.concentration,
        }


class Item(BaseModel):
    """D&D 5e item (equipment, weapons, armor)."""
    name: str = Field(..., description="Item name")
    type: str = Field(..., description="Item type")
    rarity: Optional[str] = Field(None, description="Item rarity")
    weight: float = Field(..., ge=0, description="Weight in pounds")
    cost: int = Field(default=0, ge=0, description="Cost in gold pieces")
    description: Optional[str] = Field(None, description="Item description")
    properties: Optional[Dict] = Field(None, description="Item-specific properties")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "type": self.type,
            "rarity": self.rarity,
            "weight": self.weight,
            "cost": self.cost,
            "description": self.description,
            "properties": self.properties,
        }


class Feature(BaseModel):
    """D&D 5e feature (class feature, racial feature, etc.)."""
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    source_type: str = Field(..., description="Source type (class, race, background, feat)")
    level_obtained: Optional[int] = Field(None, ge=1, le=20, description="Level at which feature is obtained")
    prerequisites: Optional[Dict] = Field(None, description="Prerequisites")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "level_obtained": self.level_obtained,
            "prerequisites": self.prerequisites,
        }

