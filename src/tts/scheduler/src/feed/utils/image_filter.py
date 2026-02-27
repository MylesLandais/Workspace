"""Image URL filtering utilities."""

import re
from typing import List

from ..models.post import Post


def is_image_url(url: str, include_galleries: bool = True) -> bool:
    """
    Check if URL points to an image or image gallery.
    
    Args:
        url: URL to check
        include_galleries: If True, include Reddit galleries as image posts
    
    Returns:
        True if URL appears to be an image or image gallery
    """
    if not url:
        return False
    
    # Image file extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.avif']
    url_lower = url.lower()
    
    # Check for direct image URLs
    if any(url_lower.endswith(ext) for ext in image_extensions):
        return True
    
    # Check for Reddit image hosting
    if 'i.redd.it' in url_lower or 'preview.redd.it' in url_lower:
        return True
    
    # Check for Reddit galleries (multi-image posts)
    if include_galleries and 'reddit.com/gallery/' in url_lower:
        return True
    
    # Check for Imgur direct image links
    if 'imgur.com' in url_lower:
        # Exclude albums and galleries
        if '/a/' in url_lower or '/gallery/' in url_lower:
            return False
        # Check for image extension in URL
        if any(ext in url_lower for ext in image_extensions):
            return True
        # imgur.com/XXXXX format might be an image (single image)
        imgur_id_pattern = r'imgur\.com/([a-zA-Z0-9]+)$'
        if re.search(imgur_id_pattern, url_lower):
            return True
    
    return False


def filter_image_posts(posts: List[Post], include_galleries: bool = True) -> List[Post]:
    """
    Filter posts to only include image posts.
    
    Args:
        posts: List of posts to filter
        include_galleries: If True, include Reddit galleries as image posts
    
    Returns:
        List of posts that have image URLs or galleries
    """
    return [p for p in posts if is_image_url(p.url, include_galleries=include_galleries)]

