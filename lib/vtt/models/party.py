"""Party and campaign data models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from .character import Character


class Party(BaseModel):
    """Party model for grouping characters."""
    name: str = Field(..., min_length=1, description="Party name")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    description: Optional[str] = Field(None, description="Party description")
    character_uuids: List[UUID] = Field(default_factory=list, description="Character UUIDs in party")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
        }


class Campaign(BaseModel):
    """Campaign model for world/setting context."""
    name: str = Field(..., min_length=1, description="Campaign name")
    setting: Optional[str] = Field(None, description="Campaign setting")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    description: Optional[str] = Field(None, description="Campaign description")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "setting": self.setting,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
        }


class PartyView(BaseModel):
    """Party view with full character details."""
    party: Party
    characters: List[Character] = Field(default_factory=list)

