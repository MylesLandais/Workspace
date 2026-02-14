"""Repository interfaces for data access layer."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from feed.models.post import Post


class PostRepository(ABC):
    """Abstract repository for post data access."""
    
    @abstractmethod
    async def get_post(self, post_id: str) -> Optional[Post]:
        """Get a single post by ID."""
        pass
    
    @abstractmethod
    async def get_posts_by_subreddit(
        self,
        subreddit: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Get posts by subreddit with pagination."""
        pass
    
    @abstractmethod
    async def get_posts_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Get posts by user with pagination."""
        pass
    
    @abstractmethod
    async def save_post(self, post: Post) -> None:
        """Save or update a post."""
        pass
    
    @abstractmethod
    async def save_posts(self, posts: List[Post]) -> None:
        """Save or update multiple posts."""
        pass
    
    @abstractmethod
    async def delete_post(self, post_id: str) -> None:
        """Delete a post."""
        pass


class MediaRepository(ABC):
    """Abstract repository for media data access."""
    
    @abstractmethod
    async def get_media(self, media_id: str) -> Optional[dict]:
        """Get media metadata by ID."""
        pass
    
    @abstractmethod
    async def get_media_by_post(
        self,
        post_id: str,
        media_type: Optional[str] = None
    ) -> List[dict]:
        """Get all media for a post, optionally filtered by type."""
        pass
    
    @abstractmethod
    async def save_media(self, media: dict) -> None:
        """Save or update media metadata."""
        pass
    
    @abstractmethod
    async def delete_media(self, media_id: str) -> None:
        """Delete media metadata."""
        pass
