from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, List

class DataSource(ABC):
    """Abstract base class for data sources (e.g., Reddit, Twitter)."""

    @abstractmethod
    def fetch_feed(self, target_name: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """
        Fetches a feed of items from the source.
        
        Args:
            target_name: The name of the target (e.g., subreddit name, username).
            limit: Maximum number of items to fetch.
            
        Yields:
            Raw data dictionaries for each item found.
        """
        pass

class ObjectStore(ABC):
    """Abstract base class for object storage (e.g., MinIO, S3)."""

    @abstractmethod
    def save_raw(self, data: Dict[str, Any], path: str) -> str:
        """
        Saves raw data to the object store.
        
        Args:
            data: The dictionary to save (will be serialized to JSON).
            path: The logical path/key for the file.
            
        Returns:
            The full path/key where the object was stored.
        """
        pass
