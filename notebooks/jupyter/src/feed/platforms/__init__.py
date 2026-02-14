"""Platform adapters for feed engine."""

from .base import PlatformAdapter
from .reddit import RedditAdapter
from .fourchan import ImageboardAdapter
from .depop import DepopAdapter
from .fapello import FapelloAdapter
from .blog import BlogAdapter
from .listal import ListalAdapter
from .tumblr import TumblrAdapter

__all__ = ["PlatformAdapter", "RedditAdapter", "ImageboardAdapter", "DepopAdapter", "FapelloAdapter", "BlogAdapter", "ListalAdapter", "TumblrAdapter"]


