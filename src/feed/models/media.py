"""Media model for cross-platform content normalization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from ..ontology.schema import MediaType


class Media(BaseModel):
    """Base media model for cross-platform content normalization."""

    uuid: UUID = Field(default_factory=uuid4, description="Unique identifier (UUID)")
    title: Optional[str] = Field(default=None, description="Media title")
    source_url: str = Field(..., description="Original content URL")
    publish_date: datetime = Field(..., description="Publication timestamp")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail image URL")
    media_type: MediaType = Field(..., description="Type of media content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Platform attribution
    platform_name: Optional[str] = Field(default=None, description="Platform name (for GraphQL)")
    platform_slug: Optional[str] = Field(default=None, description="Platform slug (for GraphQL)")
    platform_icon_url: Optional[str] = Field(default=None, description="Platform icon URL (for GraphQL)")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary suitable for Neo4j node creation."""
        base_dict = {
            "uuid": str(self.uuid),
            "title": self.title,
            "source_url": self.source_url,
            "publish_date": self.publish_date,
            "thumbnail_url": self.thumbnail_url,
            "media_type": self.media_type.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return base_dict


class VideoMedia(Media):
    """Video media with additional properties."""

    duration: Optional[int] = Field(default=None, description="Duration in seconds")
    view_count: Optional[int] = Field(default=None, description="View count")
    aspect_ratio: Optional[str] = Field(default=None, description="Aspect ratio (e.g., '16:9', '9:16')")
    resolution: Optional[str] = Field(default=None, description="Resolution (e.g., '1080p')")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary with video-specific properties."""
        base_dict = super().to_neo4j_dict()
        base_dict.update({
            "duration": self.duration,
            "view_count": self.view_count,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
        })
        return base_dict


class ImageMedia(Media):
    """Image media with additional properties."""

    width: Optional[int] = Field(default=None, description="Width in pixels")
    height: Optional[int] = Field(default=None, description="Height in pixels")
    aspect_ratio: Optional[str] = Field(default=None, description="Aspect ratio (e.g., '1:1', '4:3')")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary with image-specific properties."""
        base_dict = super().to_neo4j_dict()
        base_dict.update({
            "width": self.width,
            "height": self.height,
            "aspect_ratio": self.aspect_ratio,
        })
        return base_dict


class TextMedia(Media):
    """Text media with additional properties."""

    body_content: str = Field(..., description="Full text content")
    word_count: Optional[int] = Field(default=None, description="Word count")

    def to_neo4j_dict(self) -> dict:
        """Convert to dictionary with text-specific properties."""
        base_dict = super().to_neo4j_dict()
        base_dict.update({
            "body_content": self.body_content,
            "word_count": self.word_count,
        })
        return base_dict








