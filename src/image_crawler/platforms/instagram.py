"""Instagram platform crawler."""

from typing import List, Dict
from .base import BasePlatformCrawler


class InstagramCrawler(BasePlatformCrawler):
    """Crawler for Instagram profiles."""

    def __init__(
        self,
        handle: str,
        check_interval: int = 3600,
    ):
        """
        Initialize Instagram crawler.

        Args:
            handle: Instagram handle (without @)
            check_interval: Check interval in seconds
        """
        super().__init__(check_interval)
        self.handle = handle.replace("@", "")

    def fetch_image_urls(self, limit: int = 50) -> List[str]:
        """
        Fetch image URLs from Instagram profile.

        Args:
            limit: Maximum number of URLs to fetch

        Returns:
            List of image URLs
        """
        raise NotImplementedError(
            "Instagram crawler requires instaloader or official API. "
            "Install with: pip install instaloader"
        )

    def get_source_metadata(self) -> Dict:
        """
        Get Instagram profile metadata.

        Returns:
            Dictionary with profile metadata
        """
        return {
            "type": "instagram",
            "handle": self.handle,
        }








