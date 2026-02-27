"""Monitor imageboard threads with random polling intervals and auto-follow links."""

import sys
import time
import signal
import subprocess
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Set
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from parse_imageboard_thread import ImageboardThreadParser
from feed.storage.neo4j_connection import get_connection


class RandomThreadMonitor:
    """Monitor an imageboard thread with random polling intervals."""
    
    def __init__(
        self,
        thread_url: str,
        interval_min: int = 120,  # 2 minutes
        interval_max: int = 600,  # 10 minutes
        max_depth: int = 5,  # Max depth of linked threads to follow
        cache_dir: Optional[Path] = None,
        download_images: bool = True,
    ):
        """
        Initialize thread monitor with random intervals.
        
        Args:
            thread_url: Imageboard thread URL
            interval_min: Minimum polling interval in seconds
            interval_max: Maximum polling interval in seconds
            max_depth: Maximum depth of linked threads to follow
            cache_dir: Directory for caching images and HTML
            download_images: Whether to download images
        """
        self.thread_url = thread_url
        self.interval_min = interval_min
        self.interval_max = interval_max
        self.max_depth = max_depth
        self.parser = ImageboardThreadParser(
            cache_dir=cache_dir,
            download_images=download_images,
        )
        self.neo4j = get_connection()
        self.running = True
        
        # Parse URL to get board and thread_id
        url_info = self.parser.parse_url(thread_url)
        self.board = url_info["board"]
        self.thread_id = url_info["thread_id"]
        
        # Track monitored threads to avoid duplicates
        self.monitored_threads: Set[int] = {self.thread_id}
        self.current_depth = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutdown signal received. Stopping monitor...")
        self.running = False
    
    def _get_random_interval(self) -> int:
        """Get a random interval between min and max."""
        return random.randint(self.interval_min, self.interval_max)
    
    def _monitor_linked_threads(self, linked_thread_ids: List[int]):
        """
        Start monitoring linked threads if within depth limit.
        
        Args:
            linked_thread_ids: List of thread IDs to monitor
        """
        if self.current_depth >= self.max_depth:
            print(f"  -> Max depth ({self.max_depth}) reached, not following new links")
            return
        
        for linked_thread_id in linked_thread_ids:
            if linked_thread_id in self.monitored_threads:
                continue
            
            self.monitored_threads.add(linked_thread_id)
            linked_url = f"https://boards.4chan.org/{self.board}/thread/{linked_thread_id}"
            
            # Check if thread exists in database
            check_query = """
            MATCH (t:Thread {board: $board, thread_id: $thread_id})
            RETURN t.thread_id as thread_id, t.last_crawled_at as last_crawled_at
            LIMIT 1
            """
            result = self.neo4j.execute_read(
                check_query,
                parameters={"board": self.board, "thread_id": linked_thread_id}
            )
            
            if result:
                print(f"  -> Thread /{self.board}/{linked_thread_id} already in database")
                continue
            
            print(f"  -> Starting monitor for linked thread /{self.board}/{linked_thread_id} (depth {self.current_depth + 1})")
            
            # Spawn a new monitor process for this thread
            try:
                script_path = Path(__file__).absolute()
                cmd = [
                    sys.executable,
                    str(script_path),
                    linked_url,
                    "--interval-min", str(self.interval_min),
                    "--interval-max", str(self.interval_max),
                    "--max-depth", str(self.max_depth),
                ]
                if not self.parser.download_images:
                    cmd.append("--no-images")
                
                # Start in background (detached)
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                print(f"  -> Monitor started for /{self.board}/{linked_thread_id}")
            except Exception as e:
                print(f"  -> Warning: Could not start monitor for /{self.board}/{linked_thread_id}: {e}")
    
    def check_thread(self) -> dict:
        """
        Check thread for updates.
        
        Returns:
            Dictionary with check results
        """
        interval = self._get_random_interval()
        next_check_time = datetime.now()
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking thread...")
        print(f"Thread: /{self.board}/{self.thread_id}")
        print(f"Next interval: {interval}s ({interval / 60:.1f} min)")
        
        try:
            # Fetch and parse thread
            html_text, html_bytes = self.parser.fetch_thread_html(self.thread_url)
            thread_data = self.parser.parse_thread_html(html_text, self.thread_url)
            
            # Cache HTML
            html_path = self.parser.cache_html(self.thread_url, html_bytes)
            
            # Check if thread exists in database
            existing = self.parser.check_thread_exists(
                self.neo4j, self.board, self.thread_id
            )
            
            # Compute content hash
            content_hash = self.parser.compute_content_hash(thread_data)
            
            # Determine if content changed
            changed = True
            if existing:
                existing_hash = existing.get("content_hash")
                if existing_hash == content_hash:
                    changed = False
                    print("  -> No changes detected")
                else:
                    print("  -> Changes detected!")
                    old_post_count = existing.get("post_count", 0)
                    new_post_count = thread_data["post_count"]
                    if new_post_count > old_post_count:
                        print(f"  -> New posts: {new_post_count - old_post_count}")
            else:
                print("  -> First time seeing this thread")
            
            # Count images
            image_count = sum(1 for p in thread_data.get("posts", []) if p.get("image_url"))
            print(f"  -> Posts: {thread_data['post_count']} (with images: {image_count})")
            
            # Store in database
            self.parser.store_thread(self.neo4j, thread_data, html_path)
            
            # Check for linked threads
            linked_threads = []
            for post_data in thread_data.get("posts", []):
                linked_thread_ids = post_data.get("linked_thread_ids", [])
                for linked_thread_id in linked_thread_ids:
                    if linked_thread_id != self.thread_id and linked_thread_id not in self.monitored_threads:
                        linked_threads.append(linked_thread_id)
            
            if linked_threads:
                print(f"  -> Found {len(linked_threads)} new linked thread(s): {linked_threads}")
                self._monitor_linked_threads(linked_threads)
            
            return {
                "success": True,
                "changed": changed,
                "post_count": thread_data["post_count"],
                "image_count": image_count,
                "content_hash": content_hash,
                "linked_threads": linked_threads,
                "next_interval": interval,
            }
            
        except Exception as e:
            print(f"  -> ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
            }
    
    def run(self):
        """Run monitoring loop with random intervals."""
        print("=" * 70)
        print("RANDOM INTERVAL THREAD MONITOR")
        print("=" * 70)
        print(f"Thread URL: {self.thread_url}")
        print(f"Board: /{self.board}/")
        print(f"Thread ID: {self.thread_id}")
        print(f"Polling interval: {self.interval_min}-{self.interval_max} seconds ({self.interval_min/60:.1f}-{self.interval_max/60:.1f} min)")
        print(f"Max depth: {self.max_depth}")
        print(f"Download images: {self.parser.download_images}")
        print(f"Cache directory: {self.parser.cache_dir}")
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
            if result.get("changed"):
                print("Thread indexed successfully")
            else:
                print("Thread already indexed, monitoring for changes...")
        else:
            print(f"Initial check failed: {result.get('error')}")
            print("Will retry on next interval...")
        
        # Monitoring loop
        while self.running:
            try:
                # Get random interval and wait
                interval = result.get("next_interval", self._get_random_interval())
                print(f"\nWaiting {interval}s ({interval / 60:.1f} min) until next check...")
                
                # Sleep in small increments to allow quick shutdown
                sleep_remaining = interval
                while sleep_remaining > 0 and self.running:
                    sleep_time = min(5, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
                
                if not self.running:
                    break
                
                # Check thread
                result = self.check_thread()
                check_count += 1
                
                if result.get("success") and result.get("changed"):
                    print("  -> Thread updated in database")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                # Continue monitoring even on error
                continue
        
        print("\n" + "=" * 70)
        print("MONITORING STOPPED")
        print("=" * 70)
        print(f"Total checks performed: {check_count}")
        print(f"Threads monitored: {len(self.monitored_threads)}")
        print(f"Monitored thread IDs: {sorted(self.monitored_threads)}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor an imageboard thread with random polling intervals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor thread with default intervals (2-10 min)
  python monitor_random.py https://boards.4chan.org/b/thread/944305638

  # Monitor with shorter intervals (1-5 min)
  python monitor_random.py https://boards.4chan.org/b/thread/944305638 --interval-min 60 --interval-max 300

  # Monitor with deeper linked thread following
  python monitor_random.py https://boards.4chan.org/b/thread/944305638 --max-depth 10

  # Monitor without downloading images
  python monitor_random.py https://boards.4chan.org/b/thread/944305638 --no-images
        """
    )
    parser.add_argument(
        "thread_url",
        help="Imageboard thread URL (e.g., https://boards.4chan.org/b/thread/944305638)"
    )
    parser.add_argument(
        "--interval-min",
        type=int,
        default=120,
        help="Minimum polling interval in seconds (default: 120 = 2 minutes)"
    )
    parser.add_argument(
        "--interval-max",
        type=int,
        default=600,
        help="Maximum polling interval in seconds (default: 600 = 10 minutes)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum depth of linked threads to follow (default: 5)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/home/jovyan/workspaces/cache/imageboard"),
        help="Cache directory for images and HTML"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't download images"
    )
    
    args = parser.parse_args()
    
    if args.interval_min >= args.interval_max:
        print("Error: interval-min must be less than interval-max")
        return 1
    
    monitor = RandomThreadMonitor(
        thread_url=args.thread_url,
        interval_min=args.interval_min,
        interval_max=args.interval_max,
        max_depth=args.max_depth,
        cache_dir=args.cache_dir,
        download_images=not args.no_images,
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
