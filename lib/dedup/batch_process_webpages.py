"""Batch process WebPage nodes from crawler for image deduplication."""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from feed.storage.neo4j_connection import get_connection
from feed.utils import is_image_url, download_and_hash_image
from image_dedup.deduplicator import ImageDeduplicator
from image_dedup.models import IngestRequest


class WebPageBatchProcessor:
    """Batch processor for WebPage nodes from crawler."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_clip: bool = True,
        batch_size: int = 100,
    ):
        """Initialize processor."""
        import os
        storage_path = storage_path or os.getenv(
            "IMAGE_DEDUP_STORAGE_PATH", "/tmp/image_dedup_storage"
        )
        self.deduplicator = ImageDeduplicator(
            storage_path=storage_path, enable_clip=enable_clip
        )
        self.neo4j = get_connection()
        self.batch_size = batch_size
        self.stats = {
            "processed": 0,
            "successful": 0,
            "duplicates": 0,
            "new": 0,
            "errors": 0,
            "skipped": 0,
        }

    def get_webpages_with_images(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get WebPage nodes that appear to be images."""
        query = """
        MATCH (w:WebPage)
        WHERE w.normalized_url CONTAINS '.jpg' 
           OR w.normalized_url CONTAINS '.jpeg'
           OR w.normalized_url CONTAINS '.png'
           OR w.normalized_url CONTAINS '.webp'
           OR w.normalized_url CONTAINS '.gif'
           OR w.normalized_url CONTAINS 'i.redd.it'
           OR w.normalized_url CONTAINS 'imgur.com'
           OR w.normalized_url CONTAINS 'i.imgur.com'
        RETURN w.normalized_url as url,
               w.original_url as original_url,
               w.domain as domain,
               w.created_at as created_at,
               w.last_crawled_at as last_crawled_at
        ORDER BY w.created_at DESC
        """

        if limit:
            query += f" SKIP {offset} LIMIT {limit}"

        result = self.neo4j.execute_read(query)

        webpages = []
        for record in result:
            url = record.get("url") or record.get("original_url")
            if url and is_image_url(url):
                webpages.append({
                    "url": url,
                    "domain": record.get("domain"),
                    "created_at": record.get("created_at"),
                    "last_crawled_at": record.get("last_crawled_at"),
                })

        return webpages

    def check_already_processed(self, url: str) -> bool:
        """Check if URL has already been processed."""
        # Check if we have an ImageFile with this URL stored
        query = """
        MATCH (i:ImageFile)
        WHERE i.storage_path CONTAINS $url_hash OR i.sha256 IN [
            // We'd need to compute hash to check, so this is approximate
        ]
        RETURN count(i) as count
        """
        # For now, just check if URL appears in any stored image path
        # This is a simplified check
        return False

    def download_image(self, url: str, retries: int = 3) -> Optional[bytes]:
        """Download image with retries."""
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0)"}

        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=10, stream=True)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    return None

                image_bytes = b""
                max_size = 10 * 1024 * 1024  # 10MB
                for chunk in response.iter_content(chunk_size=8192):
                    image_bytes += chunk
                    if len(image_bytes) > max_size:
                        return None

                if image_bytes:
                    return image_bytes

            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None

        return None

    def process_webpage(self, webpage: Dict[str, Any]) -> bool:
        """Process a single webpage."""
        url = webpage["url"]

        # Download image
        image_bytes = self.download_image(url)
        if not image_bytes:
            self.stats["errors"] += 1
            return False

        try:
            created_at = webpage.get("created_at") or webpage.get("last_crawled_at")
            if isinstance(created_at, (int, float)):
                created_at = datetime.fromtimestamp(created_at)
            elif isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()

            # Create ingest request (no post_id since this is from crawler)
            ingest_request = IngestRequest(
                image_bytes=image_bytes,
                post_id=None,  # No Reddit post associated
                source="crawler",
                metadata={
                    "url": url,
                    "domain": webpage.get("domain"),
                    "created_at": created_at,
                },
            )

            # Process through deduplicator
            result = self.deduplicator.ingest_image(ingest_request)

            self.stats["successful"] += 1
            if result.is_duplicate:
                self.stats["duplicates"] += 1
            else:
                self.stats["new"] += 1

            return True

        except Exception as e:
            print(f"  Error processing {url}: {e}")
            self.stats["errors"] += 1
            return False

    def process_all(self, limit: Optional[int] = None, start_from: int = 0) -> Dict[str, int]:
        """Process all webpages."""
        print(f"Starting batch processing of WebPage nodes...")
        print(f"Batch size: {self.batch_size}")
        print(f"Starting from offset: {start_from}")

        offset = start_from
        batch_num = 0

        while True:
            batch_num += 1
            print(f"\n--- Batch {batch_num} (offset: {offset}) ---")

            batch_limit = (
                self.batch_size
                if limit is None
                else min(self.batch_size, limit - offset + start_from)
            )
            webpages = self.get_webpages_with_images(limit=batch_limit, offset=offset)

            if not webpages:
                print("No more webpages to process")
                break

            print(f"Processing {len(webpages)} webpages...")

            for i, webpage in enumerate(webpages, 1):
                self.stats["processed"] += 1
                url = webpage["url"]
                print(f"  [{self.stats['processed']}] Processing {url[:60]}...", end=" ")

                success = self.process_webpage(webpage)

                if success:
                    print("(success)")
                else:
                    print("(error)")

                if self.stats["processed"] % 10 == 0:
                    self.print_stats()

            offset += len(webpages)

            if limit and offset >= start_from + limit:
                break

            time.sleep(1)

        print("\n" + "=" * 60)
        print("Batch processing complete!")
        self.print_stats()

        return self.stats

    def print_stats(self) -> None:
        """Print current statistics."""
        print(
            f"\nStatistics: "
            f"Processed: {self.stats['processed']}, "
            f"Successful: {self.stats['successful']}, "
            f"New: {self.stats['new']}, "
            f"Duplicates: {self.stats['duplicates']}, "
            f"Errors: {self.stats['errors']}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch process WebPage nodes for image deduplication"
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--no-clip", action="store_true")
    parser.add_argument("--storage-path", type=str, default=None)

    args = parser.parse_args()

    processor = WebPageBatchProcessor(
        storage_path=args.storage_path, enable_clip=not args.no_clip
    )
    stats = processor.process_all(limit=args.limit, start_from=args.offset)







