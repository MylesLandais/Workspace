"""
WD14 service - orchestrates image discovery, tagging, and storage.
Combines S3 scanning, batch processing, and Valkey/Neo4j caching.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from io import BytesIO
from PIL import Image

from src.image_captioning.wd14_tagger import WD14Tagger
from src.image_captioning.models import WD14Result
from src.feed.storage.minio_connection import get_minio_connection
from src.feed.services.wd14_cache import WD14Cache

logger = logging.getLogger(__name__)


class WD14Service:
    """Orchestrates WD14 tagging pipeline."""

    BATCH_SIZE = 32
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    def __init__(self):
        """Initialize service with tagger, cache, and S3 connection."""
        self.tagger = WD14Tagger()
        self.cache = WD14Cache()
        self.s3_conn = get_minio_connection()
        self.s3 = self.s3_conn.get_minio_client()

    def scan_bucket(self, bucket_name: str, prefix: str = "") -> Tuple[List[Dict], int]:
        """Discover images in S3 bucket.

        Args:
            bucket_name: S3 bucket to scan
            prefix: S3 prefix (optional)

        Returns:
            Tuple of (list of image dicts, count of new images)
        """
        logger.info(f"Scanning bucket {bucket_name} with prefix '{prefix}'")

        discovered_images = []
        new_count = 0

        try:
            # List all objects in bucket
            for obj in self.s3.list_objects(bucket_name, prefix=prefix, recursive=True):
                if not obj.is_dir:
                    key = obj.object_name
                    file_ext = Path(key).suffix.lower()

                    if file_ext not in self.SUPPORTED_FORMATS:
                        continue

                    # Compute SHA256 from object
                    sha256 = self._compute_object_hash(bucket_name, key)

                    # Check if already processed
                    if self.cache.get_cached_tags(sha256) is None:
                        new_count += 1
                        discovered_images.append({
                            "sha256": sha256,
                            "bucket_name": bucket_name,
                            "prefix": prefix,
                            "key": key,
                            "s3_uri": f"s3://{bucket_name}/{key}",
                        })

            logger.info(f"Found {len(discovered_images)} images ({new_count} new)")
            self.cache.discover_bucket_images(bucket_name, discovered_images)

            return discovered_images, new_count

        except Exception as e:
            logger.error(f"Error scanning bucket {bucket_name}: {e}")
            raise

    def process_batch(self, images: List[Dict], limit: Optional[int] = None) -> Dict:
        """Process batch of images with WD14 tagger.

        Args:
            images: List of image dicts from scan_bucket
            limit: Optional max images to process

        Returns:
            Dict with processing stats
        """
        if limit:
            images = images[:limit]

        total = len(images)
        success = 0
        failed = 0

        logger.info(f"Processing batch of {total} images")

        for i, image_dict in enumerate(images):
            try:
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{total}")

                # Download image from S3
                image = self._download_image(image_dict["bucket_name"], image_dict["key"])
                if not image:
                    failed += 1
                    self.cache.mark_failed(
                        image_dict["sha256"],
                        image_dict["bucket_name"],
                        image_dict["s3_uri"],
                        "Failed to download image"
                    )
                    continue

                # Tag with WD14
                result = self.tagger.tag_image(image, image_dict["sha256"])

                # Cache result
                result_json = json.dumps(result.to_dict())
                self.cache.cache_tags(image_dict["sha256"], result_json)
                self.cache.clear_failed(image_dict["sha256"])

                success += 1

                # Store in Neo4j (optional, async)
                self._store_in_neo4j(image_dict["sha256"], result)

            except Exception as e:
                logger.error(f"Error processing {image_dict['s3_uri']}: {e}")
                failed += 1
                self.cache.mark_failed(
                    image_dict["sha256"],
                    image_dict["bucket_name"],
                    image_dict["s3_uri"],
                    str(e)
                )

        logger.info(f"Batch complete: {success} success, {failed} failed")

        return {
            "total": total,
            "success": success,
            "failed": failed,
        }

    def retry_failed(self, older_than_hours: int = 24) -> Dict:
        """Retry failed jobs.

        Args:
            older_than_hours: Only retry jobs failed longer than this

        Returns:
            Dict with retry stats
        """
        failed_jobs = self.cache.get_failed_jobs(older_than_hours)
        logger.info(f"Retrying {len(failed_jobs)} failed jobs")

        # Reprocess as batch
        results = self.process_batch(failed_jobs)

        return {
            "retried": len(failed_jobs),
            **results,
        }

    def get_tags(self, image_sha256: str) -> Optional[WD14Result]:
        """Retrieve cached WD14 tags for image.

        Args:
            image_sha256: Image SHA256 hash

        Returns:
            WD14Result or None if not tagged
        """
        tags_json = self.cache.get_cached_tags(image_sha256)
        if not tags_json:
            return None

        return WD14Result.from_dict(json.loads(tags_json))

    def get_stats(self) -> Dict:
        """Get tagging statistics.

        Returns:
            Dict with cache stats
        """
        return self.cache.get_cache_stats()

    # Private helpers

    def _compute_object_hash(self, bucket_name: str, key: str) -> str:
        """Compute SHA256 of S3 object.

        Args:
            bucket_name: S3 bucket
            key: Object key

        Returns:
            SHA256 hex string
        """
        try:
            response = self.s3.get_object(bucket_name, key)
            data = response.read()
            return hashlib.sha256(data).hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {bucket_name}/{key}: {e}")
            return ""

    def _download_image(self, bucket_name: str, key: str) -> Optional[Image.Image]:
        """Download image from S3 and convert to PIL Image.

        Args:
            bucket_name: S3 bucket
            key: Object key

        Returns:
            PIL Image or None if download fails
        """
        try:
            response = self.s3.get_object(bucket_name, key)
            data = response.read()
            image = Image.open(BytesIO(data))
            return image
        except Exception as e:
            logger.error(f"Error downloading {bucket_name}/{key}: {e}")
            return None

    def _store_in_neo4j(self, image_sha256: str, result: WD14Result) -> None:
        """Store WD14 result in Neo4j (optional async operation).

        Args:
            image_sha256: Image SHA256
            result: WD14Result to store
        """
        try:
            from src.feed.storage.neo4j_connection import get_neo4j_connection

            driver = get_neo4j_connection()

            with driver.session() as session:
                # Create WD14Result node
                session.run("""
                    MERGE (r:WD14Result {image_sha256: $sha256})
                    SET r.rating = $rating,
                        r.processed_at = datetime($processed_at),
                        r.model_version = $model_version
                """,
                    sha256=image_sha256,
                    rating=result.rating,
                    processed_at=result.processed_at.isoformat(),
                    model_version=result.model_version,
                )

                # Create and link tags
                for tag in result.get_all_tags():
                    session.run("""
                        MERGE (t:WD14Tag {name: $name, category: $category})
                        WITH t
                        MATCH (r:WD14Result {image_sha256: $sha256})
                        MERGE (r)-[:HAS_TAG {confidence: $confidence}]->(t)
                    """,
                        name=tag.name,
                        category=tag.category.value,
                        sha256=image_sha256,
                        confidence=tag.confidence,
                    )

        except Exception as e:
            logger.warning(f"Failed to store in Neo4j: {e}")
            # Don't fail the whole operation if Neo4j write fails
