"""
Simple Valkey cache for WD14 tagging state.
Tracks discovered images, cached tags, and failed retries.
"""

import json
import time
from typing import Dict, List, Optional

from src.feed.storage.valkey_connection import get_valkey_connection


class WD14Cache:
    """Simple Valkey cache for WD14 processing state."""

    PREFIX_TAGS = "wd14:tags"
    PREFIX_FAILED = "wd14:failed"
    PREFIX_DISCOVERED = "wd14:discovered"
    CACHE_TTL = 7 * 24 * 3600  # 7 days

    def __init__(self):
        """Initialize cache connection."""
        self.client = get_valkey_connection().client

    def cache_tags(self, image_sha256: str, tags_json: str) -> None:
        """Cache WD14 tags result.

        Args:
            image_sha256: Image SHA256
            tags_json: JSON string of WD14Result
        """
        tags_key = f"{self.PREFIX_TAGS}:{image_sha256}"
        self.client.set(tags_key, tags_json, ex=self.CACHE_TTL)

    def get_cached_tags(self, image_sha256: str) -> Optional[str]:
        """Retrieve cached WD14 tags.

        Args:
            image_sha256: Image SHA256

        Returns:
            JSON string of WD14Result or None
        """
        tags_key = f"{self.PREFIX_TAGS}:{image_sha256}"
        return self.client.get(tags_key)

    def mark_failed(self, image_sha256: str, bucket_name: str, s3_uri: str, error: str) -> None:
        """Track failed processing for retry.

        Args:
            image_sha256: Image SHA256
            bucket_name: S3 bucket
            s3_uri: S3 URI
            error: Error message
        """
        failed_key = f"{self.PREFIX_FAILED}:{image_sha256}"
        failed_data = {
            "image_sha256": image_sha256,
            "bucket_name": bucket_name,
            "s3_uri": s3_uri,
            "error": error,
            "failed_at": time.time(),
        }
        self.client.set(failed_key, json.dumps(failed_data), ex=self.CACHE_TTL)

    def get_failed_jobs(self, older_than_hours: int = 24) -> List[Dict]:
        """Get failed jobs older than cutoff for retry.

        Args:
            older_than_hours: Only return jobs failed longer than this

        Returns:
            List of failed job dicts
        """
        cutoff_time = time.time() - (older_than_hours * 3600)
        cursor = "0"
        failed_jobs = []

        while True:
            cursor, keys = self.client.scan(cursor, match=f"{self.PREFIX_FAILED}:*", count=100)
            for key in keys:
                data = self.client.get(key)
                if data:
                    job = json.loads(data)
                    if job["failed_at"] < cutoff_time:
                        failed_jobs.append(job)

            if cursor == "0":
                break

        return failed_jobs

    def clear_failed(self, image_sha256: str) -> None:
        """Clear failed marker for image (after successful processing).

        Args:
            image_sha256: Image SHA256
        """
        failed_key = f"{self.PREFIX_FAILED}:{image_sha256}"
        self.client.delete(failed_key)

    def discover_bucket_images(self, bucket_name: str, images: List[Dict]) -> int:
        """Register discovered images in bucket.

        Args:
            bucket_name: S3 bucket name
            images: List of dicts with {sha256, s3_uri, prefix}

        Returns:
            Number of newly discovered images
        """
        discovered_key = f"{self.PREFIX_DISCOVERED}:{bucket_name}"
        newly_discovered = 0

        for image_info in images:
            sha256 = image_info["sha256"]
            # Check if already cached or failed
            if self.get_cached_tags(sha256) is None and self._get_failed(sha256) is None:
                newly_discovered += 1

        # Store discovery metadata
        discovery_data = {
            "bucket_name": bucket_name,
            "discovered_count": len(images),
            "newly_discovered": newly_discovered,
            "discovered_at": time.time(),
        }
        self.client.set(discovered_key, json.dumps(discovery_data), ex=self.CACHE_TTL)

        return newly_discovered

    def _get_failed(self, image_sha256: str) -> Optional[Dict]:
        """Get failed job data if exists."""
        failed_key = f"{self.PREFIX_FAILED}:{image_sha256}"
        data = self.client.get(failed_key)
        return json.loads(data) if data else None

    def get_cache_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dict with counts
        """
        cursor = "0"
        cached_count = 0
        failed_count = 0

        while True:
            cursor, keys = self.client.scan(cursor, match=f"{self.PREFIX_TAGS}:*", count=100)
            cached_count += len(keys)
            if cursor == "0":
                break

        cursor = "0"
        while True:
            cursor, keys = self.client.scan(cursor, match=f"{self.PREFIX_FAILED}:*", count=100)
            failed_count += len(keys)
            if cursor == "0":
                break

        return {
            "cached_tags": cached_count,
            "failed_jobs": failed_count,
        }
