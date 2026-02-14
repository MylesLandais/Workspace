"""Post model for social media posts."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Post(BaseModel):
    """Represents a social media post."""

    id: str = Field(..., description="Unique post identifier")
    title: str = Field(..., description="Post title")
    created_utc: datetime = Field(..., description="Creation timestamp (UTC)")
    score: int = Field(default=0, description="Upvote score")
    num_comments: int = Field(default=0, description="Number of comments")
    upvote_ratio: float = Field(default=0.0, description="Upvote ratio (0.0-1.0)")
    over_18: bool = Field(default=False, description="NSFW flag")
    url: str = Field(..., description="Post URL")
    selftext: str = Field(default="", description="Post body text (for self-posts)")
    author: Optional[str] = Field(default=None, description="Post author username")
    subreddit: str = Field(..., description="Subreddit name")
    permalink: Optional[str] = Field(default=None, description="Reddit permalink")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }








