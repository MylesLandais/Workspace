"""Character data models for D&D 5e."""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4


class AbilityScores(BaseModel):
    """D&D 5e ability scores."""
    strength: int = Field(ge=1, le=30, description="Strength score")
    dexterity: int = Field(ge=1, le=30, description="Dexterity score")
    constitution: int = Field(ge=1, le=30, description="Constitution score")
    intelligence: int = Field(ge=1, le=30, description="Intelligence score")
    wisdom: int = Field(ge=1, le=30, description="Wisdom score")
    charisma: int = Field(ge=1, le=30, description="Charisma score")

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary with lowercase keys."""
        return {
            "str": self.strength,
            "dex": self.dexterity,
            "con": self.constitution,
            "int": self.intelligence,
            "wis": self.wisdom,
            "cha": self.charisma,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "AbilityScores":
        """Create from dictionary with lowercase keys."""
        return cls(
            strength=data.get("str", data.get("strength", 10)),
            dexterity=data.get("dex", data.get("dexterity", 10)),
            constitution=data.get("con", data.get("constitution", 10)),
            intelligence=data.get("int", data.get("intelligence", 10)),
            wisdom=data.get("wis", data.get("wisdom", 10)),
            charisma=data.get("cha", data.get("charisma", 10)),
        )

    def calculate_modifier(self, score: int) -> int:
        """Calculate ability modifier from score."""
        return (score - 10) // 2

    def get_modifiers(self) -> Dict[str, int]:
        """Get all ability modifiers."""
        return {
            "str": self.calculate_modifier(self.strength),
            "dex": self.calculate_modifier(self.dexterity),
            "con": self.calculate_modifier(self.constitution),
            "int": self.calculate_modifier(self.intelligence),
            "wis": self.calculate_modifier(self.wisdom),
            "cha": self.calculate_modifier(self.charisma),
        }


class Character(BaseModel):
    """D&D 5e character model."""
    uuid: UUID = Field(default_factory=uuid4, description="Unique character identifier")
    name: str = Field(..., min_length=1, description="Character name")
    level: int = Field(..., ge=1, le=20, description="Character level")
    hit_points: int = Field(..., ge=0, description="Current hit points")
    hit_points_max: int = Field(..., ge=1, description="Maximum hit points")
    armor_class: int = Field(..., ge=0, description="Armor class")
    proficiency_bonus: int = Field(..., ge=0, description="Proficiency bonus")
    ability_scores: AbilityScores = Field(..., description="Ability scores")
    ability_modifiers: Dict[str, int] = Field(default_factory=dict, description="Ability modifiers")
    saving_throws: Dict[str, bool] = Field(default_factory=dict, description="Saving throw proficiencies")
    skills: Dict[str, bool] = Field(default_factory=dict, description="Skill proficiencies")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    @field_validator("proficiency_bonus")
    @classmethod
    def validate_proficiency_bonus(cls, v: int, info) -> int:
        """Calculate proficiency bonus from level if not provided."""
        if v == 0 and "level" in info.data:
            level = info.data["level"]
            return (level - 1) // 4 + 2
        return v

    def model_post_init(self, __context) -> None:
        """Calculate ability modifiers after initialization."""
        if not self.ability_modifiers:
            self.ability_modifiers = self.ability_scores.get_modifiers()

    def to_neo4j_dict(self) -> Dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "level": self.level,
            "hit_points": self.hit_points,
            "hit_points_max": self.hit_points_max,
            "armor_class": self.armor_class,
            "proficiency_bonus": self.proficiency_bonus,
            "ability_scores": self.ability_scores.to_dict(),
            "ability_modifiers": self.ability_modifiers,
            "saving_throws": self.saving_throws,
            "skills": self.skills,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_neo4j_record(cls, record: Dict) -> "Character":
        """Create Character from Neo4j record."""
        data = dict(record)
        data["ability_scores"] = AbilityScores.from_dict(data.get("ability_scores", {}))
        data["uuid"] = UUID(data["uuid"]) if isinstance(data.get("uuid"), str) else data.get("uuid")
        data["created_at"] = datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at")
        data["updated_at"] = datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at")
        return cls(**data)


class CharacterCreate(BaseModel):
    """Model for creating a new character."""
    name: str
    class_name: str
    race_name: str
    background_name: str
    level: int = Field(default=1, ge=1, le=20)
    ability_scores: Optional[AbilityScores] = None
    subclass_name: Optional[str] = None

