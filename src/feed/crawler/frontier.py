"""URL Frontier Manager for web crawling queue and URL normalization."""

import re
from typing import List, Optional, Set, Dict
from urllib.parse import urlparse, urlunparse, urljoin, parse_qs
from datetime import datetime, timedelta
from collections import defaultdict
import heapq

from ..storage.neo4j_connection import Neo4jConnection
from .temporal import TemporalVersionManager


class URLNormalizer:
    """Normalizes and canonicalizes URLs for duplicate detection."""

    @staticmethod
    def normalize(url: str) -> str:
        """
        Normalize a URL to canonical form.
        
        Args:
            url: Original URL string
            
        Returns:
            Normalized URL string
        """
        if not url:
            return ""
        
        # Parse URL
        parsed = urlparse(url.strip())
        
        # Normalize scheme (lowercase, default to http)
        scheme = parsed.scheme.lower() or "http"
        if scheme not in ["http", "https"]:
            return url  # Return as-is for non-HTTP URLs
        
        # Normalize netloc (lowercase, remove port if default)
        netloc = parsed.netloc.lower()
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]
        
        # Normalize path (remove trailing slash, decode)
        path = parsed.path.rstrip("/") or "/"
        
        # Remove default query params that don't affect content
        # Keep important params but sort them
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        # Remove common tracking params
        tracking_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", 
                          "utm_content", "fbclid", "gclid", "_ga", "ref"}
        filtered_params = {k: v for k, v in query_params.items() 
                          if k.lower() not in tracking_params}
        
        # Sort and reconstruct query
        if filtered_params:
            sorted_params = sorted(filtered_params.items())
            query = "&".join(f"{k}={v[0]}" if len(v) == 1 else f"{k}={','.join(sorted(v))}"
                            for k, v in sorted_params)
        else:
            query = ""
        
        # Reconstruct normalized URL
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, ""))
        return normalized
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL string
            
        Returns:
            Domain string (e.g., "example.com")
        """
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            # Remove port if present
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            return netloc
        except Exception:
            return ""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid for crawling.
        
        Args:
            url: URL string
            
        Returns:
            True if URL is valid
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            # Only HTTP/HTTPS
            if parsed.scheme not in ["http", "https"]:
                return False
            # Must have valid domain
            domain = URLNormalizer.extract_domain(url)
            if not domain or "." not in domain:
                return False
            return True
        except Exception:
            return False


class URLFrontier:
    """Manages URL queue with priority scheduling and domain-based rate limiting."""
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        max_urls_per_domain: int = 1000,
        default_crawl_delay: float = 1.0,
        use_temporal_prioritization: bool = True,
    ):
        """
        Initialize URL frontier.
        
        Args:
            neo4j: Neo4j connection instance
            max_urls_per_domain: Maximum URLs to queue per domain
            default_crawl_delay: Default delay between crawls (seconds)
            use_temporal_prioritization: Whether to use temporal history for prioritization
        """
        self.neo4j = neo4j
        self.max_urls_per_domain = max_urls_per_domain
        self.default_crawl_delay = default_crawl_delay
        self.normalizer = URLNormalizer()
        self.use_temporal_prioritization = use_temporal_prioritization
        
        if use_temporal_prioritization:
            self.temporal_manager = TemporalVersionManager(neo4j)
        else:
            self.temporal_manager = None
        
        # In-memory tracking for rate limiting
        self.domain_last_crawl: Dict[str, datetime] = {}
        self.domain_crawl_delays: Dict[str, float] = defaultdict(lambda: default_crawl_delay)
    
    def add_url(self, url: str, priority: float = 1.0) -> bool:
        """
        Add URL to frontier if not already present.
        
        Args:
            url: URL to add
            priority: Priority (higher = more important)
            
        Returns:
            True if URL was added, False if already exists
        """
        if not self.normalizer.is_valid_url(url):
            return False
        
        normalized = self.normalizer.normalize(url)
        domain = self.normalizer.extract_domain(normalized)
        
        if not domain:
            return False
        
        # Check if URL already exists
        query = """
        MATCH (w:WebPage {normalized_url: $normalized_url})
        RETURN w.normalized_url as url
        LIMIT 1
        """
        existing = self.neo4j.execute_read(
            query,
            parameters={"normalized_url": normalized}
        )
        
        if existing:
            return False
        
        # Create or update WebPage node
        now = datetime.utcnow()
        create_query = """
        MERGE (w:WebPage {normalized_url: $normalized_url})
        ON CREATE SET
            w.original_url = $original_url,
            w.domain = $domain,
            w.next_crawl_at = datetime(),
            w.crawl_interval_days = 0.042,  // 1 hour in days
            w.change_count = 0,
            w.no_change_count = 0,
            w.robots_allowed = true,
            w.created_at = datetime(),
            w.updated_at = datetime()
        ON MATCH SET
            w.updated_at = datetime()
        RETURN w
        """
        
        self.neo4j.execute_write(
            create_query,
            parameters={
                "normalized_url": normalized,
                "original_url": url,
                "domain": domain,
            }
        )
        
        return True
    
    def get_next_urls(self, limit: int = 100) -> List[Dict]:
        """
        Get next URLs ready for crawling, respecting rate limits.
        
        Args:
            limit: Maximum number of URLs to return
            
        Returns:
            List of URL dictionaries with metadata
        """
        now = datetime.utcnow()
        ready_urls = []
        
        # Get URLs ready for crawling
        query = """
        MATCH (w:WebPage)
        WHERE w.next_crawl_at IS NOT NULL 
        AND w.next_crawl_at <= datetime()
        AND w.robots_allowed = true
        RETURN w.normalized_url as url,
               w.domain as domain,
               w.next_crawl_at as next_crawl_at
        ORDER BY w.next_crawl_at ASC
        LIMIT $limit
        """
        
        candidates = self.neo4j.execute_read(
            query,
            parameters={"limit": limit * 2}  # Get more to filter by rate limits
        )
        
        # Filter by domain rate limits
        for record in candidates:
            url = record["url"]
            domain = record["domain"]
            
            if not domain:
                continue
            
            # Check if we can crawl this domain
            last_crawl = self.domain_last_crawl.get(domain)
            delay = self.domain_crawl_delays.get(domain, self.default_crawl_delay)
            
            if last_crawl:
                time_since = (now - last_crawl).total_seconds()
                if time_since < delay:
                    continue  # Skip, not enough time has passed
            
            ready_urls.append({
                "url": url,
                "domain": domain,
            })
            
            if len(ready_urls) >= limit:
                break
        
        return ready_urls
    
    def mark_crawled(self, url: str, domain: str) -> None:
        """
        Mark URL as crawled and update domain rate limit tracking.
        
        Args:
            url: Normalized URL
            domain: Domain of the URL
        """
        now = datetime.utcnow()
        self.domain_last_crawl[domain] = now
        
        # Update Neo4j
        query = """
        MATCH (w:WebPage {normalized_url: $url})
        SET w.last_crawled_at = datetime(),
            w.updated_at = datetime()
        """
        self.neo4j.execute_write(query, parameters={"url": url})
    
    def set_domain_crawl_delay(self, domain: str, delay: float) -> None:
        """
        Set crawl delay for a domain (from robots.txt).
        
        Args:
            domain: Domain name
            delay: Delay in seconds
        """
        self.domain_crawl_delays[domain] = delay
    
    def get_domain_stats(self) -> Dict[str, int]:
        """
        Get statistics about URLs per domain.
        
        Returns:
            Dictionary mapping domain to URL count
        """
        query = """
        MATCH (w:WebPage)
        RETURN w.domain as domain, count(w) as count
        ORDER BY count DESC
        """
        results = self.neo4j.execute_read(query)
        return {record["domain"]: record["count"] for record in results}
    
    def get_temporal_priority(self, url: str) -> float:
        """
        Calculate priority based on temporal history (change frequency).
        
        Args:
            url: Normalized URL
            
        Returns:
            Priority score (higher = more important)
        """
        if not self.use_temporal_prioritization or not self.temporal_manager:
            return 1.0  # Default priority
        
        # Higher priority for pages that change frequently
        change_rate = self.temporal_manager.get_change_frequency(url, days=30)
        
        # Normalize: 0-10 changes/month -> 0.5-2.0 priority multiplier
        if change_rate == 0:
            return 0.5  # Low priority for static pages
        elif change_rate > 10:
            return 2.0  # High priority for very active pages
        else:
            return 0.5 + (change_rate / 10.0 * 1.5)  # Linear scaling

