"""Subreddit statistics service for tracking post counts by time period."""

import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import requests

from ..storage.neo4j_connection import Neo4jConnection


class SubredditStatsService:
    """Service for fetching and storing subreddit post count statistics."""

    def __init__(
        self,
        neo4j: Optional[Neo4jConnection] = None,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
    ):
        """
        Initialize subreddit stats service.
        
        Args:
            neo4j: Neo4j connection for storing statistics
            user_agent: Custom User-Agent string (required by Reddit)
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
        """
        self.neo4j = neo4j
        self.user_agent = (
            user_agent
            or os.getenv("FEED_USER_AGENT", "feed/1.0 (by /u/feeduser)")
        )
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headers = {"User-Agent": self.user_agent}

    def _delay(self) -> None:
        """Add human-like delay between requests."""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def get_post_count_by_range(
        self,
        subreddit: str,
        after: datetime,
        before: datetime,
    ) -> Optional[int]:
        """
        Get post count for a subreddit within a time range using Reddit API.
        
        This uses a Pushshift-style pattern: query with after/before timestamps
        and count results. Since Reddit's API doesn't directly return counts,
        we paginate through results to estimate the count.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            after: Start timestamp (inclusive)
            before: End timestamp (exclusive)
        
        Returns:
            Estimated post count for the range, or None if error
        """
        subreddit = subreddit.replace("r/", "").replace("/r/", "")
        after_ts = int(after.timestamp())
        before_ts = int(before.timestamp())
        
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        total_count = 0
        after_token = None
        
        try:
            # Paginate through results to count posts in range
            while True:
                params = {
                    "limit": 100,  # Max per page
                    "sort": "new",
                }
                if after_token:
                    params["after"] = after_token
                
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                children = data.get("data", {}).get("children", [])
                if not children:
                    break
                
                # Count posts within our time range
                page_count = 0
                for child in children:
                    post_data = child.get("data", {})
                    created_utc = post_data.get("created_utc", 0)
                    
                    # If post is before our range, we've gone too far back
                    if created_utc < after_ts:
                        return total_count
                    
                    # If post is within range, count it
                    if after_ts <= created_utc < before_ts:
                        page_count += 1
                    # If post is after our range, we're done
                    elif created_utc >= before_ts:
                        return total_count
                
                total_count += page_count
                
                # Check if we should continue
                next_after = data.get("data", {}).get("after")
                if not next_after:
                    break
                
                # If we got fewer posts than limit, we're at the end
                if len(children) < 100:
                    break
                
                after_token = next_after
                self._delay()
            
            self._delay()
            return total_count
            
        except requests.RequestException as e:
            print(f"Error fetching post count for r/{subreddit}: {e}")
            return None

    def get_monthly_post_count(
        self,
        subreddit: str,
        year: int,
        month: int,
    ) -> Optional[int]:
        """
        Get post count for a specific month.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            year: Year (e.g., 2024)
            month: Month (1-12)
        
        Returns:
            Post count for the month, or None if error
        """
        # Calculate month boundaries
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        return self.get_post_count_by_range(subreddit, start, end)

    def get_yearly_post_count(
        self,
        subreddit: str,
        year: int,
    ) -> Optional[int]:
        """
        Get post count for a specific year.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            year: Year (e.g., 2024)
        
        Returns:
            Post count for the year, or None if error
        """
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        return self.get_post_count_by_range(subreddit, start, end)

    def get_rolling_monthly_counts(
        self,
        subreddit: str,
        months: int = 12,
    ) -> Dict[str, int]:
        """
        Get rolling monthly post counts for the last N months.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to fetch (default 12)
        
        Returns:
            Dictionary mapping "YYYY-MM" to post count
        """
        counts = {}
        today = datetime.utcnow()
        
        for i in range(months):
            # Calculate month N months ago
            target_date = today - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            count = self.get_monthly_post_count(subreddit, year, month)
            if count is not None:
                key = f"{year}-{month:02d}"
                counts[key] = count
            
            # Add delay between months
            if i < months - 1:
                self._delay()
        
        return counts

    def store_subreddit_stats(
        self,
        subreddit: str,
        stats: Dict[str, any],
    ) -> bool:
        """
        Store subreddit statistics in Neo4j.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            stats: Dictionary with statistics (e.g., monthly_counts, yearly_counts)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.neo4j:
            return False
        
        subreddit = subreddit.replace("r/", "").replace("/r/", "")
        
        # Update Subreddit node with statistics
        query = """
        MATCH (s:Subreddit {name: $subreddit})
        SET s.stats = $stats,
            s.stats_updated_at = datetime()
        RETURN s.name as name
        """
        
        try:
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "subreddit": subreddit,
                    "stats": stats,
                }
            )
            return bool(result)
        except Exception as e:
            print(f"Error storing stats for r/{subreddit}: {e}")
            return False

    def get_subreddit_stats(
        self,
        subreddit: str,
    ) -> Optional[Dict[str, any]]:
        """
        Get stored subreddit statistics from Neo4j.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
        
        Returns:
            Statistics dictionary or None if not found
        """
        if not self.neo4j:
            return None
        
        subreddit = subreddit.replace("r/", "").replace("/r/", "")
        
        query = """
        MATCH (s:Subreddit {name: $subreddit})
        RETURN s.stats as stats, s.stats_updated_at as updated_at
        LIMIT 1
        """
        
        try:
            result = self.neo4j.execute_read(
                query,
                parameters={"subreddit": subreddit}
            )
            if result:
                record = result[0]
                return {
                    "stats": record.get("stats"),
                    "updated_at": record.get("updated_at"),
                }
            return None
        except Exception as e:
            print(f"Error fetching stats for r/{subreddit}: {e}")
            return None

    def estimate_all_time_posts(
        self,
        subreddit: str,
        start_year: int = 2005,
    ) -> Optional[int]:
        """
        Estimate all-time post count by querying from start_year to now.
        
        Note: This is an approximation. Reddit doesn't expose native all-time counts.
        For more complete coverage, consider using public Reddit datasets (BigQuery).
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            start_year: Year to start counting from (default 2005, Reddit's founding)
        
        Returns:
            Estimated all-time post count, or None if error
        """
        start = datetime(start_year, 1, 1)
        end = datetime.utcnow()
        return self.get_post_count_by_range(subreddit, start, end)

    def calculate_post_velocity(
        self,
        subreddit: str,
        months: int = 3,
    ) -> Optional[float]:
        """
        Calculate average posts per day over the last N months.
        
        This helps determine crawler policy: high-velocity subreddits need
        more frequent crawling, low-velocity subreddits can be crawled less often.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            months: Number of months to analyze (default 3)
        
        Returns:
            Average posts per day, or None if error
        """
        counts = self.get_rolling_monthly_counts(subreddit, months=months)
        if not counts:
            return None
        
        total_posts = sum(counts.values())
        total_days = months * 30  # Approximate
        
        return total_posts / total_days if total_days > 0 else None

