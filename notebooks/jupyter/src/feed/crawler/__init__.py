"""Web crawler components for adaptive decay scheduling and URL tracking."""

from .frontier import URLFrontier
from .scheduler import AdaptiveScheduler
from .deduplication import DuplicateDetector
from .content import ContentAnalyzer
from .robots import RobotsParser
from .temporal import TemporalVersionManager
from .temporal_queries import TemporalQueries
from .temporal_analytics import TemporalAnalytics

# Try to import reddit_crawler (may not be available if dependencies missing)
try:
    from .reddit_crawler import RedditCrawler, CrawlerConfig
    __all__ = [
        "URLFrontier",
        "AdaptiveScheduler",
        "DuplicateDetector",
        "ContentAnalyzer",
        "RobotsParser",
        "TemporalVersionManager",
        "TemporalQueries",
        "TemporalAnalytics",
        "RedditCrawler",
        "CrawlerConfig",
    ]
except ImportError:
    __all__ = [
        "URLFrontier",
        "AdaptiveScheduler",
        "DuplicateDetector",
        "ContentAnalyzer",
        "RobotsParser",
        "TemporalVersionManager",
        "TemporalQueries",
        "TemporalAnalytics",
    ]

