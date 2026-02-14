import os
import hashlib
import requests
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from feed.storage.minio_connection import get_minio_connection
from feed.storage.valkey_connection import get_valkey_connection


class ModelImageCache:
    """Manages image caching with MinIO storage and Redis/Valkey tracking."""
    
    def __init__(
        self,
        bucket_name: str = "model-images",
        cache_ttl_hours: int = 24,
        use_local_fallback: bool = True,
    ):
        """
        Initialize image cache.
        
        Args:
            bucket_name: MinIO bucket name for images
            cache_ttl_hours: How long to consider cache valid
            use_local_fallback: Fall back to local disk if MinIO fails
        """
        self.bucket_name = bucket_name
        self.cache_ttl = cache_ttl_hours
        self.use_local_fallback = use_local_fallback
        
        # Initialize storage connections
        self.minio = get_minio_connection()
        self.valkey = get_valkey_connection()
        
        # Local fallback cache directory
        self.local_cache_dir = Path("cache/model_images")
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure MinIO bucket exists
        self.minio.ensure_bucket(self.bucket_name)
    
    def compute_sha256(self, data: bytes) -> str:
        """Compute SHA-256 hash of image data."""
        return hashlib.sha256(data).hexdigest()
    
    def get_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL."""
        return f"img:{self.bucket_name}:{url}"
    
    def is_cached(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if image is cached.
        
        Returns:
            Tuple of (is_cached, storage_location/presigned_url)
        """
        cache_key = self.get_cache_key(url)
        
        try:
            # Check Valkey first (fast)
            cached = self.valkey.client.get(cache_key)
            if cached:
                return True, cached
            
            # Check MinIO for object existence
            # Use SHA-256 of URL as object name for deduplication
            sha256 = hashlib.sha256(url.encode()).hexdigest()
            object_name = f"images/{sha256}"
            
            if self.minio.object_exists(self.bucket_name, object_name):
                # Generate presigned URL for serving
                presigned_url = self.minio.generate_presigned_url(
                    self.bucket_name, object_name, expires_seconds=86400  # 24 hours
                )
                return True, presigned_url
            
        except Exception as e:
            print(f"Warning: Cache check failed, using fallback: {e}")
        
        # Check local fallback cache
        if self.use_local_fallback:
            local_path = self.local_cache_dir / f"{sha256[:16]}.jpg"
            if local_path.exists():
                return True, f"file://{local_path.absolute()}"
        
        return False, None
    
    def download_and_cache(
        self,
        url: str,
        max_size_mb: int = 10,
        timeout: int = 30,
    ) -> Tuple[bool, Optional[str]]:
        """
        Download image from URL and cache it in MinIO/local.
        
        Args:
            url: Image URL to download
            max_size_mb: Maximum file size in MB
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (success, storage_location/presigned_url)
        """
        # Check if already cached
        is_cached, cached_url = self.is_cached(url)
        if is_cached:
            print(f"    ✓ Image cached: {url[:60]}...")
            return True, cached_url
        
        # Download image
        try:
            print(f"    ⬇ Downloading: {url[:60]}...")
            headers = {"User-Agent": "Mozilla/5.0 (compatible; RedditCrawler/1.0)"}
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get("content-type", "image/jpeg")
            
            # Download in chunks to handle large files
            image_data = b""
            downloaded_bytes = 0
            max_size = max_size_mb * 1024 * 1024
            
            for chunk in response.iter_content(chunk_size=8192):
                downloaded_bytes += len(chunk)
                if downloaded_bytes > max_size:
                    print(f"    ✗ Image too large (> {max_size_mb}MB), skipping")
                    return False, None
                image_data += chunk
            
            # Compute hashes
            sha256 = hashlib.sha256(image_data).hexdigest()
            object_name = f"images/{sha256}"
            
            # Try to upload to MinIO
            success = False
            storage_location = None
            
            if content_type.startswith("image/"):
                uploaded = self.minio.upload_bytes(
                    self.bucket_name,
                    object_name,
                    image_data,
                    content_type=content_type,
                )
                
                if uploaded:
                    # Generate presigned URL
                    presigned_url = self.minio.generate_presigned_url(
                        self.bucket_name, object_name, expires_seconds=86400
                    )
                    storage_location = presigned_url
                    success = True
                    
                    # Cache in Valkey
                    cache_key = self.get_cache_key(url)
                    self.valkey.client.setex(cache_key, 86400, presigned_url)  # 24 hours TTL
                    print(f"    ✓ Uploaded to MinIO and cached")
            
            # Fallback to local storage if MinIO failed
            if not success and self.use_local_fallback:
                local_path = self.local_cache_dir / f"{sha256[:16]}.jpg"
                local_path.write_bytes(image_data)
                storage_location = f"file://{local_path.absolute()}"
                success = True
                print(f"    ✓ Cached locally (MinIO unavailable)")
            
            return success, storage_location
            
        except requests.RequestException as e:
            print(f"    ✗ Download failed: {e}")
            return False, None
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False, None
    
    def batch_cache_images(
        self,
        urls: list[str],
        max_concurrent: int = 5,
        max_size_mb: int = 10,
    ) -> dict[str, Tuple[bool, Optional[str]]]:
        """
        Cache multiple images from URLs.
        
        Args:
            urls: List of image URLs
            max_concurrent: Maximum concurrent downloads
            max_size_mb: Maximum file size per image
            
        Returns:
            Dictionary mapping URL to (success, storage_location)
        """
        results = {}
        
        for url in urls:
            success, location = self.download_and_cache(url, max_size_mb=max_size_mb)
            results[url] = (success, location)
        
        # Summary
        successful = sum(1 for s, _ in results.values() if s)
        print(f"\nCache summary: {successful}/{len(urls)} successful")
        
        return results
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            # Get all cache keys
            pattern = f"img:{self.bucket_name}:*"
            keys = self.valkey.client.keys(pattern)
            
            # Get MinIO bucket stats (approximate)
            # Note: MinIO doesn't have a simple count API, using cache key count
            
            return {
                "bucket_name": self.bucket_name,
                "cached_urls": len(keys) if keys else 0,
                "local_cache_dir": str(self.local_cache_dir),
                "cache_ttl_hours": self.cache_ttl,
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def invalidate_url(self, url: str) -> bool:
        """
        Invalidate cache for a specific URL.
        
        Returns:
            True if invalidation successful
        """
        cache_key = self.get_cache_key(url)
        
        try:
            self.valkey.client.delete(cache_key)
            
            # Optionally delete from MinIO (not recommended, URLs expire)
            
            return True
        except Exception as e:
            print(f"Error invalidating cache: {e}")
            return False
    
    def clear_local_fallback(self) -> int:
        """Clear local fallback cache and return freed bytes."""
        try:
            total_size = 0
            for file_path in self.local_cache_dir.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            # Delete all files
            for file_path in self.local_cache_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            
            return total_size
        except Exception as e:
            print(f"Error clearing local cache: {e}")
            return 0


def get_model_image_cache() -> ModelImageCache:
    """Get or create global ModelImageCache instance."""
    global _model_image_cache
    if "_model_image_cache" not in globals():
        _model_image_cache = ModelImageCache()
    return _model_image_cache
