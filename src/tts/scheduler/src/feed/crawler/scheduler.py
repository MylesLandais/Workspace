"""Adaptive decay scheduler for web crawling intervals."""

from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

from ..storage.neo4j_connection import Neo4jConnection
from .temporal import TemporalVersionManager


class DecayInterval(Enum):
    """Predefined decay intervals in the exponential backoff sequence."""
    HOUR_1 = 0.042  # 1 hour in days
    HOUR_4 = 0.167  # 4 hours
    HOUR_8 = 0.333  # 8 hours
    HOUR_12 = 0.5   # 12 hours
    DAY_1 = 1.0
    DAY_2 = 2.0
    DAY_3 = 3.0
    DAY_5 = 5.0
    DAY_7 = 7.0
    DAY_14 = 14.0
    DAY_31 = 31.0
    DAY_90 = 90.0
    YEAR_1 = 365.0
    YEAR_2 = 730.0
    YEAR_3 = 1095.0
    YEAR_5 = 1825.0
    YEAR_7 = 2555.0  # Max interval


# Ordered sequence of intervals for exponential backoff
INTERVAL_SEQUENCE = [
    DecayInterval.HOUR_1.value,
    DecayInterval.HOUR_4.value,
    DecayInterval.HOUR_8.value,
    DecayInterval.HOUR_12.value,
    DecayInterval.DAY_1.value,
    DecayInterval.DAY_2.value,
    DecayInterval.DAY_3.value,
    DecayInterval.DAY_5.value,
    DecayInterval.DAY_7.value,
    DecayInterval.DAY_14.value,
    DecayInterval.DAY_31.value,
    DecayInterval.DAY_90.value,
    DecayInterval.YEAR_1.value,
    DecayInterval.YEAR_2.value,
    DecayInterval.YEAR_3.value,
    DecayInterval.YEAR_5.value,
    DecayInterval.YEAR_7.value,
]


class AdaptiveScheduler:
    """Manages adaptive decay scheduling for web page re-crawling."""
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        decay_factor: float = 1.5,
        max_interval_days: float = DecayInterval.YEAR_7.value,
        use_temporal_history: bool = True,
    ):
        """
        Initialize adaptive scheduler.
        
        Args:
            neo4j: Neo4j connection instance
            decay_factor: Multiplier for interval when no change detected (1.5-2.0)
            max_interval_days: Maximum interval in days
            use_temporal_history: Whether to use temporal version history for optimization
        """
        self.neo4j = neo4j
        self.decay_factor = decay_factor
        self.max_interval_days = max_interval_days
        self.use_temporal_history = use_temporal_history
        if use_temporal_history:
            self.temporal_manager = TemporalVersionManager(neo4j)
        else:
            self.temporal_manager = None
    
    def get_next_interval(self, current_interval: Optional[float], changed: bool) -> float:
        """
        Calculate next crawl interval based on change detection.
        
        Args:
            current_interval: Current interval in days (None for first crawl)
            changed: Whether content changed in last crawl
            
        Returns:
            Next interval in days
        """
        if changed:
            # Reset to initial interval if content changed
            return DecayInterval.HOUR_1.value
        
        if current_interval is None:
            # First crawl, start with 1 hour
            return DecayInterval.HOUR_1.value
        
        # Find next interval in sequence
        next_interval = self._find_next_in_sequence(current_interval)
        
        # Apply decay factor for smoother transitions
        decayed = current_interval * self.decay_factor
        
        # Use the larger of sequence-based or decay-based interval
        next_interval = max(next_interval, decayed)
        
        # Cap at maximum
        return min(next_interval, self.max_interval_days)
    
    def _find_next_in_sequence(self, current_interval: float) -> float:
        """
        Find next interval in predefined sequence.
        
        Args:
            current_interval: Current interval in days
            
        Returns:
            Next interval from sequence
        """
        for interval in INTERVAL_SEQUENCE:
            if interval > current_interval:
                return interval
        
        # If current is >= max, return max
        return INTERVAL_SEQUENCE[-1]
    
    def schedule_next_crawl(
        self,
        url: str,
        changed: bool,
        current_interval: Optional[float] = None
    ) -> datetime:
        """
        Schedule next crawl time for a URL.
        
        Args:
            url: Normalized URL
            changed: Whether content changed
            current_interval: Current interval in days (fetched from DB if None)
            
        Returns:
            Next crawl datetime
        """
        if current_interval is None:
            # Fetch current interval from database
            query = """
            MATCH (w:WebPage {normalized_url: $url})
            RETURN w.crawl_interval_days as interval
            LIMIT 1
            """
            result = self.neo4j.execute_read(query, parameters={"url": url})
            if result:
                current_interval = result[0].get("interval")
        
        next_interval = self.get_next_interval(current_interval, changed)
        next_crawl = datetime.utcnow() + timedelta(days=next_interval)
        
        # Update database
        self.update_schedule(url, next_crawl, next_interval, changed)
        
        return next_crawl
    
    def update_schedule(
        self,
        url: str,
        next_crawl: datetime,
        interval_days: float,
        changed: bool
    ) -> None:
        """
        Update crawl schedule in database.
        
        Args:
            url: Normalized URL
            next_crawl: Next crawl datetime
            interval_days: Interval in days
            changed: Whether content changed
        """
        query = """
        MATCH (w:WebPage {normalized_url: $url})
        SET w.next_crawl_at = datetime({epochSeconds: $next_crawl_epoch}),
            w.crawl_interval_days = $interval_days,
            w.updated_at = datetime()
        """
        
        if changed:
            query += """
            SET w.change_count = COALESCE(w.change_count, 0) + 1,
                w.no_change_count = 0
            """
        else:
            query += """
            SET w.no_change_count = COALESCE(w.no_change_count, 0) + 1
            """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "url": url,
                "next_crawl_epoch": int(next_crawl.timestamp()),
                "interval_days": interval_days,
            }
        )
    
    def get_pages_due_for_crawl(self, limit: int = 100) -> list:
        """
        Get pages that are due for crawling.
        
        Args:
            limit: Maximum number of pages to return
            
        Returns:
            List of page records
        """
        query = """
        MATCH (w:WebPage)
        WHERE w.next_crawl_at IS NOT NULL 
        AND w.next_crawl_at <= datetime()
        AND w.robots_allowed = true
        RETURN w.normalized_url as url,
               w.crawl_interval_days as interval,
               w.last_crawled_at as last_crawled
        ORDER BY w.next_crawl_at ASC
        LIMIT $limit
        """
        
        return self.neo4j.execute_read(query, parameters={"limit": limit})
    
    def calculate_utility(self, url: str, freshness_weight: float = 1.0) -> float:
        """
        Calculate utility score for re-crawling a page.
        
        Utility = freshness_gain / crawl_cost
        
        Args:
            url: Normalized URL
            freshness_weight: Weight for freshness component
            
        Returns:
            Utility score (higher = more valuable to crawl)
        """
        query = """
        MATCH (w:WebPage {normalized_url: $url})
        RETURN w.last_crawled_at as last_crawled,
               w.next_crawl_at as next_crawl,
               w.change_count as change_count,
               w.no_change_count as no_change_count,
               w.crawl_interval_days as interval
        LIMIT 1
        """
        
        result = self.neo4j.execute_read(query, parameters={"url": url})
        if not result:
            return 0.0
        
        record = result[0]
        last_crawled = record.get("last_crawled")
        change_count = record.get("change_count", 0)
        no_change_count = record.get("no_change_count", 0)
        interval = record.get("interval", 1.0)
        
        if not last_crawled:
            return 1.0  # Never crawled, high utility
        
        # Calculate staleness (time since last crawl)
        now = datetime.utcnow()
        if isinstance(last_crawled, datetime):
            staleness_days = (now - last_crawled).total_seconds() / 86400
        else:
            staleness_days = interval
        
        # Freshness gain increases with staleness
        freshness_gain = staleness_days * freshness_weight
        
        # Crawl cost increases with interval (less frequent = more expensive to change)
        crawl_cost = 1.0 + (interval * 0.1)
        
        # Change frequency factor (pages that change often are more valuable)
        change_rate = change_count / max(change_count + no_change_count, 1)
        change_factor = 1.0 + change_rate
        
        utility = (freshness_gain * change_factor) / crawl_cost
        
        return utility
    
    def calculate_change_rate(self, url: str, days: int = 30) -> float:
        """
        Calculate change rate using temporal version history.
        
        Args:
            url: Normalized URL
            days: Number of days to analyze
            
        Returns:
            Change rate (changes per day)
        """
        if not self.use_temporal_history or not self.temporal_manager:
            # Fallback to basic calculation
            return 0.0
        
        change_count = self.temporal_manager.get_change_frequency(url, days)
        return change_count / days if days > 0 else 0.0
    
    def predict_next_change(self, url: str) -> Optional[datetime]:
        """
        Predict next change time based on historical patterns.
        
        Args:
            url: Normalized URL
            
        Returns:
            Predicted datetime of next change, or None if insufficient data
        """
        if not self.use_temporal_history or not self.temporal_manager:
            return None
        
        stats = self.temporal_manager.get_version_statistics(url)
        
        if stats["change_count"] < 3:
            # Need at least 3 changes to make a prediction
            return None
        
        # Simple prediction: average time between changes
        if stats["first_version_at"] and stats["last_version_at"]:
            try:
                if isinstance(stats["first_version_at"], str):
                    from dateutil import parser
                    first = parser.parse(stats["first_version_at"])
                    last = parser.parse(stats["last_version_at"])
                else:
                    first = stats["first_version_at"]
                    last = stats["last_version_at"]
                
                total_days = (last - first).total_seconds() / 86400
                if total_days > 0 and stats["change_count"] > 1:
                    avg_days_between = total_days / (stats["change_count"] - 1)
                    next_change = last + timedelta(days=avg_days_between)
                    return next_change
            except Exception:
                pass
        
        return None
    
    def get_optimal_interval_from_history(self, url: str) -> Optional[float]:
        """
        Calculate optimal interval based on version history.
        
        Args:
            url: Normalized URL
            
        Returns:
            Optimal interval in days, or None if insufficient data
        """
        if not self.use_temporal_history or not self.temporal_manager:
            return None
        
        # Get change rate
        change_rate = self.calculate_change_rate(url, days=90)
        
        if change_rate == 0:
            # No changes in 90 days, use maximum interval
            return self.max_interval_days
        
        # Calculate optimal interval: aim to catch changes within 2-3 intervals
        # If change_rate is 0.1 changes/day, we want to check every 10-15 days
        optimal_interval = 2.0 / change_rate if change_rate > 0 else self.max_interval_days
        
        # Clamp to valid range
        optimal_interval = max(DecayInterval.HOUR_1.value, min(optimal_interval, self.max_interval_days))
        
        return optimal_interval

