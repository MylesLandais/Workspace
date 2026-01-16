"""Handle model for platform-specific accounts."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from ..ontology.schema import HandleStatus, VerificationConfidence


class Handle(BaseModel):
    """Represents a platform-specific account handle."""

    uuid: UUID = Field(default_factory=uuid4, description="Unique identifier (UUID)")
    username: str = Field(..., description="Platform-specific username (e.g., '@sjokz')")
    display_name: Optional[str] = Field(default=None, description="Display name on platform")
    profile_url: str = Field(..., description="Full URL to profile")
    follower_count: Optional[int] = Field(default=None, description="Follower/subscriber count")
    verified_by_platform: bool = Field(default=False, description="Platform's verification badge")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Relationship properties (for OWNS_HANDLE edge)
    status: Optional[HandleStatus] = Field(default=None, description="Handle status")
    verified: Optional[bool] = Field(default=None, description="Whether handle is verified")
    confidence: Optional[VerificationConfidence] = Field(default=None, description="Verification confidence")
    discovered_at: Optional[datetime] = Field(default=None, description="When handle was discovered")
    verified_at: Optional[datetime] = Field(default=None, description="When verification occurred")

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
            "username": self.username,
            "display_name": self.display_name,
            "profile_url": self.profile_url,
            "follower_count": self.follower_count,
            "verified_by_platform": self.verified_by_platform,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_owns_handle_edge_dict(self) -> dict:
        """Convert to dictionary suitable for OWNS_HANDLE relationship properties."""
        return {
            "status": self.status.value if self.status else HandleStatus.UNVERIFIED.value,
            "verified": self.verified if self.verified is not None else False,
            "confidence": self.confidence.value if self.confidence else VerificationConfidence.MEDIUM.value,
            "discovered_at": self.discovered_at or datetime.utcnow(),
            "verified_at": self.verified_at,
            "created_at": datetime.utcnow(),
        }








