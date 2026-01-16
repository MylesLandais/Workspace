"""Monitor a specific Reddit thread for new comments and images."""

import sys
import time
import signal
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection


def compute_sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def download_and_cache_image(
    image_url: str,
    cache_dir: Path
) -> Optional[Path]:
    """
    Download and cache a Reddit image.
    
    Args:
        image_url: Image URL
        cache_dir: Directory to cache images
    
    Returns:
        Path to cached image or None
    """
    try:
        # Add user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; RedditArchiver/1.0)"
        }
        
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Compute hash
        img_hash = compute_sha256_hash(response.content)
        
        # Determine extension
        url_path = image_url.split('?')[0]  # Remove query params
        ext = Path(url_path).suffix or '.jpg'
        
        # Create cache directory if needed
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with hash-based filename
        filename = f"{img_hash}{ext}"
        cache_path = cache_dir / filename
        
        # Don't re-download if exists
        if cache_path.exists():
            return cache_path
        
        cache_path.write_bytes(response.content)
        return cache_path
        
    except Exception as e:
        print(f"    ⚠ Error downloading {image_url}: {e}")
        return None


class RedditThreadMonitor:
    """Monitor a Reddit thread for changes."""
    
    def __init__(
        self,
        thread_permalink: str,
        interval_seconds: int = 300,  # 5 minutes default
        max_depth: int = 3,  # Max comment depth to track
        cache_dir: Optional[Path] = None,
        download_images: bool = True,
        run_once: bool = False,
    ):
        """
        Initialize Reddit thread monitor.
        
        Args:
            thread_permalink: Reddit thread permalink (e.g., /r/subreddit/comments/id/title/)
            interval_seconds: How often to check for updates (default: 300 = 5 minutes)
            max_depth: Maximum comment depth to track
            cache_dir: Directory for caching images
            download_images: Whether to download images to disk
            run_once: If True, run only one check and exit
        """
        self.thread_permalink = thread_permalink
        self.interval_seconds = interval_seconds
        self.max_depth = max_depth
        self.download_images = download_images
        self.run_once = run_once
        self.adapter = RedditAdapter()
        self.neo4j = get_connection()
        self.running = True
        
        # Set cache directory
        if cache_dir is None:
            cache_dir = Path("cache/reddit/images")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract subreddit and post ID from permalink
        parts = thread_permalink.strip('/').split('/')
        self.subreddit = None
        self.post_id = None
        for i, part in enumerate(parts):
            if part == 'r' and i + 1 < len(parts):
                self.subreddit = parts[i + 1]
            if part == 'comments' and i + 1 < len(parts):
                self.post_id = parts[i + 1]
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutdown signal received. Stopping monitor...")
        self.running = False
    
    def check_thread(self) -> dict:
        """
        Check thread for updates.
        
        Returns:
            Dictionary with check results
        """
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking thread...")
        print(f"Thread: {self.thread_permalink}")
        
        try:
            # Fetch thread data
            post, comments, raw_data = self.adapter.fetch_thread(
                self.thread_permalink,
                limit=1000
            )
            
            if not post:
                print("  -> ERROR: Post not found (may be deleted)")
                return {
                    "success": False,
                    "error": "Post not found"
                }
            
            print(f"  -> Post: {post.title[:60]}...")
            print(f"  -> Author: {post.author}")
            print(f"  -> Score: {post.score}")
            print(f"  -> Comments: {len(comments)}")
            
            # Extract images
            post_images = self.adapter.extract_all_images(post, raw_data)
            print(f"  -> Images in post: {len(post_images)}")
            
            # Extract images from comments
            comment_images = self.adapter.extract_images_from_comments(comments)
            print(f"  -> Images in comments: {len(comment_images)}")
            
            # Download images if requested
            cached_images = 0
            if self.download_images:
                print(f"  -> Downloading images to cache...")
                all_images = post_images + [ci['url'] for ci in comment_images]
                for img_url in all_images:
                    cached_path = download_and_cache_image(img_url, self.cache_dir)
                    if cached_path:
                        cached_images += 1
                print(f"  -> Cached {cached_images} images to disk")
            
            # Store in database
            self._store_post(post, comments, post_images, comment_images, cached_images > 0)
            
            return {
                "success": True,
                "post_id": post.id,
                "post_score": post.score,
                "comment_count": len(comments),
                "post_image_count": len(post_images),
                "comment_image_count": len(comment_images),
                "cached_images": cached_images,
            }
            
        except Exception as e:
            print(f"  -> ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
            }
    
    def _store_post(self, post, comments, post_images, comment_images, has_cached_images):
        """Store post and comments in Neo4j."""
        try:
            # Store post
            post_query = """
            MERGE (p:Post {id: $id})
            SET p.title = $title,
                p.author = $author,
                p.score = $score,
                p.num_comments = $num_comments,
                p.url = $url,
                p.selftext = $selftext,
                p.subreddit = $subreddit,
                p.permalink = $permalink,
                p.updated_at = datetime()
            """
            
            self.neo4j.execute_write(
                post_query,
                parameters={
                    "id": post.id,
                    "title": post.title,
                    "author": post.author,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "selftext": post.selftext,
                    "subreddit": post.subreddit,
                    "permalink": post.permalink,
                }
            )
            
            # Store comments
            comment_count = 0
            image_count = 0
            
            for comment in comments:
                if comment.depth > self.max_depth:
                    continue
                
                comment_query = """
                MERGE (c:Comment {id: $id})
                SET c.body = $body,
                    c.author = $author,
                    c.score = $score,
                    c.depth = $depth,
                    c.is_submitter = $is_submitter,
                    c.created_utc = $created_utc,
                    c.link_id = $link_id,
                    c.updated_at = datetime()
                MERGE (p:Post {id: $post_id})
                MERGE (c)-[:REPLIED_TO]->(p)
                """
                
                self.neo4j.execute_write(
                    comment_query,
                    parameters={
                        "id": comment.id,
                        "body": comment.body,
                        "author": comment.author,
                        "score": comment.score,
                        "depth": comment.depth,
                        "is_submitter": comment.is_submitter,
                        "created_utc": comment.created_utc.isoformat() if comment.created_utc else None,
                        "link_id": comment.link_id,
                        "post_id": post.id,
                    }
                )
                comment_count += 1
            
            # Store image URLs and paths
            for img_url in post_images + [ci['url'] for ci in comment_images]:
                # Get local path if cached
                image_path = None
                if has_cached_images:
                    img_hash = compute_sha256_hash(requests.get(img_url, timeout=10).content)
                    url_path = img_url.split('?')[0]
                    ext = Path(url_path).suffix or '.jpg'
                    cache_path = self.cache_dir / f"{img_hash}{ext}"
                    if cache_path.exists():
                        image_path = str(cache_path)
                
                image_query = """
                MERGE (i:Image {url: $url})
                SET i.image_path = $image_path,
                    i.updated_at = datetime()
                MERGE (p:Post {id: $post_id})
                MERGE (p)-[:HAS_IMAGE]->(i)
                """
                
                self.neo4j.execute_write(
                    image_query,
                    parameters={
                        "url": img_url,
                        "image_path": image_path,
                        "post_id": post.id,
                    }
                )
                image_count += 1
            
            print(f"  -> Stored: {comment_count} comments, {image_count} images")
            
        except Exception as e:
            print(f"  -> Warning: Error storing to database: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Run monitoring loop."""
        print("=" * 70)
        print("REDDIT THREAD MONITOR WITH IMAGE CACHING")
        print("=" * 70)
        print(f"Thread: {self.thread_permalink}")
        print(f"Subreddit: /r/{self.subreddit}/" if self.subreddit else "Unknown")
        print(f"Post ID: {self.post_id}")
        print(f"Check interval: {self.interval_seconds} seconds ({self.interval_seconds / 60:.1f} minutes)")
        print(f"Max comment depth: {self.max_depth}")
        print(f"Download images: {self.download_images}")
        print(f"Cache directory: {self.cache_dir}")
        print()
        print(f"Connected to Neo4j: {self.neo4j.uri}")
        print()
        print("Press Ctrl+C to stop monitoring")
        print("=" * 70)
        print()
        
        check_count = 0
        
        # Initial check
        print("Performing initial check...")
        result = self.check_thread()
        check_count += 1
        
        if result.get("success"):
            print("Thread indexed successfully")
        else:
            print(f"Initial check failed: {result.get('error')}")
            if self.run_once:
                return
            print("Will retry on next interval...")
        
        if self.run_once:
            print("Run once mode enabled. Exiting.")
            return

        # Monitoring loop
        while self.running:
            try:
                print(f"\nWaiting {self.interval_seconds} seconds until next check...")
                
                # Sleep in small increments for faster shutdown
                sleep_remaining = self.interval_seconds
                while sleep_remaining > 0 and self.running:
                    sleep_time = min(5, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
                
                if not self.running:
                    break
                
                # Check thread
                result = self.check_thread()
                check_count += 1
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 70)
        print("MONITORING STOPPED")
        print("=" * 70)
        print(f"Total checks performed: {check_count}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor a Reddit thread for new comments and images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor thread with default 5 minute intervals
  python monitor_reddit_thread.py /r/lululemon/comments/1q1it5f/atmospheric_purple

  # Monitor with 2 minute intervals
  python monitor_reddit_thread.py /r/lululemon/comments/1q1it5f/atmospheric_purple --interval 120

  # Track deeper comment trees
  python monitor_reddit_thread.py /r/lululemon/comments/1q1it5f/atmospheric_purple --max-depth 5

  # Don't download images (track URLs only)
  python monitor_reddit_thread.py /r/lululemon/comments/1q1it5f/atmospheric_purple --no-images
        """
    )
    parser.add_argument(
        "thread_permalink",
        help="Reddit thread permalink (e.g., /r/subreddit/comments/id/title/)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum comment depth to track (default: 3)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache/reddit/images"),
        help="Directory for caching images (default: cache/reddit/images)"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't download images (track URLs only)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run only one check and exit"
    )
    
    args = parser.parse_args()
    
    monitor = RedditThreadMonitor(
        thread_permalink=args.thread_permalink,
        interval_seconds=args.interval,
        max_depth=args.max_depth,
        cache_dir=args.cache_dir,
        download_images=not args.no_images,
        run_once=args.once,
    )
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
