"""Image hashing utilities for duplicate detection."""

import hashlib
import requests
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False


def compute_sha256_hash(image_bytes: bytes) -> str:
    """
    Compute SHA-256 hash of image bytes for exact duplicate detection.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        SHA-256 hash as hex string
    """
    return hashlib.sha256(image_bytes).hexdigest()


def compute_dhash(image_bytes: bytes) -> Optional[str]:
    """
    Compute perceptual hash (dHash) for near-duplicate detection.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        dHash as hex string, or None if imagehash not available or error
    """
    if not IMAGEHASH_AVAILABLE:
        return None
    
    try:
        img = Image.open(BytesIO(image_bytes))
        hash_value = imagehash.dhash(img)
        return str(hash_value)
    except Exception:
        return None


def download_and_hash_image(
    url: str,
    timeout: int = 10,
    max_size_mb: int = 10
) -> Tuple[Optional[str], Optional[str], Optional[bytes]]:
    """
    Download image and compute both SHA-256 and dHash.
    
    Args:
        url: Image URL to download
        timeout: Request timeout in seconds
        max_size_mb: Maximum image size in MB
        
    Returns:
        Tuple of (sha256_hash, dhash, image_bytes) or (None, None, None) on error
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FeedBot/1.0)'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            return None, None, None
        
        # Check size
        content_length = response.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > max_size_mb:
                return None, None, None
        
        # Download image
        image_bytes = b''
        for chunk in response.iter_content(chunk_size=8192):
            image_bytes += chunk
            if len(image_bytes) > max_size_mb * 1024 * 1024:
                return None, None, None
        
        if not image_bytes:
            return None, None, None
        
        # Compute hashes
        sha256 = compute_sha256_hash(image_bytes)
        dhash = compute_dhash(image_bytes)
        
        return sha256, dhash, image_bytes
        
    except Exception:
        return None, None, None


def hash_image_url(url: str, timeout: int = 10) -> Tuple[Optional[str], Optional[str]]:
    """
    Hash an image from URL without downloading full image (for quick checks).
    Downloads minimal data to compute hash.
    
    Args:
        url: Image URL
        timeout: Request timeout
        
    Returns:
        Tuple of (sha256_hash, dhash) or (None, None) on error
    """
    sha256, dhash, _ = download_and_hash_image(url, timeout=timeout)
    return sha256, dhash








