"""Monitor a Reddit subreddit for new posts and threads."""

import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Set
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection


class RedditSubredditMonitor:
    """Monitor a Reddit subreddit for new posts."""
    
    def __init__(
        self,
        subreddit: str,
        interval_seconds: int = 600,  # 10 minutes default
        sort: str = "new",  # new, hot, top, rising
        auto_monitor_threads: bool = True,  # Automatically monitor threads with images
        thread_check_interval: int = 300,  # How often to check individual threads
    ):
        """
        Initialize Reddit subreddit monitor.
        
        Args:
            subreddit: Subreddit name (without r/ prefix)
            interval_seconds: How often to check for new posts (default: 600 = 10 minutes)
            sort: Sort order for posts (new, hot, top, rising)
            auto_monitor_threads: Automatically start monitoring threads with images
            thread_check_interval: How often to check monitored threads
        """
        self.subreddit = subreddit.replace("r/", "")
        self.interval_seconds = interval_seconds
        self.sort = sort
        self.auto_monitor_threads = auto_monitor_threads
        self.thread_check_interval = thread_check_interval
        self.adapter = RedditAdapter()
        self.neo4j = get_connection()
        self.running = True
        
        # Track known post IDs
        self.known_posts: Set[str] = set()
        # Track monitored threads
        self.monitored_threads: Set[str] = set()
        # Track child processes
        self.processes: List[subprocess.Popen] = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutdown signal received. Stopping monitor and child processes...")
        self.running = False
        self._cleanup_processes()
        
    def _cleanup_processes(self):
        """Terminate all child processes."""
        print(f"Cleaning up {len(self.processes)} child processes...")
        for p in self.processes:
            try:
                if p.poll() is None:  # If still running
                    p.terminate()
            except Exception as e:
                print(f"Error terminating process {p.pid}: {e}")
        
        # Give them a moment to die
        time.sleep(1)
        
        for p in self.processes:
            try:
                if p.poll() is None:
                    print(f"Force killing process {p.pid}")
                    p.kill()
            except Exception as e:
                pass
        self.processes = []
    
    def check_subreddit(self) -> dict:
        """
        Check subreddit for new posts.
        
        Returns:
            Dictionary with check results
        """
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking r/{self.subreddit}...")
        
        try:
            # Fetch posts
            posts, after = self.adapter.fetch_posts(
                self.subreddit,
                sort=self.sort,
                limit=50
            )
            
            if not posts:
                print("  -> No posts found")
                return {
                    "success": False,
                    "error": "No posts found"
                }
            
            # Filter new posts
            new_posts = [p for p in posts if p.id not in self.known_posts]
            
            print(f"  -> Total posts: {len(posts)}")
            print(f"  -> New posts: {len(new_posts)}")
            
            if new_posts:
                # Store new posts
                for post in new_posts:
                    self._store_post(post)
                    self.known_posts.add(post.id)
                
                print(f"  -> Stored {len(new_posts)} new posts")
                
                # Auto-monitor threads with images
                if self.auto_monitor_threads:
                    self._auto_monitor_new_threads(new_posts)
            else:
                print("  -> No new posts")
            
            # Cleanup finished processes from list
            self.processes = [p for p in self.processes if p.poll() is None]
            
            return {
                "success": True,
                "total_posts": len(posts),
                "new_posts": len(new_posts),
            }
            
        except Exception as e:
            print(f"  -> ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
            }
    
    def _store_post(self, post):
        """Store post in Neo4j."""
        try:
            query = """
            MERGE (p:Post {id: $id})
            SET p.title = $title,
                p.author = $author,
                p.score = $score,
                p.num_comments = $num_comments,
                p.url = $url,
                p.selftext = $selftext,
                p.subreddit = $subreddit,
                p.permalink = $permalink,
                p.over_18 = $over_18,
                p.upvote_ratio = $upvote_ratio,
                p.created_utc = $created_utc,
                p.updated_at = datetime()
            MERGE (s:Subreddit {name: $subreddit})
            MERGE (p)-[:POSTED_IN]->(s)
            """
            
            self.neo4j.execute_write(
                query,
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
                    "over_18": post.over_18,
                    "upvote_ratio": post.upvote_ratio,
                    "created_utc": post.created_utc.isoformat() if post.created_utc else None,
                }
            )
            
        except Exception as e:
            print(f"    ⚠ Warning: Error storing post {post.id}: {e}")
    
    def _auto_monitor_new_threads(self, new_posts):
        """Automatically start monitoring threads with images."""
        
        for post in new_posts:
            # Skip already monitored
            if post.id in self.monitored_threads:
                continue
            
            # Check if post has images
            has_image = any(
                domain in post.url
                for domain in ["i.redd.it", "reddit.com/gallery", "imgur.com", "i.imgur.com"]
            )
            
            if has_image:
                print(f"\n  -> Starting monitor for post: {post.title[:50]}...")
                print(f"     URL: {post.url}")
                
                # Start thread monitor as subprocess
                try:
                    # Fix: Point to monitor_reddit_thread.py explicitly
                    script_path = project_root / "monitor_reddit_thread.py"
                    
                    cmd = [
                        sys.executable,
                        str(script_path),
                        post.permalink,
                        "--interval", str(self.thread_check_interval),
                    ]
                    
                    # Start in background, but track it
                    # Removed start_new_session=True to allow signal propagation if desired,
                    # but since we handle cleanup explicitly, it's fine either way.
                    # Keeping it default (attached to group) is usually better for cleanup.
                    p = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        cwd=str(project_root)
                    )
                    
                    self.processes.append(p)
                    self.monitored_threads.add(post.id)
                    print(f"     ✓ Monitor started (PID: {p.pid})")
                    
                except Exception as e:
                    print(f"     ✗ Error starting monitor: {e}")
    
    def run(self):
        """Run monitoring loop."""
        print("=" * 70)
        print("REDDIT SUBREDDIT MONITOR")
        print("=" * 70)
        print(f"Subreddit: r/{self.subreddit}/")
        print(f"Check interval: {self.interval_seconds} seconds ({self.interval_seconds / 60:.1f} minutes)")
        print(f"Sort order: {self.sort}")
        print(f"Auto-monitor threads: {self.auto_monitor_threads}")
        print(f"Thread check interval: {self.thread_check_interval} seconds")
        print()
        print(f"Connected to Neo4j: {self.neo4j.uri}")
        print()
        print("Press Ctrl+C to stop monitoring")
        print("=" * 70)
        print()
        
        check_count = 0
        
        # Initial check
        print("Performing initial check...")
        result = self.check_subreddit()
        check_count += 1
        
        if result.get("success"):
            print("Subreddit indexed successfully")
        else:
            print(f"Initial check failed: {result.get('error')}")
            print("Will retry on next interval...")
        
        # Monitoring loop
        while self.running:
            try:
                print(f"\nWaiting {self.interval_seconds} seconds until next check...")
                
                # Sleep in small increments
                sleep_remaining = self.interval_seconds
                while sleep_remaining > 0 and self.running:
                    sleep_time = min(5, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
                
                if not self.running:
                    break
                
                # Check subreddit
                result = self.check_subreddit()
                check_count += 1
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        self._cleanup_processes()
        print("\n" + "=" * 70)
        print("MONITORING STOPPED")
        print("=" * 70)
        print(f"Total checks performed: {check_count}")
        print(f"Posts indexed: {len(self.known_posts)}")
        print(f"Threads monitored: {len(self.monitored_threads)}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor a Reddit subreddit for new posts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor subreddit with default settings
  python monitor_reddit_subreddit.py JordynJonesCandy

  # Monitor with 5 minute intervals
  python monitor_reddit_subreddit.py JordynJonesCandy --interval 300

  # Monitor hot posts instead of new
  python monitor_reddit_subreddit.py JordynJonesCandy --sort hot

  # Don't auto-monitor individual threads
  python monitor_reddit_subreddit.py JordynJonesCandy --no-auto-monitor
        """
    )
    parser.add_argument(
        "subreddit",
        help="Subreddit name (with or without r/ prefix)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Check interval in seconds (default: 600 = 10 minutes)"
    )
    parser.add_argument(
        "--sort",
        type=str,
        default="new",
        choices=["new", "hot", "top", "rising"],
        help="Sort order (default: new)"
    )
    parser.add_argument(
        "--thread-interval",
        type=int,
        default=300,
        help="How often to check monitored threads in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--no-auto-monitor",
        action="store_true",
        help="Don't automatically monitor individual threads"
    )
    
    args = parser.parse_args()
    
    monitor = RedditSubredditMonitor(
        subreddit=args.subreddit,
        interval_seconds=args.interval,
        sort=args.sort,
        auto_monitor_threads=not args.no_auto_monitor,
        thread_check_interval=args.thread_interval,
    )
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        monitor._cleanup_processes()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        monitor._cleanup_processes()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
