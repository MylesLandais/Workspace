"""Core interfaces for the feed system."""

from .repository import PostRepository, MediaRepository
from .adapter import PlatformAdapter

__all__ = [
    'PostRepository',
    'MediaRepository',
    'PlatformAdapter'
]
