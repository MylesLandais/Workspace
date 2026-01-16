"""Feed system - Clean architecture implementation.

This package provides a clean architecture for managing social media feed data
with caching, offline support, and multiple platform integrations.
"""

__version__ = "1.0.0"

from .di import DIContainer
from .repositories import CachedPostRepository
from .services.post_service import PostService
from .offline import OfflineStorage

__all__ = [
    'DIContainer',
    'CachedPostRepository',
    'PostService',
    'OfflineStorage'
]
