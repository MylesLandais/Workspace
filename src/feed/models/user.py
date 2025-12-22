"""User model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """Represents a social media user."""

    username: str = Field(..., description="Username")
    created_utc: Optional[datetime] = Field(default=None, description="Account creation timestamp")
    karma: Optional[int] = Field(default=None, description="Total karma")
    link_karma: Optional[int] = Field(default=None, description="Link karma")
    comment_karma: Optional[int] = Field(default=None, description="Comment karma")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }

