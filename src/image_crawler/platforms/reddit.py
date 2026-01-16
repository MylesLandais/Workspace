"""Reddit platform crawler."""

from typing import List, Dict, Optional
from .base import BasePlatformCrawler

try:
    from ..feed.platforms.reddit import RedditAdapter
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False
    RedditAdapter = None


class RedditCrawler(BasePlatformCrawler):
    """Crawler for Reddit subreddits."""

    def __init__(
        self,
        subreddit: str,
        check_interval: int = 1800,
        mock: bool = False,
    ):
        """
        Initialize Reddit crawler.

        Args:
            subreddit: Subreddit name (with or without r/ prefix)
            check_interval: Check interval in seconds
            mock: Use mock mode (no real API calls)
        """
        super().__init__(check_interval)
        if not REDDIT_AVAILABLE:
            raise ImportError("Reddit adapter not available")

        self.subreddit = subreddit.replace("r/", "").replace("/r/", "")
        self.adapter = RedditAdapter(mock=mock, delay_min=1.0, delay_max=2.0)

    def fetch_image_urls(self, limit: int = 50) -> List[str]:
        """
        Fetch image URLs from Reddit subreddit.

        Args:
            limit: Maximum number of URLs to fetch

        Returns:
            List of image URLs
        """
        posts, _ = self.adapter.fetch_posts(
            source=self.subreddit,
            sort="new",
            limit=limit,
        )

        image_urls = []
        for post in posts:
            if post.url and self._is_image_url(post.url):
                image_urls.append(post.url)

        self.mark_checked()
        return image_urls

    def _is_image_url(self, url: str) -> bool:
        """
        Check if URL is an image.

        Args:
            url: URL to check

        Returns:
            True if image URL
        """
        if not url:
            return False

        url_lower = url.lower()
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"]

        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True

        if "i.redd.it" in url_lower or "preview.redd.it" in url_lower:
            return True

        return False

    def get_source_metadata(self) -> Dict:
        """
        Get subreddit metadata.

        Returns:
            Dictionary with subreddit metadata
        """
        metadata = self.adapter.fetch_source_metadata(self.subreddit)
        if metadata:
            return {
                "type": "reddit",
                "name": metadata.name,
                "subscribers": metadata.subscribers,
                "description": metadata.description,
            }
        return {
            "type": "reddit",
            "name": self.subreddit,
        }








