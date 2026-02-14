"""Imageboard platform adapter using public JSON API."""

import os
import time
import random
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import requests
from urllib.parse import urlparse

from .base import PlatformAdapter
from ..models.post import Post
from ..models.subreddit import Subreddit


class ImageboardAdapter(PlatformAdapter):
    """Imageboard adapter using public JSON API (no API key required)."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        keywords: Optional[List[str]] = None,
        mock: bool = False,
    ):
        """
        Initialize imageboard adapter.
        
        Args:
            user_agent: Custom User-Agent string
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            keywords: List of keywords to filter threads by (case-insensitive, whole-word matching)
            mock: If True, return mock data without network requests
        """
        self.user_agent = (
            user_agent
            or os.getenv("FEED_USER_AGENT", "feed/1.0 (by /u/feeduser)")
        )
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.keywords = keywords or ["irl"]
        self.mock = mock
        self.headers = {"User-Agent": self.user_agent}
        self.base_url = "https://a.4cdn.org"

    def _delay(self) -> None:
        """Add human-like delay between requests."""
        if not self.mock:
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

    def _matches_keywords(self, title: str) -> bool:
        """
        Check if title matches any of the configured keywords using whole-word matching.
        
        Uses regex word boundaries (\b) to ensure keywords match as complete words,
        not substrings. This prevents "irl" from matching "GIRL", "twirl", etc.
        
        Args:
            title: Thread title/subject to check
        
        Returns:
            True if title matches any keyword, False otherwise
        """
        if not self.keywords or not title:
            return True  # No keywords means match all
        
        title_lower = title.lower()
        
        for keyword in self.keywords:
            # Escape special regex characters in keyword
            escaped_keyword = re.escape(keyword.lower())
            # Use word boundaries to match whole words only
            pattern = r'\b' + escaped_keyword + r'\b'
            if re.search(pattern, title_lower):
                return True
        
        return False

    def fetch_threads(self, board: str) -> List[Dict[str, Any]]:
        """
        Fetch catalog (list of threads) from a board.
        
        Args:
            board: Board name (e.g., "b", "pol")
        
        Returns:
            List of thread data dictionaries
        """
        if self.mock:
            return self._fetch_threads_mock(board)
        
        url = f"{self.base_url}/{board}/catalog.json"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            catalog = response.json()
            
            # Catalog is a list of pages, each containing threads
            all_threads = []
            for page in catalog:
                threads = page.get("threads", [])
                all_threads.extend(threads)
            
            # Filter by keywords in thread subject
            filtered_threads = []
            for thread in all_threads:
                subject = thread.get("sub", "") or thread.get("com", "")
                # Extract text from HTML comment if present
                if subject and "<" in subject:
                    # Simple HTML tag removal
                    subject = re.sub(r'<[^>]+>', '', subject)
                
                if self._matches_keywords(subject):
                    filtered_threads.append(thread)
            
            self._delay()
            return filtered_threads
            
        except requests.RequestException as e:
            print(f"Error fetching catalog from /{board}/: {e}")
            return []

    def fetch_thread(self, board: str, thread_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single thread with all its posts.
        
        Args:
            board: Board name
            thread_id: Thread ID number
        
        Returns:
            Thread data dictionary or None if thread not found/archived
        """
        if self.mock:
            return self._fetch_thread_mock(board, thread_id)
        
        url = f"{self.base_url}/{board}/thread/{thread_id}.json"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self._delay()
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Thread /{board}/{thread_id} not found (likely archived)")
                return None
            raise
        except requests.RequestException as e:
            print(f"Error fetching thread /{board}/{thread_id}: {e}")
            return None

    def fetch_posts(
        self,
        source: str,
        sort: str = "new",
        limit: int = 100,
        after: Optional[str] = None,
    ) -> Tuple[List[Post], Optional[str]]:
        """
        Fetch posts from a board by getting threads and converting to Post objects.
        
        This method implements the PlatformAdapter interface.
        Note: Imageboard doesn't have pagination like Reddit, so 'after' and 'sort' are ignored.
        
        Args:
            source: Board name (e.g., "b", "pol")
            sort: Ignored for imageboard
            limit: Maximum number of posts to return
            after: Ignored for imageboard
        
        Returns:
            Tuple of (list of posts, None for pagination token)
        """
        board = source.replace("/", "")
        
        # Get threads from catalog
        threads = self.fetch_threads(board)
        
        if not threads:
            return [], None
        
        # Limit number of threads to process
        threads = threads[:limit]
        
        all_posts = []
        
        # Fetch each thread and convert posts
        for thread_data in threads:
            thread_id = thread_data.get("no")
            if not thread_id:
                continue
            
            # Get full thread data
            thread = self.fetch_thread(board, thread_id)
            if not thread:
                continue  # Thread archived or not found
            
            posts = thread.get("posts", [])
            if not posts:
                continue
            
            # Get subject from first post (OP)
            op_post = posts[0]
            subject = op_post.get("sub", "") or ""
            
            # Convert each post with an image to a Post object
            for post_data in posts:
                # Only include posts with images
                if not post_data.get("tim"):
                    continue
                
                # Build image URL: https://i.4cdn.org/board/tim.ext
                tim = post_data.get("tim")
                ext = post_data.get("ext", ".jpg")
                image_url = f"https://i.4cdn.org/{board}/{tim}{ext}"
                
                # Create Post object
                post_id = f"{board}_{thread_id}_{post_data.get('no', '')}"
                created_timestamp = post_data.get("time", 0)
                created_utc = datetime.fromtimestamp(created_timestamp)
                
                # Get comment text (remove HTML tags)
                comment = post_data.get("com", "")
                if comment and "<" in comment:
                    comment = re.sub(r'<[^>]+>', '', comment)
                
                post = Post(
                    id=post_id,
                    title=subject or f"Thread {thread_id}",
                    created_utc=created_utc,
                    score=post_data.get("replies", 0),
                    num_comments=post_data.get("replies", 0),
                    upvote_ratio=0.0,  # Imageboard doesn't have voting
                    over_18=True,  # Assume /b/ is NSFW
                    url=image_url,
                    selftext=comment,
                    author=None,  # Imageboard is anonymous
                    subreddit=board,  # Reuse subreddit field for board name
                    permalink=f"/{board}/thread/{thread_id}#p{post_data.get('no', '')}",
                )
                all_posts.append(post)
                
                if len(all_posts) >= limit:
                    break
            
            if len(all_posts) >= limit:
                break
        
        return all_posts[:limit], None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch board metadata.
        
        Args:
            source: Board name
        
        Returns:
            Subreddit metadata object (reusing the model) or None
        """
        board = source.replace("/", "")
        
        # Imageboard doesn't provide board metadata via JSON API easily
        # Return a basic object
        return Subreddit(
            name=board,
            subscribers=None,
            created_utc=None,
            description=f"Imageboard /{board}/ board",
        )

    def _fetch_threads_mock(self, board: str) -> List[Dict[str, Any]]:
        """Return mock threads for testing."""
        return [
            {
                "no": 123456789,
                "sub": "IRL fap 6",
                "replies": 100,
                "images": 50,
            },
            {
                "no": 987654321,
                "sub": "GIRL thread",
                "replies": 200,
                "images": 75,
            },
        ]

    def _fetch_thread_mock(self, board: str, thread_id: int) -> Dict[str, Any]:
        """Return mock thread for testing."""
        return {
            "posts": [
                {
                    "no": thread_id,
                    "time": int(time.time()),
                    "sub": "IRL fap 6",
                    "com": "Mock thread comment",
                    "tim": 1234567890123,
                    "ext": ".jpg",
                    "replies": 10,
                }
            ]
        }






