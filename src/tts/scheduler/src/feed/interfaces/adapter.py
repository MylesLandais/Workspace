"""Adapter interfaces for platform integration."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class PlatformAdapter(ABC):
    """Abstract adapter for social media platforms."""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier (e.g., 'reddit', 'youtube')."""
        pass
    
    @abstractmethod
    async def fetch_posts(
        self,
        source: str,
        limit: int = 100,
        sort: str = 'new',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a source.
        
        Args:
            source: Source identifier (e.g., subreddit, channel ID)
            limit: Maximum number of posts to fetch
            sort: Sort order (new, hot, top, etc.)
            **kwargs: Platform-specific parameters
            
        Returns:
            List of post data dictionaries
        """
        pass
    
    @abstractmethod
    async def fetch_media(self, media_url: str) -> Optional[bytes]:
        """Fetch media content from URL."""
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict[str, int]:
        """
        Get rate limit configuration.
        
        Returns:
            Dict with rate limit keys:
            - requests_per_minute
            - requests_per_second
            - concurrent_requests
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Check if API credentials are valid."""
        pass
    
    @abstractmethod
    def get_post_url(self, post_data: Dict[str, Any]) -> str:
        """Extract or construct post URL."""
        pass
