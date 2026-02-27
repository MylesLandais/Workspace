"""Tumblr platform adapter that parses blog RSS feeds and scrapes full post content."""

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


class TumblrAdapter(PlatformAdapter):
    """Tumblr adapter that parses RSS feeds and enriches with full post content."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        mock: bool = False,
    ):
        """
        Initialize Tumblr adapter.

        Args:
            user_agent: Custom User-Agent string
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            mock: If True, return mock data without network requests
        """
        self.user_agent = (
            user_agent
            or os.getenv("FEED_USER_AGENT", "feed/1.0 (TumblrBot)")
        )
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.mock = mock
        self.headers = {"User-Agent": self.user_agent}
        self._post_metadata = {}

    def _delay(self) -> None:
        """Add human-like delay between requests."""
        if not self.mock:
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

    def _normalize_blog_url(self, source: str) -> str:
        """
        Normalize Tumblr blog URL to RSS feed URL.

        Args:
            source: Blog URL or blog name (e.g., "blackswandive.tumblr.com" or "blackswandive")

        Returns:
            RSS feed URL
        """
        source = source.strip()

        if not source:
            raise ValueError("Blog URL cannot be empty")

        if source.startswith("http://") or source.startswith("https://"):
            parsed = urlparse(source)
            blog_name = parsed.netloc.replace(".tumblr.com", "").replace("www.", "")
        else:
            blog_name = source.replace(".tumblr.com", "")

        if not blog_name:
            raise ValueError(f"Invalid Tumblr blog URL: {source}")

        return f"https://{blog_name}.tumblr.com/rss"

    def _extract_post_id(self, url: str) -> str:
        """
        Extract post ID from Tumblr post URL.

        Args:
            url: Tumblr post URL

        Returns:
            Post ID
        """
        match = re.search(r"/post/(\d+)", url)
        if match:
            return match.group(1)
        return url.split("/")[-1] if url else ""

    def _scrape_post_content(self, post_url: str) -> Dict[str, Any]:
        """
        Scrape full content from a Tumblr post URL.

        Args:
            post_url: URL of the Tumblr post

        Returns:
            Dictionary with 'content', 'images', 'author', etc.
        """
        try:
            response = requests.get(post_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            content_selectors = [
                '.post-content',
                '.caption',
                '.body',
                'article',
                'main',
                '#content',
            ]

            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem
                    break

            if not content:
                content = soup.find('body')

            if not content:
                return {
                    'content': '',
                    'images': [],
                    'author': None,
                    'published_date': None,
                    'tags': [],
                }

            text_content = content.get_text(separator='\n', strip=True)

            images = []
            for img in content.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        parsed_url = urlparse(post_url)
                        src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                    elif not src.startswith('http'):
                        src = urljoin(post_url, src)
                    images.append(src)

            author = None
            author_selectors = [
                '.post-author',
                '.author',
                '[rel="author"]',
                '.byline',
                '.tumblr-blog',
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break

            tags = []
            tag_elements = soup.select('.tags a, .tag, [href*="/tagged/"]')
            for tag_elem in tag_elements:
                tag = tag_elem.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)

            published_date = None
            date_selectors = [
                'time[datetime]',
                '.post-date',
                '.timestamp',
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
                    break

            self._delay()

            return {
                'content': text_content,
                'images': images,
                'author': author,
                'published_date': published_date,
                'tags': tags,
            }

        except Exception as e:
            print(f"Error scraping post content from {post_url}: {e}")
            return {
                'content': '',
                'images': [],
                'author': None,
                'published_date': None,
                'tags': [],
            }

    def _matches_entity(self, text: str, entity: str, case_sensitive: bool = False) -> bool:
        """
        Check if text contains the entity (exact match, not fuzzy).

        Args:
            text: Text to search in
            entity: Entity name to match
            case_sensitive: Whether matching should be case-sensitive

        Returns:
            True if entity is found in text
        """
        if not text or not entity:
            return False

        if not case_sensitive:
            text = text.lower()
            entity = entity.lower()

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
        Fetch posts from a Tumblr blog RSS feed.

        Args:
            source: Tumblr blog URL or name (e.g., "blackswandive" or "https://blackswandive.tumblr.com")
            sort: Sort order (ignored for RSS, kept for API compatibility)
            limit: Maximum number of posts to fetch
            after: Pagination token (ignored for RSS, kept for API compatibility)
            entity_filter: Optional entity name to filter posts
            scrape_content: Whether to scrape full content from post URLs

        Returns:
            Tuple of (list of posts, next page token or None)
        """
        if self.mock:
            return self._fetch_posts_mock(source, limit, entity_filter)

        try:
            rss_url = self._normalize_blog_url(source)

            feed = feedparser.parse(rss_url)

            if feed.bozo and feed.bozo_exception:
                print(f"Error parsing RSS feed: {feed.bozo_exception}")
                return [], None

            posts = []
            blog_name = feed.feed.get('title', self._extract_blog_name(source))

            for entry in feed.entries[:limit]:
                post_url = entry.get('link', '')
                title = entry.get('title', '')
                description = entry.get('description', '')
                published = entry.get('published_parsed')

                created_utc = datetime.utcnow()
                if published:
                    try:
                        created_utc = datetime(*published[:6])
                    except:
                        pass

                search_text = f"{title} {description}".lower()

                if entity_filter:
                    if not self._matches_entity(search_text, entity_filter, case_sensitive=False):
                        continue

                full_content = description
                images = []
                author = blog_name
                published_date = created_utc
                tags = []

                if scrape_content and post_url:
                    scraped = self._scrape_post_content(post_url)
                    full_content = scraped['content'] or description
                    images = scraped['images']
                    if scraped['author']:
                        author = scraped['author']
                    if scraped['published_date']:
                        published_date = scraped['published_date']
                    if scraped['tags']:
                        tags = scraped['tags']

                post_id = self._extract_post_id(post_url)

                post = Post(
                    id=post_id,
                    title=title,
                    created_utc=published_date,
                    score=0,
                    num_comments=0,
                    upvote_ratio=0.0,
                    over_18=False,
                    url=post_url,
                    selftext=full_content,
                    author=author,
                    subreddit=self._extract_blog_name(source),
                    permalink=post_url,
                )

                post_data = {
                    'post': post,
                    'images': images,
                    'tags': tags,
                    'entity_matched': entity_filter if entity_filter else None,
                }
                posts.append(post_data)

            self._delay()

            post_objects = [p['post'] for p in posts]
            self._post_metadata = {p['post'].id: p for p in posts}
            return post_objects, None

        except Exception as e:
            print(f"Error fetching posts from Tumblr blog {source}: {e}")
            import traceback
            traceback.print_exc()
            return [], None

    def _extract_blog_name(self, source: str) -> str:
        """
        Extract blog name from URL or name.

        Args:
            source: Blog URL or name

        Returns:
            Blog name
        """
        source = source.strip()
        if source.startswith("http://") or source.startswith("https://"):
            parsed = urlparse(source)
            name = parsed.netloc.replace(".tumblr.com", "").replace("www.", "")
        else:
            name = source.replace(".tumblr.com", "")
        return name

    def get_post_metadata(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata (images, tags, entity_matched) for a post by ID.

        Args:
            post_id: Post ID

        Returns:
            Dictionary with 'images', 'tags', and 'entity_matched' or None
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
            id="mock-tumblr-1",
            title="Photo",
            created_utc=now.replace(day=20, hour=7, minute=8, second=11),
            score=0,
            num_comments=0,
            upvote_ratio=0.0,
            over_18=False,
            url=f"https://{self._extract_blog_name(source)}.tumblr.com/post/123456789",
            selftext="Mock Tumblr post content...",
            author=self._extract_blog_name(source),
            subreddit=self._extract_blog_name(source),
            permalink=f"https://{self._extract_blog_name(source)}.tumblr.com/post/123456789",
        )

        mock_posts = [mock_post]

        if entity_filter:
            filtered = [
                p for p in mock_posts
                if self._matches_entity(f"{p.title} {p.selftext}", entity_filter)
            ]
            for p in filtered:
                self._post_metadata[p.id] = {
                    'images': [],
                    'tags': [],
                    'entity_matched': entity_filter,
                }
            return filtered, None

        for p in mock_posts[:limit]:
            self._post_metadata[p.id] = {
                'images': [],
                'tags': [],
                'entity_matched': None,
            }
        return mock_posts[:limit], None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch metadata about a Tumblr blog.

        Args:
            source: Tumblr blog URL or name

        Returns:
            Subreddit object (reused for blog metadata) or None if not found
        """
        if self.mock:
            return Subreddit(
                name=self._extract_blog_name(source),
                subscribers=None,
                created_utc=None,
                description="Mock Tumblr blog",
                public_description="Mock Tumblr blog description",
            )

        try:
            rss_url = self._normalize_blog_url(source)
            feed = feedparser.parse(rss_url)

            if feed.bozo and feed.bozo_exception:
                print(f"Error parsing RSS feed: {feed.bozo_exception}")
                return None

            feed_info = feed.feed

            blog_name = self._extract_blog_name(source)
            description = feed_info.get('description', '')
            title = feed_info.get('title', blog_name)

            created_utc = None
            if feed_info.get('published_parsed'):
                try:
                    created_utc = datetime(*feed_info.published_parsed[:6])
                except:
                    pass

            subreddit_obj = Subreddit(
                name=blog_name,
                subscribers=None,
                created_utc=created_utc,
                description=description,
                public_description=title,
            )

            self._delay()
            return subreddit_obj

        except Exception as e:
            print(f"Error fetching metadata for Tumblr blog {source}: {e}")
            return None
