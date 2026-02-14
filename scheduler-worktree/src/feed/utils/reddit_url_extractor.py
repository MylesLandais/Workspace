"""Utility to extract Reddit URLs from text content (comments, posts)."""

import re
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs


def extract_reddit_urls(text: str) -> List[Dict[str, str]]:
    """
    Extract all Reddit URLs from text content.
    
    Handles various formats:
    - https://www.reddit.com/r/subreddit/comments/post_id/title/
    - https://old.reddit.com/r/subreddit/comments/post_id/title/
    - /r/subreddit/comments/post_id/title/
    - reddit.com/r/subreddit/comments/post_id/title/
    
    Args:
        text: Text content to search (comment body, post selftext, etc.)
    
    Returns:
        List of dicts with keys: 'url', 'subreddit', 'post_id', 'permalink'
    """
    if not text:
        return []
    
    # Pattern for Reddit permalinks
    # Matches both new and old reddit, with or without protocol
    patterns = [
        # Full URLs (new reddit)
        r'https?://(?:www\.)?reddit\.com(/r/[^/]+/comments/[^/\s\)]+)',
        # Full URLs (old reddit)
        r'https?://old\.reddit\.com(/r/[^/]+/comments/[^/\s\)]+)',
        # Relative permalinks (already start with /r/)
        r'(/r/[^/]+/comments/[^/\s\)]+)',
        # Short URLs (redd.it)
        r'https?://redd\.it/([a-zA-Z0-9]+)',
    ]
    
    found_urls = []
    seen = set()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            url = match.group(0)
            
            # Skip if we've already seen this URL
            if url in seen:
                continue
            seen.add(url)
            
            # Parse the URL
            parsed = parse_reddit_url(url)
            if parsed:
                found_urls.append(parsed)
    
    return found_urls


def parse_reddit_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a Reddit URL and extract components.
    
    Args:
        url: Reddit URL string
    
    Returns:
        Dict with 'url', 'subreddit', 'post_id', 'permalink', or None if invalid
    """
    # Normalize URL
    if url.startswith('/'):
        # Relative permalink
        permalink = url
        full_url = f"https://www.reddit.com{permalink}"
    elif url.startswith('http'):
        # Full URL
        parsed_url = urlparse(url)
        permalink = parsed_url.path
        full_url = url
    elif 'redd.it' in url:
        # Short URL - extract post ID
        post_id = url.split('/')[-1].split('?')[0]
        # We can't get subreddit from short URL without fetching
        return {
            'url': url,
            'permalink': f'/comments/{post_id}',
            'post_id': post_id,
            'subreddit': None,  # Unknown from short URL
        }
    else:
        return None
    
    # Extract components from permalink
    # Format: /r/subreddit/comments/POST_ID/title/
    parts = permalink.strip('/').split('/')
    
    if len(parts) < 4 or parts[0] != 'r' or parts[2] != 'comments':
        return None
    
    subreddit = parts[1]
    post_id = parts[3]
    
    return {
        'url': full_url,
        'permalink': permalink.rstrip('/'),
        'post_id': post_id,
        'subreddit': subreddit,
    }


def extract_post_id_from_permalink(permalink: str) -> Optional[str]:
    """
    Extract post ID from a Reddit permalink.
    
    Args:
        permalink: Reddit permalink (e.g., /r/subreddit/comments/POST_ID/title/)
    
    Returns:
        Post ID or None
    """
    parsed = parse_reddit_url(permalink)
    if parsed:
        return parsed.get('post_id')
    return None


def extract_post_id_from_url(url: str) -> Optional[str]:
    """
    Extract post ID from a Reddit URL (full URL or permalink).
    
    Args:
        url: Reddit URL (e.g., https://www.reddit.com/r/subreddit/comments/POST_ID/title/)
    
    Returns:
        Post ID or None
    """
    parsed = parse_reddit_url(url)
    if parsed:
        return parsed.get('post_id')
    return None

