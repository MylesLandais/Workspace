"""Blog/RSS platform adapter that parses RSS feeds and scrapes full post content."""

import os
import time
import random
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse, urljoin
import requests
import feedparser
from bs4 import BeautifulSoup

from .base import PlatformAdapter
from ..models.post import Post
from ..models.subreddit import Subreddit


class BlogAdapter(PlatformAdapter):
    """Blog adapter that parses RSS feeds and enriches with full post content."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        mock: bool = False,
    ):
        """
        Initialize Blog adapter.
        
        Args:
            user_agent: Custom User-Agent string
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            mock: If True, return mock data without network requests
        """
        self.user_agent = (
            user_agent
            or os.getenv("FEED_USER_AGENT", "feed/1.0 (BlogBot)")
        )
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.mock = mock
        self.headers = {"User-Agent": self.user_agent}
        self._post_metadata = {}  # Store metadata for posts

    def _delay(self) -> None:
        """Add human-like delay between requests."""
        if not self.mock:
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

    def _scrape_post_content(self, post_url: str) -> Dict[str, Any]:
        """
        Scrape full content from a blog post URL.
        
        Args:
            post_url: URL of the blog post
            
        Returns:
            Dictionary with 'content', 'images', 'author', etc.
        """
        try:
            response = requests.get(post_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Try to find main content area (common patterns)
            content = None
            content_selectors = [
                'article',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.post',
                '#content',
                '.post-body',
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem
                    break
            
            # Fallback to body if no content area found
            if not content:
                content = soup.find('body')
            
            if not content:
                return {
                    'content': '',
                    'images': [],
                    'author': None,
                    'published_date': None,
                }
            
            # Extract text content
            text_content = content.get_text(separator='\n', strip=True)
            
            # Extract images
            images = []
            for img in content.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    # Make absolute URL if relative
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        parsed_url = urlparse(post_url)
                        src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                    elif not src.startswith('http'):
                        src = urljoin(post_url, src)
                    images.append(src)
            
            # Try to extract author
            author = None
            author_selectors = [
                '.author',
                '.post-author',
                '[rel="author"]',
                '.byline',
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Try to extract published date
            published_date = None
            date_selectors = [
                'time[datetime]',
                '.published',
                '.post-date',
                '[itemprop="datePublished"]',
            ]
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    datetime_attr = date_elem.get('datetime')
                    if datetime_attr:
                        try:
                            published_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        except:
                            pass
                    if not published_date:
                        date_text = date_elem.get_text(strip=True)
                        # Try to parse common date formats
                        # This is a simple fallback - could be enhanced
                        pass
                    break
            
            self._delay()
            
            return {
                'content': text_content,
                'images': images,
                'author': author,
                'published_date': published_date,
            }
            
        except Exception as e:
            print(f"Error scraping post content from {post_url}: {e}")
            return {
                'content': '',
                'images': [],
                'author': None,
                'published_date': None,
            }

    def _matches_entity(self, text: str, entity: str, case_sensitive: bool = False) -> bool:
        """
        Check if text contains the entity (exact match, not fuzzy).
        
        Args:
            text: Text to search in
            entity: Entity name to match (e.g., "princess lexie")
            case_sensitive: Whether matching should be case-sensitive
            
        Returns:
            True if entity is found in text
        """
        if not text or not entity:
            return False
        
        if not case_sensitive:
            text = text.lower()
            entity = entity.lower()
        
        # Use word boundaries to avoid partial matches
        # This ensures "princess lexie" matches but "princess lexi" doesn't
        pattern = r'\b' + re.escape(entity) + r'\b'
        return bool(re.search(pattern, text))

    def fetch_posts(
        self,
        source: str,
        sort: str = "new",
        limit: int = 100,
        after: Optional[str] = None,
        entity_filter: Optional[str] = None,
        scrape_content: bool = True,
    ) -> Tuple[List[Post], Optional[str]]:
        """
        Fetch posts from an RSS feed.
        
        Args:
            source: RSS feed URL
            sort: Sort order (ignored for RSS, kept for API compatibility)
            limit: Maximum number of posts to fetch
            after: Pagination token (ignored for RSS, kept for API compatibility)
            entity_filter: Optional entity name to filter posts (e.g., "princess lexie")
            scrape_content: Whether to scrape full content from post URLs
            
        Returns:
            Tuple of (list of posts, next page token or None)
        """
        if self.mock:
            return self._fetch_posts_mock(source, limit, entity_filter)
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(source)
            
            if feed.bozo and feed.bozo_exception:
                print(f"Error parsing RSS feed: {feed.bozo_exception}")
                return [], None
            
            posts = []
            
            for entry in feed.entries[:limit]:
                # Extract basic info from RSS
                post_url = entry.get('link', '')
                title = entry.get('title', '')
                description = entry.get('description', '')
                published = entry.get('published_parsed')
                
                # Convert published date
                created_utc = datetime.utcnow()
                if published:
                    try:
                        created_utc = datetime(*published[:6])
                    except:
                        pass
                
                # Combine title and description for entity matching
                search_text = f"{title} {description}".lower()
                
                # Apply entity filter if provided
                if entity_filter:
                    if not self._matches_entity(search_text, entity_filter, case_sensitive=False):
                        continue
                
                # Scrape full content if requested
                full_content = description
                images = []
                author = entry.get('author')
                published_date = created_utc
                
                if scrape_content and post_url:
                    scraped = self._scrape_post_content(post_url)
                    full_content = scraped['content'] or description
                    images = scraped['images']
                    if scraped['author']:
                        author = scraped['author']
                    if scraped['published_date']:
                        published_date = scraped['published_date']
                
                # Create post ID from URL (use slug or hash)
                post_id = self._generate_post_id(post_url)
                
                # Create Post object
                # Note: Blog posts don't have all Reddit fields, so we use defaults
                post = Post(
                    id=post_id,
                    title=title,
                    created_utc=published_date,
                    score=0,  # Blogs don't have scores
                    num_comments=0,  # Could be scraped if blog has comments
                    upvote_ratio=0.0,
                    over_18=False,  # Could be determined from content
                    url=post_url,
                    selftext=full_content,  # Store full content in selftext
                    author=author,
                    subreddit=self._extract_blog_name(source),  # Use blog name as "subreddit"
                    permalink=post_url,
                )
                
                # Store additional metadata separately (can't add to Pydantic model)
                # We'll return a tuple with post and metadata
                post_data = {
                    'post': post,
                    'images': images,
                    'entity_matched': entity_filter if entity_filter else None,
                }
                posts.append(post_data)
            
            self._delay()
            # Extract just the Post objects for return (metadata is stored separately)
            post_objects = [p['post'] for p in posts]
            # Store metadata in a dict keyed by post ID for later retrieval
            self._post_metadata = {p['post'].id: p for p in posts}
            return post_objects, None  # RSS feeds typically don't have pagination tokens
            
        except Exception as e:
            print(f"Error fetching posts from RSS feed {source}: {e}")
            import traceback
            traceback.print_exc()
            return [], None

    def _generate_post_id(self, url: str) -> str:
        """Generate a post ID from URL."""
        # Use the URL slug or hash it
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if path:
            # Use last part of path as ID
            slug = path.split('/')[-1]
            # Remove common extensions
            slug = slug.replace('.html', '').replace('.php', '')
            return slug[:100]  # Limit length
        # Fallback: hash the URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _extract_blog_name(self, feed_url: str) -> str:
        """Extract blog name from feed URL."""
        parsed = urlparse(feed_url)
        domain = parsed.netloc.replace('www.', '')
        # Remove common TLDs for cleaner name
        domain = domain.split('.')[0]
        return domain

    def get_post_metadata(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata (images, entity_matched) for a post by ID.
        
        Args:
            post_id: Post ID
            
        Returns:
            Dictionary with 'images' and 'entity_matched' or None
        """
        return self._post_metadata.get(post_id)
    
    def _fetch_posts_mock(
        self,
        source: str,
        limit: int,
        entity_filter: Optional[str],
    ) -> Tuple[List[Post], Optional[str]]:
        """Return mock posts for testing."""
        now = datetime.utcnow()
        mock_post = Post(
            id="mock-blog-1",
            title="Princess Lexie Height Comparison JOI",
            created_utc=now.replace(day=20, hour=7, minute=8, second=11),
            score=0,
            num_comments=0,
            upvote_ratio=0.0,
            over_18=False,
            url="https://femdom-pov.me/princess-lexie-height-comparison-joi/",
            selftext="Mock blog post content about Princess Lexie...",
            author="mock_author",
            subreddit="femdom-pov",
            permalink="https://femdom-pov.me/princess-lexie-height-comparison-joi/",
        )
        
        mock_posts = [mock_post]
        
        if entity_filter:
            filtered = [
                p for p in mock_posts
                if self._matches_entity(f"{p.title} {p.selftext}", entity_filter)
            ]
            # Store metadata
            for p in filtered:
                self._post_metadata[p.id] = {
                    'images': [],
                    'entity_matched': entity_filter,
                }
            return filtered, None
        
        # Store metadata for all mock posts
        for p in mock_posts[:limit]:
            self._post_metadata[p.id] = {
                'images': [],
                'entity_matched': None,
            }
        return mock_posts[:limit], None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch metadata about a blog/RSS feed.
        
        Args:
            source: RSS feed URL
            
        Returns:
            Subreddit object (reused for blog metadata) or None if not found
        """
        if self.mock:
            return Subreddit(
                name=self._extract_blog_name(source),
                subscribers=None,
                created_utc=None,
                description="Mock blog feed",
                public_description="Mock blog feed description",
            )
        
        try:
            feed = feedparser.parse(source)
            
            if feed.bozo and feed.bozo_exception:
                print(f"Error parsing RSS feed: {feed.bozo_exception}")
                return None
            
            feed_info = feed.feed
            
            blog_name = self._extract_blog_name(source)
            description = feed_info.get('description', '')
            title = feed_info.get('title', blog_name)
            
            # Try to extract creation date from feed
            created_utc = None
            if feed_info.get('published_parsed'):
                try:
                    created_utc = datetime(*feed_info.published_parsed[:6])
                except:
                    pass
            
            subreddit_obj = Subreddit(
                name=blog_name,
                subscribers=None,  # Blogs don't have subscriber counts
                created_utc=created_utc,
                description=description,
                public_description=title,
            )
            
            self._delay()
            return subreddit_obj
            
        except Exception as e:
            print(f"Error fetching metadata for blog feed {source}: {e}")
            return None

