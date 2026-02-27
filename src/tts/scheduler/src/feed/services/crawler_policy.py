"""Crawler policy service that uses subreddit statistics to determine intelligent crawling schedules."""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..storage.neo4j_connection import Neo4jConnection
from .subreddit_stats import SubredditStatsService


class CrawlFrequency(Enum):
    """Crawl frequency levels based on post velocity."""
    VERY_HIGH = "very_high"  # > 50 posts/day: crawl every 1-2 hours
    HIGH = "high"  # 20-50 posts/day: crawl every 3-6 hours
    MEDIUM = "medium"  # 5-20 posts/day: crawl every 12-24 hours
    LOW = "low"  # 1-5 posts/day: crawl every 1-2 days
    VERY_LOW = "very_low"  # < 1 post/day: crawl every 3-7 days


class CrawlerPolicy:
    """Intelligent crawler policy based on subreddit statistics."""

    def __init__(
        self,
        neo4j: Neo4jConnection,
        stats_service: Optional[SubredditStatsService] = None,
    ):
        """
        Initialize crawler policy service.
        
        Args:
            neo4j: Neo4j connection
            stats_service: Optional subreddit stats service (creates one if not provided)
        """
        self.neo4j = neo4j
        self.stats_service = stats_service or SubredditStatsService(neo4j=neo4j)

    def get_crawl_frequency(
        self,
        subreddit: str,
        months: int = 3,
    ) -> CrawlFrequency:
        """
        Determine crawl frequency based on post velocity.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to analyze for velocity (default 3)
        
        Returns:
            CrawlFrequency enum value
        """
        velocity = self.stats_service.calculate_post_velocity(subreddit, months=months)
        
        if velocity is None:
            # If we can't determine velocity, default to medium
            return CrawlFrequency.MEDIUM
        
        if velocity >= 50:
            return CrawlFrequency.VERY_HIGH
        elif velocity >= 20:
            return CrawlFrequency.HIGH
        elif velocity >= 5:
            return CrawlFrequency.MEDIUM
        elif velocity >= 1:
            return CrawlFrequency.LOW
        else:
            return CrawlFrequency.VERY_LOW

    def get_crawl_delay_seconds(
        self,
        subreddit: str,
        months: int = 3,
    ) -> Tuple[float, float]:
        """
        Get recommended delay range (min, max) in seconds between crawls.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to analyze for velocity (default 3)
        
        Returns:
            Tuple of (min_delay_seconds, max_delay_seconds)
        """
        frequency = self.get_crawl_frequency(subreddit, months=months)
        
        # Convert frequency to delay ranges (in seconds)
        delay_ranges = {
            CrawlFrequency.VERY_HIGH: (3600, 7200),  # 1-2 hours
            CrawlFrequency.HIGH: (10800, 21600),  # 3-6 hours
            CrawlFrequency.MEDIUM: (43200, 86400),  # 12-24 hours
            CrawlFrequency.LOW: (86400, 172800),  # 1-2 days
            CrawlFrequency.VERY_LOW: (259200, 604800),  # 3-7 days
        }
        
        return delay_ranges.get(frequency, (43200, 86400))  # Default to medium

    def get_request_delay_seconds(
        self,
        subreddit: str,
        months: int = 3,
    ) -> Tuple[float, float]:
        """
        Get recommended delay range (min, max) in seconds between requests within a crawl.
        
        High-velocity subreddits can use shorter delays since we're crawling more frequently.
        Low-velocity subreddits should use longer delays to be respectful.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to analyze for velocity (default 3)
        
        Returns:
            Tuple of (min_delay_seconds, max_delay_seconds)
        """
        frequency = self.get_crawl_frequency(subreddit, months=months)
        
        # Higher frequency = shorter delays (we're crawling more often, so each crawl can be faster)
        # Lower frequency = longer delays (we're crawling less often, so be more respectful)
        delay_ranges = {
            CrawlFrequency.VERY_HIGH: (2.0, 5.0),  # Fast requests
            CrawlFrequency.HIGH: (3.0, 8.0),
            CrawlFrequency.MEDIUM: (5.0, 15.0),  # Standard
            CrawlFrequency.LOW: (10.0, 30.0),  # Slower, more respectful
            CrawlFrequency.VERY_LOW: (15.0, 45.0),  # Very slow
        }
        
        return delay_ranges.get(frequency, (5.0, 15.0))  # Default to medium

    def get_max_pages_per_crawl(
        self,
        subreddit: str,
        months: int = 3,
    ) -> int:
        """
        Get recommended maximum pages to fetch per crawl.
        
        High-velocity subreddits need more pages to catch up.
        Low-velocity subreddits need fewer pages.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to analyze for velocity (default 3)
        
        Returns:
            Maximum pages to fetch per crawl
        """
        frequency = self.get_crawl_frequency(subreddit, months=months)
        
        page_limits = {
            CrawlFrequency.VERY_HIGH: 5,  # Fetch more pages
            CrawlFrequency.HIGH: 3,
            CrawlFrequency.MEDIUM: 2,  # Standard
            CrawlFrequency.LOW: 1,  # Just check for new posts
            CrawlFrequency.VERY_LOW: 1,  # Minimal
        }
        
        return page_limits.get(frequency, 2)  # Default to medium

    def get_subreddit_policy(
        self,
        subreddit: str,
        months: int = 3,
    ) -> Dict[str, any]:
        """
        Get complete crawling policy for a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to analyze for velocity (default 3)
        
        Returns:
            Dictionary with policy recommendations
        """
        frequency = self.get_crawl_frequency(subreddit, months=months)
        crawl_delay = self.get_crawl_delay_seconds(subreddit, months=months)
        request_delay = self.get_request_delay_seconds(subreddit, months=months)
        max_pages = self.get_max_pages_per_crawl(subreddit, months=months)
        
        # Get velocity for context
        velocity = self.stats_service.calculate_post_velocity(subreddit, months=months)
        
        return {
            "subreddit": subreddit,
            "frequency": frequency.value,
            "post_velocity": velocity,  # posts per day
            "crawl_delay_seconds": {
                "min": crawl_delay[0],
                "max": crawl_delay[1],
            },
            "request_delay_seconds": {
                "min": request_delay[0],
                "max": request_delay[1],
            },
            "max_pages_per_crawl": max_pages,
            "recommended_schedule": self._get_schedule_description(frequency),
        }

    def _get_schedule_description(self, frequency: CrawlFrequency) -> str:
        """Get human-readable schedule description."""
        descriptions = {
            CrawlFrequency.VERY_HIGH: "Crawl every 1-2 hours, fetch up to 5 pages per crawl",
            CrawlFrequency.HIGH: "Crawl every 3-6 hours, fetch up to 3 pages per crawl",
            CrawlFrequency.MEDIUM: "Crawl every 12-24 hours, fetch up to 2 pages per crawl",
            CrawlFrequency.LOW: "Crawl every 1-2 days, fetch 1 page per crawl",
            CrawlFrequency.VERY_LOW: "Crawl every 3-7 days, fetch 1 page per crawl",
        }
        return descriptions.get(frequency, "Standard crawling schedule")

    def get_all_subreddit_policies(
        self,
        subreddits: List[str],
        months: int = 3,
    ) -> Dict[str, Dict[str, any]]:
        """
        Get crawling policies for multiple subreddits.
        
        Args:
            subreddits: List of subreddit names (without r/ prefix)
            months: Number of months to analyze for velocity (default 3)
        
        Returns:
            Dictionary mapping subreddit name to policy
        """
        policies = {}
        for subreddit in subreddits:
            try:
                policies[subreddit] = self.get_subreddit_policy(subreddit, months=months)
            except Exception as e:
                print(f"Error getting policy for r/{subreddit}: {e}")
                # Use default policy
                policies[subreddit] = {
                    "subreddit": subreddit,
                    "frequency": CrawlFrequency.MEDIUM.value,
                    "post_velocity": None,
                    "crawl_delay_seconds": {"min": 43200, "max": 86400},
                    "request_delay_seconds": {"min": 5.0, "max": 15.0},
                    "max_pages_per_crawl": 2,
                    "recommended_schedule": "Standard crawling schedule",
                }
        return policies

    def store_policy(
        self,
        subreddit: str,
        policy: Dict[str, any],
    ) -> bool:
        """
        Store crawling policy in Neo4j for reference.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            policy: Policy dictionary from get_subreddit_policy()
        
        Returns:
            True if successful, False otherwise
        """
        subreddit = subreddit.replace("r/", "").replace("/r/", "")
        
        query = """
        MATCH (s:Subreddit {name: $subreddit})
        SET s.crawler_policy = $policy,
            s.policy_updated_at = datetime()
        RETURN s.name as name
        """
        
        try:
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "subreddit": subreddit,
                    "policy": policy,
                }
            )
            return bool(result)
        except Exception as e:
            print(f"Error storing policy for r/{subreddit}: {e}")
            return False






