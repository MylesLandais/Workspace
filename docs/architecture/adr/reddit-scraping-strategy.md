# Reddit Scraping Strategy

## Status

Accepted

## Context

We need to ingest content from Reddit subreddits for image discovery and feed aggregation. Reddit provides public JSON endpoints that don't require API authentication, making them ideal for automated content collection.

We need a strategy that:
- Works reliably without API authentication
- Respects rate limits and avoids being blocked
- Extracts images, metadata, and post information
- Handles NSFW content appropriately
- Provides consistent data structure

## Decision

Use Reddit's public JSON API endpoints:
1. **JSON endpoints** (`/r/{subreddit}/{sort}.json`) for structured data access
2. **Rate limiting** with configurable delays between requests
3. **User-agent headers** required by Reddit's ToS
4. **Request spacing** with random delays to appear more human-like
5. **Error handling** with retry logic for transient failures

## Rationale

**JSON API Advantages**: Structured data format, no HTML parsing required, faster and more reliable than scraping, official endpoint supported by Reddit.

**No Authentication Required**: Public JSON endpoints work without API keys, simplifying deployment and maintenance.

**Rate Limiting**: Prevents IP bans and respects Reddit's infrastructure. Configurable delays allow tuning based on usage patterns.

**User-Agent Headers**: Required by Reddit's Terms of Service for automated access. Using descriptive user-agent helps with compliance.

**Simple and Maintainable**: JSON parsing is more reliable than HTML scraping and less likely to break when Reddit updates their UI.

## Consequences

**Positive**:
- Works without API authentication
- Simple JSON parsing, no HTML scraping complexity
- Fast and reliable data extraction
- Less likely to break when Reddit updates UI
- Lower resource usage (no headless browsers)
- Official endpoint supported by Reddit

**Negative**:
- Limited to public data (no private subreddits)
- Rate limits still apply (though more lenient than authenticated API)
- JSON structure may change (though less likely than HTML)

**Neutral**:
- Requires monitoring for HTML structure changes
- May need to adjust scraping patterns over time
- Legal/ToS considerations for web scraping

## Alternatives Considered

**HTML Scraping (old.reddit.com)**: Would work but requires HTML parsing, more fragile, and slower than JSON endpoints.

**Headless Browser (Playwright)**: Would work for new Reddit but is resource-intensive, slow, and requires JavaScript rendering.

**Reddit Official API**: Requires authentication and has stricter rate limits. Public JSON endpoints are sufficient for our use case.

**Third-Party Reddit APIs**: Services like Pushshift or RedditArchive, but they may have limitations, costs, or reliability issues.

## Implementation Notes

### Reddit JSON API Implementation

```python
import requests
from datetime import datetime
from typing import List, Optional, Tuple

class RedditAdapter:
    """Reddit adapter using public JSON endpoints."""
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
    ):
        self.user_agent = user_agent or "feed/1.0 (by /u/feeduser)"
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headers = {"User-Agent": self.user_agent}
    
    def fetch_posts(
        self,
        source: str,
        sort: str = "new",
        limit: int = 100,
        after: Optional[str] = None,
    ) -> Tuple[List[dict], Optional[str]]:
        """Fetch posts from a subreddit using JSON API."""
        subreddit = source.replace("r/", "").replace("/r/", "")
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
        params = {"limit": min(limit, 100)}
        if after:
            params["after"] = after
        
        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        children = data.get("data", {}).get("children", [])
        next_after = data.get("data", {}).get("after")
        
        for child in children:
            post_data = child.get("data", {})
            post = {
                "id": post_data.get("id"),
                "title": post_data.get("title", ""),
                "created_utc": datetime.fromtimestamp(post_data.get("created_utc", 0)),
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0.0),
                "over_18": post_data.get("over_18", False),
                "url": post_data.get("url", ""),
                "selftext": post_data.get("selftext", ""),
                "author": post_data.get("author"),
                "subreddit": subreddit,
                "permalink": post_data.get("permalink"),
            }
            posts.append(post)
        
        # Add delay between requests
        time.sleep(random.uniform(self.delay_min, self.delay_max))
        
        return posts, next_after
```

### Media Extraction from Reddit Posts

```python
def extract_media(post_element) -> dict:
    """Extract images, videos, galleries from Reddit post."""
    media = {
        "images": [],
        "videos": [],
        "gallery": False
    }
    
    # Direct image link
    if post_element.select_one('a.thumbnail img'):
        img_url = post_element.select_one('a.thumbnail img').get('src', '')
        if 'preview.redd.it' in img_url or 'i.redd.it' in img_url:
            media["images"].append(normalize_reddit_image_url(img_url))
    
    # Gallery post
    if post_element.select('.gallery'):
        gallery_items = post_element.select('.gallery img')
        for item in gallery_items:
            media["images"].append(normalize_reddit_image_url(item.get('src', '')))
        media["gallery"] = True
    
    # Video post
    if post_element.select_one('video source'):
        video_url = post_element.select_one('video source').get('src', '')
        media["videos"].append(video_url)
    
    # External link (imgur, etc.)
    external_url = post_element.select_one('a.title').get('href', '') if post_element.select_one('a.title') else ""
    if is_image_url(external_url):
        media["images"].append(external_url)
    
    return media

def normalize_reddit_image_url(url: str) -> str:
    """Convert Reddit preview URLs to full-size image URLs."""
    # Reddit preview URLs: https://preview.redd.it/xyz.jpg?width=1080&format=pjpg
    # Full URLs: https://i.redd.it/xyz.jpg
    if 'preview.redd.it' in url:
        # Extract image ID and convert to i.redd.it
        image_id = url.split('/')[-1].split('?')[0]
        return f"https://i.redd.it/{image_id}"
    return url
```

### Rate Limiting Strategy

The implementation uses configurable delays between requests rather than centralized rate limiting:

```python
import time
import random

def _delay(self, delay_min: float = 2.0, delay_max: float = 5.0) -> None:
    """Add human-like delay between requests."""
    delay = random.uniform(delay_min, delay_max)
    time.sleep(delay)
```

This approach:
- Simulates human browsing patterns
- Avoids centralized rate limit tracking overhead
- Configurable per adapter instance
- Works well for moderate request volumes

For higher volumes, consider implementing Valkey-based distributed rate limiting:

```python
async def check_rate_limit(domain: str) -> bool:
    """Check if we can make a request to Reddit."""
    key = f"ratelimit:reddit:{domain}"
    
    # Get current count
    count = await valkey.incr(key)
    if count == 1:
        await valkey.expire(key, 60)  # 1 minute window
    
    # Reddit rate limit: ~60 requests per minute per IP
    # Be conservative: 30 requests per minute
    if count > 30:
        return False
    
    return True
```

### Cross-Post Detection

```python
def detect_crosspost(post_data: dict) -> dict:
    """Detect if post is a cross-post and extract original."""
    crosspost_info = {
        "is_crosspost": False,
        "original_subreddit": None,
        "original_url": None
    }
    
    # Check for cross-post indicators in title or metadata
    title = post_data.get("title", "")
    if "crosspost" in title.lower() or "[x-post]" in title.lower():
        crosspost_info["is_crosspost"] = True
    
    # Check for cross-post link in post content
    # Reddit cross-posts have specific URL patterns
    url = post_data.get("url", "")
    if "/r/" in url and "/comments/" in url:
        # Extract original subreddit from cross-post URL
        parts = url.split("/r/")
        if len(parts) > 1:
            crosspost_info["original_subreddit"] = parts[1].split("/")[0]
            crosspost_info["original_url"] = url
    
    return crosspost_info
```

### NSFW Handling

```python
def handle_nsfw_content(post_data: dict, user_preferences: dict) -> dict:
    """Handle NSFW content based on user preferences."""
    if post_data.get("nsfw", False):
        if not user_preferences.get("show_nsfw", False):
            return None  # Skip NSFW content
        
        # Blur thumbnail for NSFW content
        post_data["thumbnail_blurred"] = True
        post_data["requires_confirmation"] = True
    
    return post_data
```

### Error Handling and Retry Logic

```python
def fetch_posts_with_retry(
    self,
    source: str,
    sort: str = "new",
    limit: int = 100,
    max_retries: int = 3,
) -> Tuple[List[dict], Optional[str]]:
    """Fetch posts with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            return self.fetch_posts(source, sort, limit)
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch posts after {max_retries} attempts: {e}")
                raise
```

### Subreddit Metadata

```python
def fetch_source_metadata(self, source: str) -> Optional[dict]:
    """Fetch subreddit metadata using JSON API."""
    subreddit = source.replace("r/", "").replace("/r/", "")
    url = f"https://www.reddit.com/r/{subreddit}/about.json"
    
    try:
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        subreddit_data = data.get("data", {})
        return {
            "name": subreddit,
            "subscribers": subreddit_data.get("subscribers"),
            "created_utc": datetime.fromtimestamp(subreddit_data.get("created_utc", 0)),
            "description": subreddit_data.get("description"),
            "public_description": subreddit_data.get("public_description"),
        }
    except requests.RequestException as e:
        logger.error(f"Error fetching metadata for r/{subreddit}: {e}")
        return None
```

## References

- [ADR: Unified Ingestion Layer](./unified-ingestion-layer.md)
- [Reddit JSON API Documentation](https://www.reddit.com/dev/api)
- Implementation: `src/feed/platforms/reddit.py`

