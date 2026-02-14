"""Base platform crawler interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class BasePlatformCrawler(ABC):
    """Base class for platform-specific crawlers."""

    def __init__(self, check_interval: int = 3600):
        """
        Initialize platform crawler.

        Args:
            check_interval: Check interval in seconds
        """
        self.check_interval = check_interval
        self.last_check: Optional[datetime] = None

    @abstractmethod
    def fetch_image_urls(self, limit: int = 50) -> List[str]:
        """
        Fetch image URLs from platform.

        Args:
            limit: Maximum number of URLs to fetch

        Returns:
            List of image URLs
        """
        pass

    @abstractmethod
    def get_source_metadata(self) -> Dict:
        """
        Get source metadata.

        Returns:
            Dictionary with source metadata
        """
        pass

    def should_check(self) -> bool:
        """
        Check if it's time to check for new images.

        Returns:
            True if should check
        """
        if self.last_check is None:
            return True

        from datetime import timedelta
        return datetime.utcnow() - self.last_check > timedelta(seconds=self.check_interval)

    def mark_checked(self) -> None:
        """Mark that check was performed."""
        self.last_check = datetime.utcnow()

