"""Reddit platform adapter using public JSON endpoints."""

import os
import time
import random
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import requests
import re
from urllib.parse import urlparse

from .base import PlatformAdapter
from ..models.post import Post
from ..models.subreddit import Subreddit
from ..models.comment import Comment


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
        time_filter: Optional[str] = None,
    ) -> Tuple[List[Post], Optional[str]]:
        """
        Fetch posts from a subreddit.
        
        Args:
            source: Subreddit name (with or without r/ prefix)
            sort: Sort order ("new", "hot", "top", "rising")
            limit: Maximum posts per page (max 100)
            after: Pagination token for next page
            time_filter: Time period for 'top' sort ("hour", "day", "week", "month", "year", "all")
        
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
        if time_filter and sort == "top":
            params["t"] = time_filter
        
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

    def fetch_thread(
        self,
        permalink: str,
        limit: int = 500,
    ) -> Tuple[Optional[Post], List[Comment], Optional[Dict[str, Any]]]:
        """
        Fetch a Reddit thread (post + comments) from a permalink.
        
        Args:
            permalink: Reddit permalink (e.g., /r/subreddit/comments/post_id/title/)
            limit: Maximum comments to fetch
        
        Returns:
            Tuple of (Post object, list of Comment objects, raw post data dict for image extraction)
        """
        # Normalize permalink
        if permalink.startswith("http"):
            # Extract path from URL
            parsed = urlparse(permalink)
            permalink = parsed.path
        
        if not permalink.startswith("/"):
            permalink = "/" + permalink
        
        # Remove trailing slash if present
        permalink = permalink.rstrip("/")
        
        # Add .json suffix
        url = f"https://www.reddit.com{permalink}.json"
        params = {"limit": limit, "raw_json": 1}
        
        if self.mock:
            return self._fetch_thread_mock(permalink)
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Reddit returns array: [0] = post listing, [1] = comments listing
            if not isinstance(data, list) or len(data) < 2:
                print(f"Unexpected response format for {permalink}")
                return None, [], None
            
            # Parse post from first item
            post_listing = data[0]
            post_children = post_listing.get("data", {}).get("children", [])
            if not post_children:
                print(f"No post found in thread {permalink}")
                return None, [], None
            
            post_data = post_children[0].get("data", {})
            raw_post_data = post_data.copy()  # Keep raw data for image extraction
            
            post = Post(
                id=post_data.get("id"),
                title=post_data.get("title", ""),
                created_utc=datetime.fromtimestamp(post_data.get("created_utc", 0)),
                score=post_data.get("score", 0),
                num_comments=post_data.get("num_comments", 0),
                upvote_ratio=post_data.get("upvote_ratio", 0.0),
                over_18=post_data.get("over_18", False),
                url=post_data.get("url", ""),
                selftext=post_data.get("selftext", ""),
                author=post_data.get("author"),
                subreddit=post_data.get("subreddit", ""),
                permalink=post_data.get("permalink"),
            )
            
            # Parse comments from second item
            comments_listing = data[1]
            comments = self._parse_comments_tree(
                comments_listing.get("data", {}).get("children", []),
                post.id,
                post.author,
                depth=0
            )
            
            self._delay()
            return post, comments, raw_post_data
            
        except requests.RequestException as e:
            print(f"Error fetching thread {permalink}: {e}")
            return None, [], None
        except Exception as e:
            print(f"Error parsing thread {permalink}: {e}")
            return None, [], None
    
    def _parse_comments_tree(
        self,
        children: List[Dict[str, Any]],
        link_id: str,
        op_author: Optional[str],
        depth: int = 0
    ) -> List[Comment]:
        """Recursively parse Reddit comments tree."""
        comments = []
        
        for child in children:
            if child.get("kind") != "t1":  # t1 = comment, t3 = post, more = MoreComments
                if child.get("kind") == "more":
                    # Skip "load more comments" placeholders for now
                    continue
                continue
            
            comment_data = child.get("data", {})
            
            # Skip deleted/removed comments
            if comment_data.get("body") in ["[deleted]", "[removed]"]:
                body = ""
            else:
                body = comment_data.get("body", "")
            
            comment = Comment(
                id=comment_data.get("id"),
                body=body,
                author=comment_data.get("author"),
                created_utc=datetime.fromtimestamp(comment_data.get("created_utc", 0)),
                score=comment_data.get("score", 0),
                ups=comment_data.get("ups", 0),
                downs=comment_data.get("downs", 0),
                parent_id=comment_data.get("parent_id"),
                link_id=link_id,
                depth=depth,
                is_submitter=comment_data.get("is_submitter", False) or (
                    comment_data.get("author") == op_author
                ),
                permalink=comment_data.get("permalink"),
            )
            comments.append(comment)
            
            # Recursively parse replies
            if comment_data.get("replies") and isinstance(comment_data["replies"], dict):
                replies_children = comment_data["replies"].get("data", {}).get("children", [])
                if replies_children:
                    comments.extend(
                        self._parse_comments_tree(
                            replies_children,
                            link_id,
                            op_author,
                            depth=depth + 1
                        )
                    )
        
        return comments
    
    def extract_all_images(self, post: Post, post_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Extract all image URLs from a post, including gallery posts.
        
        Args:
            post: Post object
            post_data: Optional raw post data from Reddit API (for gallery support)
        
        Returns:
            List of image URLs
        """
        images = []
        
        # Check if it's a gallery post
        if post_data and post_data.get("is_gallery"):
            gallery_data = post_data.get("gallery_data", {})
            media_metadata = post_data.get("media_metadata", {})
            
            items = gallery_data.get("items", [])
            for item in items:
                media_id = item.get("media_id")
                if media_id and media_id in media_metadata:
                    metadata = media_metadata[media_id]
                    # Gallery images are usually jpg or png
                    if metadata.get("status") == "valid":
                        # Try to get the source image
                        s = metadata.get("s", {})
                        image_url = s.get("u") or s.get("gif")
                        if image_url:
                            # Replace &amp; with &
                            image_url = image_url.replace("&amp;", "&")
                            images.append(image_url)
                        else:
                            # Fallback to i.redd.it URL
                            ext = metadata.get("m", "jpg").split("/")[-1]
                            images.append(f"https://i.redd.it/{media_id}.{ext}")
        
        # Check if main URL is an image
        if post.url:
            # Check for common image domains
            if any(domain in post.url for domain in ["i.redd.it", "i.imgur.com", "imgur.com"]):
                # Handle imgur albums and direct links
                if "imgur.com/a/" in post.url or "imgur.com/gallery/" in post.url:
                    # Album - would need imgur API to get all images
                    # For now, skip albums or handle separately
                    pass
                elif "imgur.com" in post.url and not post.url.endswith((".jpg", ".jpeg", ".png", ".gif")):
                    # Direct imgur link without extension, add .jpg
                    if not any(post.url.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                        images.append(post.url + ".jpg")
                else:
                    images.append(post.url)
            
            # Check for preview images in selftext or other fields
            # Reddit sometimes embeds images in markdown
            
        # Extract images from selftext markdown
        if post.selftext:
            # Look for markdown image links: ![alt](url)
            markdown_images = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', post.selftext)
            images.extend(markdown_images)
            
            # Look for direct image URLs in text
            url_pattern = r'(https?://[^\s\)]+\.(?:jpg|jpeg|png|gif|webp))'
            direct_images = re.findall(url_pattern, post.selftext, re.IGNORECASE)
            images.extend(direct_images)
        
        # Deduplicate while preserving order
        seen = set()
        unique_images = []
        for img in images:
            if img and img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images
    
    def extract_images_from_comments(self, comments: List[Comment]) -> List[Dict[str, str]]:
        """
        Extract image URLs from comment bodies.
        
        Args:
            comments: List of Comment objects
        
        Returns:
            List of dicts with 'url' and 'comment_id'
        """
        comment_images = []
        url_pattern = r'(https?://[^\s\)]+\.(?:jpg|jpeg|png|gif|webp))'
        
        for comment in comments:
            if not comment.body:
                continue
            
            # Look for markdown image links: ![alt](url)
            markdown_images = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', comment.body)
            comment_images.extend([{"url": url, "comment_id": comment.id, "author": comment.author} for url in markdown_images])
            
            # Look for direct image URLs
            direct_images = re.findall(url_pattern, comment.body, re.IGNORECASE)
            comment_images.extend([{"url": url, "comment_id": comment.id, "author": comment.author} for url in direct_images])
        
        return comment_images
    
    def _fetch_thread_mock(self, permalink: str) -> Tuple[Optional[Post], List[Comment], Optional[Dict[str, Any]]]:
        """Return mock thread for testing."""
        now = datetime.utcnow()
        post = Post(
            id="mock_thread1",
            title="[Mock] Test thread with comments",
            created_utc=now,
            score=100,
            num_comments=3,
            upvote_ratio=0.95,
            over_18=False,
            url="https://i.redd.it/mockimage.jpg",
            selftext="Mock post body text",
            author="mock_op",
            subreddit="lululemon",
            permalink=permalink,
        )
        
        comments = [
            Comment(
                id="comment1",
                body="This is a mock comment",
                author="mock_user1",
                created_utc=now,
                score=10,
                ups=10,
                downs=0,
                parent_id=f"t3_{post.id}",
                link_id=f"t3_{post.id}",
                depth=0,
                is_submitter=False,
            ),
            Comment(
                id="comment2",
                body="OP here - here's more context!",
                author="mock_op",
                created_utc=now,
                score=25,
                ups=25,
                downs=0,
                parent_id=f"t3_{post.id}",
                link_id=f"t3_{post.id}",
                depth=0,
                is_submitter=True,
            ),
        ]
        
        time.sleep(1)
        raw_post_data = {
            "is_gallery": False,
            "url": post.url,
        }
        return post, comments, raw_post_data


