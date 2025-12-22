"""Creator model for entity resolution system."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Creator(BaseModel):
    """Represents a Creator entity (canonical identity)."""

    uuid: UUID = Field(default_factory=uuid4, description="Unique identifier (UUID)")
    name: str = Field(..., description="Human-readable name (e.g., 'Eefje Depoortere')")
    slug: str = Field(..., description="URL-friendly identifier (e.g., 'sjokz')")
    bio: Optional[str] = Field(default=None, description="Aggregated bio text")
    avatar_url: Optional[str] = Field(default=None, description="Profile picture URL")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "slug": self.slug,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CreatorWithHandles(Creator):
    """Creator with nested handles for GraphQL responses."""

    handles: List["Handle"] = Field(default_factory=list, description="Associated handles")


# Forward reference resolution
from ..models.handle import Handle
CreatorWithHandles.model_rebuild()

