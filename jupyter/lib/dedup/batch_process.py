"""Batch processing script to run deduplication on existing Reddit posts."""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from feed.storage.neo4j_connection import get_connection
from feed.utils import is_image_url, download_and_hash_image
from .deduplicator import ImageDeduplicator
from .models import IngestRequest


class BatchProcessor:
    """Batch processor for existing image data."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_clip: bool = True,
        batch_size: int = 100,
        max_retries: int = 3,
    ):
        """
        Initialize batch processor.

        Args:
            storage_path: Path for image storage (default: from env)
            enable_clip: Whether to enable CLIP embeddings
            batch_size: Number of posts to process per batch
            max_retries: Maximum retry attempts for failed downloads
        """
        storage_path = storage_path or os.getenv(
            "IMAGE_DEDUP_STORAGE_PATH", "/tmp/image_dedup_storage"
        )
        self.deduplicator = ImageDeduplicator(
            storage_path=storage_path, enable_clip=enable_clip
        )
        self.neo4j = get_connection()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.stats = {
            "processed": 0,
            "successful": 0,
            "duplicates": 0,
            "new": 0,
            "errors": 0,
            "skipped": 0,
        }

    def get_posts_with_images(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get posts with image URLs from Neo4j.

        Args:
            limit: Maximum number of posts to return (None = all)
            offset: Offset for pagination

        Returns:
            List of post records with image URLs
        """
        query = """
        MATCH (p:Post)
        WHERE p.url IS NOT NULL 
          AND p.url <> ""
          AND (p.url CONTAINS '.jpg' OR p.url CONTAINS '.jpeg' OR 
               p.url CONTAINS '.png' OR p.url CONTAINS '.webp' OR
               p.url CONTAINS '.gif' OR p.url CONTAINS 'i.redd.it' OR
               p.url CONTAINS 'i.imgur.com')
        OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
        RETURN p.id as post_id,
               p.url as url,
               p.title as title,
               p.author as author,
               p.created_utc as created_utc,
               p.permalink as permalink,
               p.score as score,
               s.name as subreddit
        ORDER BY p.created_utc DESC
        """

        if limit:
            query += f" SKIP {offset} LIMIT {limit}"

        result = self.neo4j.execute_read(query)

        posts = []
        for record in result:
            url = record.get("url")
            if url and is_image_url(url):
                posts.append({
                    "post_id": record.get("post_id"),
                    "url": url,
                    "title": record.get("title"),
                    "author": record.get("author"),
                    "created_utc": record.get("created_utc"),
                    "permalink": record.get("permalink"),
                    "score": record.get("score"),
                    "subreddit": record.get("subreddit"),
                })

        return posts

    def check_already_processed(self, post_id: str) -> bool:
        """
        Check if post has already been processed through deduplication.

        Args:
            post_id: Post ID

        Returns:
            True if already processed, False otherwise
        """
        query = """
        MATCH (p:Post {id: $post_id})<-[:APPEARED_IN]-(i:ImageFile)
        RETURN count(i) as count
        """
        result = self.neo4j.execute_read(query, parameters={"post_id": post_id})
        if result:
            return result[0].get("count", 0) > 0
        return False

    def download_image(self, url: str, retries: int = 3) -> Optional[bytes]:
        """
        Download image with retries.

        Args:
            url: Image URL
            retries: Number of retry attempts

        Returns:
            Image bytes or None on failure
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0)",
        }

        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=10, stream=True)
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    return None

                # Download image
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
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                print(f"  Error downloading {url}: {e}")
                return None

        return None

    def process_post(self, post: Dict[str, Any]) -> bool:
        """
        Process a single post through deduplication.

        Args:
            post: Post record with image URL

        Returns:
            True if successful, False otherwise
        """
        post_id = post["post_id"]
        url = post["url"]

        # Check if already processed
        if self.check_already_processed(post_id):
            self.stats["skipped"] += 1
            return True

        # Download image
        image_bytes = self.download_image(url)
        if not image_bytes:
            self.stats["errors"] += 1
            return False

        try:
            # Convert created_utc to datetime if needed
            created_at = post.get("created_utc")
            if isinstance(created_at, (int, float)):
                created_at = datetime.fromtimestamp(created_at)
            elif isinstance(created_at, str):
                # Try to parse ISO format or timestamp
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    try:
                        created_at = datetime.fromtimestamp(float(created_at))
                    except (ValueError, TypeError):
                        created_at = datetime.utcnow()
            elif created_at is None:
                created_at = datetime.utcnow()

            # Create ingest request
            ingest_request = IngestRequest(
                image_bytes=image_bytes,
                post_id=post_id,
                source="reddit",
                metadata={
                    "subreddit": post.get("subreddit"),
                    "author": post.get("author"),
                    "title": post.get("title"),
                    "url": url,
                    "permalink": post.get("permalink"),
                    "created_at": created_at,
                    "score": post.get("score"),
                },
            )

            # Process through deduplicator
            result = self.deduplicator.ingest_image(ingest_request)

            # Update statistics
            self.stats["successful"] += 1
            if result.is_duplicate:
                self.stats["duplicates"] += 1
            else:
                self.stats["new"] += 1

            return True

        except Exception as e:
            print(f"  Error processing post {post_id}: {e}")
            self.stats["errors"] += 1
            return False

    def process_all(self, limit: Optional[int] = None, start_from: int = 0) -> Dict[str, int]:
        """
        Process all posts with images.

        Args:
            limit: Maximum number of posts to process (None = all)
            start_from: Offset to start from

        Returns:
            Statistics dictionary
        """
        print(f"Starting batch processing...")
        print(f"Batch size: {self.batch_size}")
        print(f"Starting from offset: {start_from}")
        if limit:
            print(f"Processing up to {limit} posts")
        else:
            print("Processing all available posts")

        offset = start_from
        batch_num = 0

        while True:
            batch_num += 1
            print(f"\n--- Batch {batch_num} (offset: {offset}) ---")

            # Get batch of posts
            batch_limit = self.batch_size if limit is None else min(
                self.batch_size, limit - offset + start_from
            )
            posts = self.get_posts_with_images(limit=batch_limit, offset=offset)

            if not posts:
                print("No more posts to process")
                break

            print(f"Processing {len(posts)} posts...")

            # Process each post
            for i, post in enumerate(posts, 1):
                self.stats["processed"] += 1
                post_id = post["post_id"]
                print(f"  [{self.stats['processed']}] Processing {post_id}...", end=" ")

                success = self.process_post(post)

                if success:
                    if self.check_already_processed(post_id):
                        print("(skipped - already processed)")
                    else:
                        print("(success)")
                else:
                    print("(error)")

                # Progress update every 10 posts
                if self.stats["processed"] % 10 == 0:
                    self.print_stats()

            offset += len(posts)

            # Check if we've reached the limit
            if limit and offset >= start_from + limit:
                break

            # Small delay between batches
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
            f"Errors: {self.stats['errors']}, "
            f"Skipped: {self.stats['skipped']}"
        )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch process existing Reddit posts through image deduplication"
    )
    parser.add_argument(
        "--storage-path",
        type=str,
        default=None,
        help="Path for image storage (default: from IMAGE_DEDUP_STORAGE_PATH env var)",
    )
    parser.add_argument(
        "--no-clip",
        action="store_true",
        help="Disable CLIP embeddings",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of posts to process per batch (default: 100)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of posts to process (default: all)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset to start from (default: 0)",
    )

    args = parser.parse_args()

    processor = BatchProcessor(
        storage_path=args.storage_path,
        enable_clip=not args.no_clip,
        batch_size=args.batch_size,
    )

    stats = processor.process_all(limit=args.limit, start_from=args.offset)

    print(f"\nFinal statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

