"""Subreddit model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Subreddit(BaseModel):
    """Represents a subreddit."""

    name: str = Field(..., description="Subreddit name (without r/ prefix)")
    subscribers: Optional[int] = Field(default=None, description="Subscriber count")
    created_utc: Optional[datetime] = Field(default=None, description="Creation timestamp")
    description: Optional[str] = Field(default=None, description="Subreddit description")
    public_description: Optional[str] = Field(
        default=None, description="Public description"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }

