"""Bio-crawler service for discovering handles from anchor URLs."""

import re
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from ..ontology.schema import VerificationConfidence
from ..models.handle import Handle
from ..storage.neo4j_connection import Neo4jConnection
from ..crawler.frontier import URLFrontier
from ..crawler.scheduler import AdaptiveScheduler
from ..crawler.deduplication import DuplicateDetector
from ..crawler.content import ContentAnalyzer
from ..crawler.robots import RobotsParser


class CandidateHandle:
    """Represents a discovered handle candidate."""

    def __init__(
        self,
        username: str,
        platform: str,
        profile_url: str,
        confidence: VerificationConfidence,
        source_url: str,
        context: Optional[str] = None,
    ):
        self.username = username
        self.platform = platform
        self.profile_url = profile_url
        self.confidence = confidence
        self.source_url = source_url
        self.context = context
        self.discovered_at = datetime.utcnow()

    def to_handle(self) -> Handle:
        """Convert to Handle model."""
        return Handle(
            username=self.username,
            profile_url=self.profile_url,
            status=None,  # Will be set when creating relationship
            verified=False,
            confidence=self.confidence,
            discovered_at=self.discovered_at,
        )


class BioCrawler:
    """Service for discovering handles from anchor URLs (bio pages)."""

    # Platform URL patterns and extraction regex
    PLATFORM_PATTERNS = {
        "Instagram": {
            "patterns": [
                r"instagram\.com/([a-zA-Z0-9._]+)",
                r"instagr\.am/([a-zA-Z0-9._]+)",
            ],
            "base_url": "https://www.instagram.com/{username}/",
        },
        "TikTok": {
            "patterns": [
                r"tiktok\.com/@([a-zA-Z0-9._]+)",
                r"vm\.tiktok\.com/.*",
            ],
            "base_url": "https://www.tiktok.com/@{username}",
        },
        "Twitter": {
            "patterns": [
                r"twitter\.com/([a-zA-Z0-9_]+)",
                r"x\.com/([a-zA-Z0-9_]+)",
            ],
            "base_url": "https://twitter.com/{username}",
        },
        "YouTube": {
            "patterns": [
                r"youtube\.com/(?:c|channel|user|@)/([a-zA-Z0-9_-]+)",
                r"youtu\.be/.*",
            ],
            "base_url": "https://www.youtube.com/@{username}",
        },
        "Reddit": {
            "patterns": [
                r"reddit\.com/user/([a-zA-Z0-9_-]+)",
                r"redd\.it/.*",
            ],
            "base_url": "https://www.reddit.com/user/{username}",
        },
        "Facebook": {
            "patterns": [
                r"facebook\.com/([a-zA-Z0-9.]+)",
                r"fb\.com/([a-zA-Z0-9.]+)",
            ],
            "base_url": "https://www.facebook.com/{username}",
        },
        "LinkedIn": {
            "patterns": [
                r"linkedin\.com/in/([a-zA-Z0-9-]+)",
            ],
            "base_url": "https://www.linkedin.com/in/{username}",
        },
    }

    def __init__(
        self,
        neo4j: Optional[Neo4jConnection] = None,
        timeout: int = 10,
        user_agent: Optional[str] = None,
        use_crawler_components: bool = True,
    ):
        """
        Initialize bio-crawler.

        Args:
            neo4j: Neo4j connection (required if use_crawler_components=True)
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            use_crawler_components: Whether to use new crawler components
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        self.use_crawler_components = use_crawler_components
        
        if use_crawler_components:
            if neo4j is None:
                raise ValueError("Neo4j connection required when use_crawler_components=True")
            self.neo4j = neo4j
            self.frontier = URLFrontier(neo4j)
            self.scheduler = AdaptiveScheduler(neo4j)
            self.deduplicator = DuplicateDetector(neo4j)
            self.content_analyzer = ContentAnalyzer()
            self.robots_parser = RobotsParser(neo4j, user_agent=self.user_agent)
        else:
            self.neo4j = None
            self.frontier = None
            self.scheduler = None
            self.deduplicator = None
            self.content_analyzer = None
            self.robots_parser = None

    def discover_handles(self, anchor_url: str) -> List[CandidateHandle]:
        """
        Discover handles from an anchor URL (e.g., YouTube About page).

        Args:
            anchor_url: URL to scan for social media links

        Returns:
            List of CandidateHandle objects
        """
        candidates = []
        start_time = time.time()

        try:
            # Check robots.txt compliance if using crawler components
            if self.use_crawler_components:
                domain = self.frontier.normalizer.extract_domain(anchor_url)
                if not self.robots_parser.is_allowed(anchor_url, domain):
                    print(f"URL {anchor_url} disallowed by robots.txt")
                    # Update robots status in database
                    normalized = self.frontier.normalizer.normalize(anchor_url)
                    self.robots_parser.update_page_robots_status(normalized, False)
                    return []
                
                # Add URL to frontier if not already present
                self.frontier.add_url(anchor_url)
                normalized = self.frontier.normalizer.normalize(anchor_url)
                
                # Check if we should crawl this URL now (respect schedule)
                webpage = self.neo4j.get_webpage(normalized)
                if webpage:
                    next_crawl = webpage.get("next_crawl_at")
                    if next_crawl:
                        # Handle both Python datetime and Neo4j DateTime objects
                        if isinstance(next_crawl, datetime):
                            next_crawl_dt = next_crawl
                        else:
                            # Try to convert Neo4j DateTime to Python datetime
                            try:
                                next_crawl_dt = datetime.fromtimestamp(next_crawl.timestamp())
                            except (AttributeError, TypeError):
                                next_crawl_dt = None
                        
                        if next_crawl_dt and datetime.utcnow() < next_crawl_dt:
                            print(f"URL {anchor_url} not due for crawl until {next_crawl_dt}")
                            return []  # Not time to crawl yet
            
            # Fetch the page
            response = requests.get(
                anchor_url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                allow_redirects=True,
            )
            response.raise_for_status()
            
            content = response.text
            content_type = response.headers.get("Content-Type", "")
            crawl_duration_ms = int((time.time() - start_time) * 1000)

            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Find all links
            links = soup.find_all("a", href=True)

            for link in links:
                href = link.get("href", "")
                text = link.get_text(strip=True)
                context = self._get_context(link)

                # Resolve relative URLs
                full_url = urljoin(anchor_url, href)

                # Check against platform patterns
                for platform_name, platform_config in self.PLATFORM_PATTERNS.items():
                    for pattern in platform_config["patterns"]:
                        match = re.search(pattern, full_url, re.IGNORECASE)
                        if match:
                            username = match.group(1) if match.groups() else None
                            if username:
                                profile_url = platform_config["base_url"].format(
                                    username=username
                                )
                                confidence = self._assess_confidence(
                                    full_url, text, context, anchor_url
                                )
                                candidates.append(
                                    CandidateHandle(
                                        username=username,
                                        platform=platform_name,
                                        profile_url=profile_url,
                                        confidence=confidence,
                                        source_url=anchor_url,
                                        context=context,
                                    )
                                )
                                break  # Found match for this platform, move to next link

            # Remove duplicates (same platform + username)
            seen = set()
            unique_candidates = []
            for candidate in candidates:
                key = (candidate.platform, candidate.username.lower())
                if key not in seen:
                    seen.add(key)
                    unique_candidates.append(candidate)
            
            # Store crawl metadata if using crawler components
            if self.use_crawler_components:
                normalized = self.frontier.normalizer.normalize(anchor_url)
                domain = self.frontier.normalizer.extract_domain(anchor_url)
                
                # Check for content duplicates
                duplicate_info = self.deduplicator.check_and_store_content(
                    normalized,
                    content,
                    exclude_url=normalized
                )
                
                # Get previous content hash to detect changes
                webpage = self.neo4j.get_webpage(normalized)
                old_hash = webpage.get("content_hash") if webpage else None
                changed = duplicate_info["content_hash"] != old_hash if old_hash else True
                
                # Update crawl metadata
                self.neo4j.update_webpage_crawl_metadata(
                    normalized,
                    http_status=response.status_code,
                    content_type=self.content_analyzer.detect_content_type(content, content_type),
                    content_length=len(content.encode('utf-8')),
                    crawl_duration_ms=crawl_duration_ms,
                )
                
                # Record crawl history (with temporal versioning)
                self.deduplicator.record_crawl_history(
                    normalized,
                    response.status_code,
                    duplicate_info["content_hash"],
                    changed,
                    content_length=len(content.encode('utf-8')),
                    crawl_duration_ms=crawl_duration_ms,
                    simhash=duplicate_info.get("simhash"),
                    content_type=self.content_analyzer.detect_content_type(content, content_type),
                )
                
                # Schedule next crawl using adaptive decay
                self.scheduler.schedule_next_crawl(normalized, changed)
                
                # Mark as crawled in frontier
                self.frontier.mark_crawled(normalized, domain)
                
                # Update robots status
                self.robots_parser.update_page_robots_status(normalized, True)
                
                # Add discovered URLs to frontier for future crawling
                for candidate in unique_candidates:
                    if self.frontier.normalizer.is_valid_url(candidate.profile_url):
                        self.frontier.add_url(candidate.profile_url)

            return unique_candidates

        except requests.RequestException as e:
            print(f"Error fetching {anchor_url}: {e}")
            # Record failure if using crawler components
            if self.use_crawler_components:
                try:
                    normalized = self.frontier.normalizer.normalize(anchor_url)
                    domain = self.frontier.normalizer.extract_domain(anchor_url)
                    self.neo4j.update_webpage_crawl_metadata(
                        normalized,
                        http_status=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                    )
                    # Still mark as crawled to update timestamp
                    self.frontier.mark_crawled(normalized, domain)
                except Exception:
                    pass
            return []
        except Exception as e:
            print(f"Error parsing {anchor_url}: {e}")
            return []

    def _get_context(self, link_element) -> Optional[str]:
        """Extract surrounding context text from link element."""
        try:
            # Get parent element text (limited to 200 chars)
            parent = link_element.parent
            if parent:
                text = parent.get_text(strip=True)
                return text[:200] if text else None
        except Exception:
            pass
        return None

    def _assess_confidence(
        self, url: str, link_text: str, context: Optional[str], source_url: str
    ) -> VerificationConfidence:
        """
        Assess confidence level for a discovered handle.

        Args:
            url: Discovered URL
            link_text: Text of the link
            context: Surrounding context
            source_url: Source page URL

        Returns:
            VerificationConfidence level
        """
        # High confidence: Link is in a trusted section (About, Bio, etc.)
        trusted_sections = ["about", "bio", "contact", "links", "social"]
        if any(section in source_url.lower() for section in trusted_sections):
            return VerificationConfidence.HIGH

        # Medium confidence: Username appears in link text or context
        if link_text or (context and len(context) > 10):
            return VerificationConfidence.MEDIUM

        # Default to medium
        return VerificationConfidence.MEDIUM

    def extract_username_from_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract platform and username from a direct profile URL.

        Args:
            url: Profile URL

        Returns:
            Dict with 'platform' and 'username' keys, or None
        """
        for platform_name, platform_config in self.PLATFORM_PATTERNS.items():
            for pattern in platform_config["patterns"]:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    username = match.group(1) if match.groups() else None
                    if username:
                        return {
                            "platform": platform_name,
                            "username": username,
                        }
        return None

