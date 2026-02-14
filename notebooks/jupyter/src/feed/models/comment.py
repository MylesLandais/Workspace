"""Comment model for Reddit comments."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Comment(BaseModel):
    """Represents a Reddit comment."""

    id: str = Field(..., description="Unique comment identifier")
    body: str = Field(default="", description="Comment body text")
    author: Optional[str] = Field(default=None, description="Comment author username")
    created_utc: datetime = Field(..., description="Creation timestamp (UTC)")
    score: int = Field(default=0, description="Upvote score")
    ups: int = Field(default=0, description="Upvotes")
    downs: int = Field(default=0, description="Downvotes")
    parent_id: Optional[str] = Field(default=None, description="Parent comment/post ID (t1_ for comment, t3_ for post)")
    link_id: str = Field(..., description="Associated post ID (t3_ format)")
    depth: int = Field(default=0, description="Comment nesting depth")
    is_submitter: bool = Field(default=False, description="Whether comment author is the post submitter (OP)")
    permalink: Optional[str] = Field(default=None, description="Comment permalink")
    
    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }







