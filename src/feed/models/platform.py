"""Platform model for social media platforms."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Platform(BaseModel):
    """Represents a social media platform."""

    name: str = Field(..., description="Platform name (e.g., 'YouTube', 'TikTok')")
    slug: str = Field(..., description="URL-friendly identifier (e.g., 'youtube')")
    api_base_url: Optional[str] = Field(default=None, description="API endpoint URL")
    icon_url: Optional[str] = Field(default=None, description="Platform icon URL")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        return {
            "name": self.name,
            "slug": self.slug,
            "api_base_url": self.api_base_url,
            "icon_url": self.icon_url,
            "created_at": self.created_at,
        }

