"""Robots.txt parser and compliance checker."""

import re
from typing import Optional, Dict, Set, List
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
import requests
from collections import defaultdict

from ..storage.neo4j_connection import Neo4jConnection


class RobotsParser:
    """Parses robots.txt files and checks crawl permissions."""
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        user_agent: str = "feed-crawler/1.0",
        cache_ttl_hours: int = 24,
    ):
        """
        Initialize robots parser.
        
        Args:
            neo4j: Neo4j connection for caching
            user_agent: User agent string for robots.txt
            cache_ttl_hours: Hours to cache robots.txt rules
        """
        self.neo4j = neo4j
        self.user_agent = user_agent
        self.cache_ttl_hours = cache_ttl_hours
        
        # In-memory cache
        self._cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    def fetch_robots_txt(self, domain: str) -> Optional[str]:
        """
        Fetch robots.txt for a domain.
        
        Args:
            domain: Domain name (e.g., "example.com")
            
        Returns:
            robots.txt content or None if not available
        """
        try:
            robots_url = f"https://{domain}/robots.txt"
            response = requests.get(
                robots_url,
                timeout=10,
                headers={"User-Agent": self.user_agent},
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
        except Exception:
            # Try HTTP if HTTPS fails
            try:
                robots_url = f"http://{domain}/robots.txt"
                response = requests.get(
                    robots_url,
                    timeout=10,
                    headers={"User-Agent": self.user_agent},
                    allow_redirects=True
                )
                response.raise_for_status()
                return response.text
            except Exception:
                return None
    
    def parse_robots_txt(self, content: str) -> Dict:
        """
        Parse robots.txt content into rules.
        
        Args:
            content: robots.txt content
            
        Returns:
            Dictionary with rules: {"allowed": Set[str], "disallowed": Set[str], "crawl_delay": float}
        """
        rules = {
            "allowed": set(),
            "disallowed": set(),
            "crawl_delay": None,
            "sitemaps": [],
        }
        
        current_user_agents = []
        default_crawl_delay = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse directive
            if ':' not in line:
                continue
            
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()
            
            if directive == 'user-agent':
                current_user_agents = [ua.lower() for ua in value.split(',')]
            elif directive == 'allow':
                if '*' in current_user_agents or self.user_agent.lower() in current_user_agents:
                    rules["allowed"].add(value)
            elif directive == 'disallow':
                if '*' in current_user_agents or self.user_agent.lower() in current_user_agents:
                    rules["disallowed"].add(value)
            elif directive == 'crawl-delay':
                if '*' in current_user_agents or self.user_agent.lower() in current_user_agents:
                    try:
                        delay = float(value)
                        if default_crawl_delay is None or delay < default_crawl_delay:
                            default_crawl_delay = delay
                    except ValueError:
                        pass
            elif directive == 'sitemap':
                rules["sitemaps"].append(value)
        
        rules["crawl_delay"] = default_crawl_delay
        
        return rules
    
    def is_allowed(self, url: str, domain: Optional[str] = None) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            domain: Domain name (extracted from URL if not provided)
            
        Returns:
            True if crawling is allowed
        """
        if not domain:
            domain = urlparse(url).netloc.lower()
            if ':' in domain:
                domain = domain.split(':')[0]
        
        if not domain:
            return True  # Default allow if can't determine domain
        
        # Get or fetch robots.txt rules
        rules = self.get_rules(domain)
        
        if not rules:
            return True  # Default allow if no robots.txt
        
        # Extract path from URL
        parsed = urlparse(url)
        path = parsed.path
        
        # Check disallowed patterns first
        for pattern in rules["disallowed"]:
            if self._matches_pattern(path, pattern):
                # Check if there's an allow that overrides
                allowed_override = False
                for allow_pattern in rules["allowed"]:
                    if self._matches_pattern(path, allow_pattern):
                        allowed_override = True
                        break
                
                if not allowed_override:
                    return False
        
        return True
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if path matches robots.txt pattern.
        
        Args:
            path: URL path
            pattern: Pattern from robots.txt (supports * wildcard)
            
        Returns:
            True if path matches pattern
        """
        if not pattern:
            return False
        
        # Convert pattern to regex
        # * matches any sequence of characters
        regex_pattern = pattern.replace('*', '.*')
        regex_pattern = f"^{regex_pattern}"
        
        try:
            return bool(re.match(regex_pattern, path))
        except Exception:
            return False
    
    def get_crawl_delay(self, domain: str) -> Optional[float]:
        """
        Get crawl delay for a domain from robots.txt.
        
        Args:
            domain: Domain name
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        rules = self.get_rules(domain)
        return rules.get("crawl_delay") if rules else None
    
    def get_rules(self, domain: str) -> Optional[Dict]:
        """
        Get robots.txt rules for a domain (with caching).
        
        Args:
            domain: Domain name
            
        Returns:
            Rules dictionary or None
        """
        # Check in-memory cache
        if domain in self._cache:
            timestamp = self._cache_timestamps.get(domain)
            if timestamp:
                age = datetime.utcnow() - timestamp
                if age < timedelta(hours=self.cache_ttl_hours):
                    return self._cache[domain]
        
        # Check database cache
        query = """
        MATCH (d:Domain {name: $domain})
        WHERE d.robots_rules IS NOT NULL
        AND d.robots_fetched_at IS NOT NULL
        AND d.robots_fetched_at > datetime() - duration({hours: $ttl_hours})
        RETURN d.robots_rules as rules
        LIMIT 1
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"domain": domain, "ttl_hours": self.cache_ttl_hours}
        )
        
        if result:
            rules = result[0].get("rules")
            if rules:
                self._cache[domain] = rules
                self._cache_timestamps[domain] = datetime.utcnow()
                return rules
        
        # Fetch and parse robots.txt
        content = self.fetch_robots_txt(domain)
        if content is None:
            return None
        
        rules = self.parse_robots_txt(content)
        
        # Store in cache
        self._cache[domain] = rules
        self._cache_timestamps[domain] = datetime.utcnow()
        
        # Store in database (create Domain node if needed)
        # Note: This requires a Domain node type in schema
        # For now, we'll just use in-memory cache
        
        return rules
    
    def update_page_robots_status(self, url: str, allowed: bool) -> None:
        """
        Update robots.txt compliance status for a page.
        
        Args:
            url: Normalized URL
            allowed: Whether robots.txt allows crawling
        """
        query = """
        MATCH (w:WebPage {normalized_url: $url})
        SET w.robots_allowed = $allowed,
            w.updated_at = datetime()
        """
        
        self.neo4j.execute_write(
            query,
            parameters={"url": url, "allowed": allowed}
        )

