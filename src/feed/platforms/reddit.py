"""Reddit platform adapter using public JSON endpoints."""

import os
import time
import random
from datetime import datetime
from typing import List, Optional, Tuple
import requests

from .base import PlatformAdapter
from ..models.post import Post
from ..models.subreddit import Subreddit


class RedditAdapter(PlatformAdapter):
    """Reddit adapter using public JSON endpoints (no API key required)."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        mock: bool = False,
    ):
        """
        Initialize Reddit adapter.
        
        Args:
            user_agent: Custom User-Agent string (required by Reddit)
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            mock: If True, return mock data without network requests
        """
        self.user_agent = (
            user_agent
            or os.getenv("FEED_USER_AGENT", "feed/1.0 (by /u/feeduser)")
        )
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.mock = mock
        self.headers = {"User-Agent": self.user_agent}

    def _delay(self) -> None:
        """Add human-like delay between requests."""
        if not self.mock:
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

    def fetch_posts(
        self,
        source: str,
        sort: str = "new",
        limit: int = 100,
        after: Optional[str] = None,
    ) -> Tuple[List[Post], Optional[str]]:
        """
        Fetch posts from a subreddit.
        
        Args:
            source: Subreddit name (with or without r/ prefix)
            sort: Sort order ("new", "hot", "top", "rising")
            limit: Maximum posts per page (max 100)
            after: Pagination token for next page
        
        Returns:
            Tuple of (list of posts, next page token or None)
        """
        # Remove r/ prefix if present
        subreddit = source.replace("r/", "").replace("/r/", "")
        
        if self.mock:
            return self._fetch_posts_mock(subreddit, sort, limit, after)
        
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
        params = {"limit": min(limit, 100)}
        if after:
            params["after"] = after
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            children = data.get("data", {}).get("children", [])
            next_after = data.get("data", {}).get("after")
            
            for child in children:
                post_data = child.get("data", {})
                try:
                    post = Post(
                        id=post_data.get("id"),
                        title=post_data.get("title", ""),
                        created_utc=datetime.fromtimestamp(
                            post_data.get("created_utc", 0)
                        ),
                        score=post_data.get("score", 0),
                        num_comments=post_data.get("num_comments", 0),
                        upvote_ratio=post_data.get("upvote_ratio", 0.0),
                        over_18=post_data.get("over_18", False),
                        url=post_data.get("url", ""),
                        selftext=post_data.get("selftext", ""),
                        author=post_data.get("author"),
                        subreddit=subreddit,
                        permalink=post_data.get("permalink"),
                    )
                    posts.append(post)
                except Exception as e:
                    print(f"Error parsing post {post_data.get('id')}: {e}")
                    continue
            
            self._delay()
            return posts, next_after
            
        except requests.RequestException as e:
            print(f"Error fetching posts from r/{subreddit}: {e}")
            return [], None

    def _fetch_posts_mock(
        self,
        subreddit: str,
        sort: str,
        limit: int,
        after: Optional[str],
    ) -> Tuple[List[Post], Optional[str]]:
        """Return mock posts for testing."""
        if after:
            return [], None
        
        now = datetime.utcnow()
        mock_posts = [
            Post(
                id="mock1abc",
                title="[Mock] Brooke in red dress looking amazing",
                created_utc=now.replace(day=20, hour=7, minute=8, second=11),
                score=156,
                num_comments=12,
                upvote_ratio=0.95,
                over_18=False,
                url="https://i.redd.it/mockimage1.jpg",
                selftext="",
                author="mock_user1",
                subreddit=subreddit,
                permalink=f"/r/{subreddit}/comments/mock1abc/",
            ),
            Post(
                id="mock2def",
                title="[Mock] New TikTok compilation - feet focus",
                created_utc=now.replace(day=21, hour=7, minute=8, second=11),
                score=89,
                num_comments=8,
                upvote_ratio=0.88,
                over_18=False,
                url="https://v.redd.it/mockvideo",
                selftext="",
                author="mock_user2",
                subreddit=subreddit,
                permalink=f"/r/{subreddit}/comments/mock2def/",
            ),
            Post(
                id="mock3ghi",
                title="[Mock] Brooke Monk bikini throwback",
                created_utc=now.replace(day=22, hour=7, minute=8, second=11),
                score=45,
                num_comments=5,
                upvote_ratio=0.92,
                over_18=False,
                url="https://i.redd.it/mockimage2.jpg",
                selftext="",
                author="mock_user3",
                subreddit=subreddit,
                permalink=f"/r/{subreddit}/comments/mock3ghi/",
            ),
        ]
        
        time.sleep(2)  # Simulate delay
        return mock_posts[:limit], None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch subreddit metadata.
        
        Args:
            source: Subreddit name (with or without r/ prefix)
        
        Returns:
            Subreddit metadata or None
        """
        subreddit = source.replace("r/", "").replace("/r/", "")
        
        if self.mock:
            return Subreddit(
                name=subreddit,
                subscribers=12456,
                created_utc=datetime.utcnow(),
                description="Mock subreddit description",
            )
        
        url = f"https://www.reddit.com/r/{subreddit}/about.json"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            subreddit_data = data.get("data", {})
            created_utc = None
            if subreddit_data.get("created_utc"):
                created_utc = datetime.fromtimestamp(subreddit_data["created_utc"])
            
            subreddit_obj = Subreddit(
                name=subreddit,
                subscribers=subreddit_data.get("subscribers"),
                created_utc=created_utc,
                description=subreddit_data.get("description"),
                public_description=subreddit_data.get("public_description"),
            )
            
            self._delay()
            return subreddit_obj
            
        except requests.RequestException as e:
            print(f"Error fetching metadata for r/{subreddit}: {e}")
            return None

