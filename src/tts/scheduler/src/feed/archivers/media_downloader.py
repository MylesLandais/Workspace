"""Media downloader service - downloads and stores imageboard media in MinIO."""

import asyncio
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import aiohttp
from pathlib import Path

from ..storage.valkey_connection import get_valkey_connection
from ..storage.minio_connection import get_minio_connection


class MediaDownloader:
    """
    Downloads media from imageboard threads, deduplicates by hash,
    and stores in MinIO object storage.
    """

    def __init__(
        self,
        board: str,
        download_thumbs: bool = True,
        download_full: bool = False,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize media downloader.
        
        Args:
            board: Board name (e.g., "b")
            download_thumbs: Download thumbnails (default: True)
            download_full: Download full images (default: False, saves storage)
            user_agent: Custom User-Agent string
        """
        self.board = board
        self.download_thumbs = download_thumbs
        self.download_full = download_full
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; imageboard-archiver/1.0)"
        
        self.valkey = get_valkey_connection()
        self.minio = get_minio_connection()
        
        # MinIO buckets
        self.thumbs_bucket = f"imageboard-{board}-thumbs"
        self.images_bucket = f"imageboard-{board}-images"
        
        # Ensure buckets exist
        self.minio.ensure_bucket(self.thumbs_bucket)
        if self.download_full:
            self.minio.ensure_bucket(self.images_bucket)
        
        # Valkey keys
        self.thread_queue_key = f"imageboard:{board}:threads:queue"
        self.media_queue_key = f"imageboard:{board}:media:queue"
        self.seen_media_key = f"imageboard:{board}:media:seen"
        self.hash_index_key = f"imageboard:{board}:media:hash_index"
        
        self.running = False

    def _compute_hash(self, data: bytes) -> Tuple[str, str]:
        """
        Compute MD5 and SHA256 hashes of data.
        
        Args:
            data: Bytes to hash
            
        Returns:
            Tuple of (md5_hash, sha256_hash)
        """
        md5 = hashlib.md5(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
        return md5, sha256

    async def _download_media(
        self,
        session: aiohttp.ClientSession,
        url: str,
    ) -> Optional[bytes]:
        """
        Download media from URL.
        
        Args:
            session: aiohttp session
            url: Media URL
            
        Returns:
            Media bytes or None on error
        """
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with session.get(url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def _get_content_type(self, ext: str) -> str:
        """
        Get content type from file extension.
        
        Args:
            ext: File extension (e.g., ".jpg", ".webm")
            
        Returns:
            Content type string
        """
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webm": "video/webm",
            ".webp": "image/webp",
        }
        return content_types.get(ext.lower(), "application/octet-stream")

    async def _process_media(
        self,
        session: aiohttp.ClientSession,
        tim: int,
        ext: str,
        is_thumbnail: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Download, hash, and store a media file.
        
        Args:
            session: aiohttp session
            tim: imageboard timestamp (file identifier)
            ext: File extension
            is_thumbnail: Whether this is a thumbnail
            
        Returns:
            Media metadata dictionary or None on error
        """
        # Build URL
        if is_thumbnail:
            url = f"https://i.4cdn.org/{self.board}/{tim}s.jpg"  # Thumbnail
            bucket = self.thumbs_bucket
        else:
            url = f"https://i.4cdn.org/{self.board}/{tim}{ext}"
            bucket = self.images_bucket
        
        # Check if already processed
        media_key = f"{tim}{ext}" if not is_thumbnail else f"{tim}s.jpg"
        seen_key = f"{self.board}:{media_key}"
        
        try:
            client = self.valkey.client
            if client.sismember(self.seen_media_key, seen_key):
                # Already processed
                return None
        except Exception:
            pass
        
        # Download media
        data = await self._download_media(session, url)
        if not data:
            return None
        
        # Compute hashes
        md5_hash, sha256_hash = self._compute_hash(data)
        
        # Check if hash already exists (deduplication)
        try:
            client = self.valkey.client
            existing_object = client.hget(self.hash_index_key, sha256_hash)
            if existing_object:
                # Media already stored with this hash
                print(f"  Dedupe: {media_key} (hash: {sha256_hash[:8]}...)")
                # Mark as seen
                client.sadd(self.seen_media_key, seen_key)
                return {
                    "tim": tim,
                    "ext": ext,
                    "is_thumbnail": is_thumbnail,
                    "md5": md5_hash,
                    "sha256": sha256_hash,
                    "size": len(data),
                    "deduplicated": True,
                    "existing_object": existing_object.decode() if isinstance(existing_object, bytes) else existing_object,
                }
        except Exception:
            pass
        
        # Store in MinIO
        object_name = f"{tim}{ext}" if not is_thumbnail else f"{tim}s.jpg"
        content_type = self._get_content_type(ext)
        
        success = self.minio.upload_bytes(
            bucket,
            object_name,
            data,
            content_type=content_type,
        )
        
        if not success:
            return None
        
        # Index by hash
        try:
            client = self.valkey.client
            client.hset(
                self.hash_index_key,
                sha256_hash,
                f"{bucket}/{object_name}",
            )
            client.sadd(self.seen_media_key, seen_key)
        except Exception:
            pass
        
        return {
            "tim": tim,
            "ext": ext,
            "is_thumbnail": is_thumbnail,
            "md5": md5_hash,
            "sha256": sha256_hash,
            "size": len(data),
            "bucket": bucket,
            "object_name": object_name,
            "url": url,
            "deduplicated": False,
        }

    async def _process_thread_media(self, thread_id: int) -> Dict[str, Any]:
        """
        Process all media from a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Processing results
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing media for thread {thread_id}...")
        
        # Fetch thread JSON to get posts with media
        thread_url = f"https://a.4cdn.org/{self.board}/thread/{thread_id}.json"
        headers = {"User-Agent": self.user_agent}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(thread_url, headers=headers, timeout=10) as response:
                    if response.status == 404:
                        return {"success": False, "error": "Thread not found"}
                    
                    response.raise_for_status()
                    thread_json = await response.json()
                    
                    posts = thread_json.get("posts", [])
                    if not posts:
                        return {"success": False, "error": "No posts"}
                    
                    # Collect media from posts
                    media_items = []
                    for post in posts:
                        tim = post.get("tim")
                        if not tim:
                            continue
                        
                        ext = post.get("ext", ".jpg")
                        
                        # Download thumbnail
                        if self.download_thumbs:
                            thumb_result = await self._process_media(
                                session, tim, ext, is_thumbnail=True
                            )
                            if thumb_result:
                                media_items.append(thumb_result)
                        
                        # Download full image
                        if self.download_full:
                            full_result = await self._process_media(
                                session, tim, ext, is_thumbnail=False
                            )
                            if full_result:
                                media_items.append(full_result)
                    
                    return {
                        "success": True,
                        "thread_id": thread_id,
                        "media_count": len(media_items),
                        "media": media_items,
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def _worker_loop(self):
        """Worker loop that processes threads from queue."""
        print(f"Media downloader worker started for /{self.board}/")
        
        while self.running:
            try:
                client = self.valkey.client
                
                # Pop thread ID from queue (blocking with timeout)
                result = client.brpop(self.thread_queue_key, timeout=5)
                
                if result:
                    # brpop returns (key, value) tuple
                    thread_id = int(result[1])
                    result = await self._process_thread_media(thread_id)
                    
                    if result.get("success"):
                        print(f"  Processed {result.get('media_count', 0)} media items")
                    else:
                        print(f"  Error: {result.get('error')}")
                else:
                    # No work, continue loop
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Error in worker loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)

    async def run(self, num_workers: int = 2):
        """
        Run media downloader with multiple workers.
        
        Args:
            num_workers: Number of parallel workers
        """
        self.running = True
        print("=" * 70)
        print(f"IMAGEBOARD MEDIA DOWNLOADER - /{self.board}/")
        print("=" * 70)
        print(f"Download thumbnails: {self.download_thumbs}")
        print(f"Download full images: {self.download_full}")
        print(f"Workers: {num_workers}")
        print(f"MinIO endpoint: {self.minio.endpoint}")
        print()
        
        # Start worker tasks
        workers = [asyncio.create_task(self._worker_loop()) for _ in range(num_workers)]
        
        try:
            await asyncio.gather(*workers)
        except KeyboardInterrupt:
            print("\nShutdown signal received")
            self.running = False
            for worker in workers:
                worker.cancel()

    def stop(self):
        """Stop downloader."""
        self.running = False


async def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download imageboard media to MinIO")
    parser.add_argument("board", help="Board name (e.g., 'b')")
    parser.add_argument("--thumbs", action="store_true", default=True, help="Download thumbnails")
    parser.add_argument("--full", action="store_true", help="Download full images")
    parser.add_argument("--workers", type=int, default=2, help="Number of workers")
    
    args = parser.parse_args()
    
    downloader = MediaDownloader(
        board=args.board,
        download_thumbs=args.thumbs,
        download_full=args.full,
    )
    
    try:
        await downloader.run(num_workers=args.workers)
    except KeyboardInterrupt:
        downloader.stop()


if __name__ == "__main__":
    asyncio.run(main())

