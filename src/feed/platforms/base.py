"""Abstract base class for platform adapters."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..models.post import Post
from ..models.subreddit import Subreddit


class PlatformAdapter(ABC):
    """Abstract base class for social media platform adapters."""

    @abstractmethod
    def fetch_posts(
        self,
        source: str,
        sort: str = "new",
        limit: int = 100,
        after: Optional[str] = None,
    ) -> tuple[List[Post], Optional[str]]:
        """
        Fetch posts from a source (e.g., subreddit).
        
        Args:
            source: Source identifier (e.g., subreddit name)
            sort: Sort order (e.g., "new", "hot", "top")
            limit: Maximum number of posts to fetch
            after: Pagination token for next page
        
        Returns:
            Tuple of (list of posts, next page token or None)
        """
        pass

    @abstractmethod
    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch metadata about a source (e.g., subreddit info).
        
        Args:
            source: Source identifier
        
        Returns:
            Source metadata or None if not found
        """
        pass








