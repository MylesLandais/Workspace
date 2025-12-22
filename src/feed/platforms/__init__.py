"""Platform adapters for feed engine."""

from .base import PlatformAdapter
from .reddit import RedditAdapter

__all__ = ["PlatformAdapter", "RedditAdapter"]

