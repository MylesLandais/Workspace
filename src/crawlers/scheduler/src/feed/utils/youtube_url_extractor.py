"""Utility to extract YouTube URLs from text content."""

import re
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs


def extract_youtube_urls(text: str) -> List[Dict[str, str]]:
    """
    Extract all YouTube URLs from text content.
    
    Handles various formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    
    Args:
        text: Text content to search (comment body, post selftext, etc.)
    
    Returns:
        List of dicts with keys: 'url', 'video_id', 'full_url'
    """
    if not text:
        return []
    
    patterns = [
        # Standard YouTube URLs
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # Short youtu.be URLs
        r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
        # Mobile YouTube URLs
        r'https?://m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # YouTube URLs with additional parameters
        r'https?://(?:www\.)?youtube\.com/watch\?.*?v=([a-zA-Z0-9_-]{11})',
    ]
    
    found_urls = []
    seen = set()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            video_id = match.group(1)
            full_url = match.group(0)
            
            # Skip if we've already seen this video ID
            if video_id in seen:
                continue
            seen.add(video_id)
            
            # Normalize to standard YouTube URL
            normalized_url = f"https://www.youtube.com/watch?v={video_id}"
            
            found_urls.append({
                'url': full_url,
                'video_id': video_id,
                'full_url': normalized_url,
                'short_url': f"https://youtu.be/{video_id}",
            })
    
    return found_urls


def parse_youtube_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a YouTube URL and extract video ID.
    
    Args:
        url: YouTube URL string
    
    Returns:
        Dict with 'video_id', 'full_url', 'short_url', or None if invalid
    """
    # Try to extract video ID from various formats
    patterns = [
        r'[?&]v=([a-zA-Z0-9_-]{11})',  # Standard watch URL
        r'youtu\.be/([a-zA-Z0-9_-]{11})',  # Short URL
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',  # Embed URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            return {
                'video_id': video_id,
                'full_url': f"https://www.youtube.com/watch?v={video_id}",
                'short_url': f"https://youtu.be/{video_id}",
            }
    
    return None


def extract_video_id_from_url(url: str) -> Optional[str]:
    """
    Extract video ID from a YouTube URL.
    
    Args:
        url: YouTube URL
    
    Returns:
        Video ID or None
    """
    parsed = parse_youtube_url(url)
    if parsed:
        return parsed.get('video_id')
    return None







