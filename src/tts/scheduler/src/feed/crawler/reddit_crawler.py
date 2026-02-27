"""Modular Reddit crawler for testing and production use."""

import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable
from dataclasses import dataclass

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter

# Try to import PollingEngine (may fail if image_dedup dependencies missing)
try:
    from feed.polling.engine import PollingEngine
    POLLING_ENGINE_AVAILABLE = True
except ImportError:
    POLLING_ENGINE_AVAILABLE = False
    PollingEngine = None

try:
    from feed.storage.neo4j_connection import get_connection
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    get_connection = None


@dataclass
class CrawlerConfig:
    """Configuration for the Reddit crawler."""
    subreddits: List[str]
    request_delay_min: float = 10.0
    request_delay_max: float = 30.0
    subreddit_delay_min: float = 60.0
    subreddit_delay_max: float = 180.0
    cycle_delay_min: float = 300.0
    cycle_delay_max: float = 600.0
    step_delay_min: float = 5.0
    step_delay_max: float = 15.0
    max_pages: int = 1
    limit_per_page: int = 100
    max_cycles: Optional[int] = None
    dry_run: bool = False
    mock: bool = False


class RedditCrawler:
    """Modular Reddit crawler."""
    
    def __init__(
        self,
        config: CrawlerConfig,
        reddit_adapter: Optional[RedditAdapter] = None,
        polling_engine: Optional[PollingEngine] = None,
        neo4j_connection = None,
    ):
        """
        Initialize crawler.
        
        Args:
            config: Crawler configuration
            reddit_adapter: Optional RedditAdapter instance (will create if None)
            polling_engine: Optional PollingEngine instance (will create if None)
            neo4j_connection: Optional Neo4j connection (will create if None)
        """
        self.config = config
        self.cycle = 0
        self.running = False
        
        # Initialize components
        if reddit_adapter is None:
            self.reddit = RedditAdapter(
                mock=config.mock,
                delay_min=config.request_delay_min,
                delay_max=config.request_delay_max,
            )
        else:
            self.reddit = reddit_adapter
            
        if neo4j_connection is None and not config.dry_run and not config.mock:
            if not NEO4J_AVAILABLE:
                raise ValueError("Neo4j connection not available (feed.storage not importable)")
            try:
                self.neo4j = get_connection()
            except Exception as e:
                raise ValueError(f"Failed to connect to Neo4j: {e}")
        else:
            self.neo4j = neo4j_connection
            
        if polling_engine is None and not config.dry_run:
            if not POLLING_ENGINE_AVAILABLE:
                print("Warning: PollingEngine not available (image_dedup dependencies missing)")
                print("Falling back to direct RedditAdapter usage")
                self.engine = None
            elif self.neo4j is None:
                raise ValueError("Neo4j connection required for PollingEngine")
            else:
                self.engine = PollingEngine(
                    platform=self.reddit,
                    neo4j=self.neo4j,
                    dry_run=config.dry_run,
                    hash_images=True,
                    enable_deduplication=True,
                )
        else:
            self.engine = polling_engine
    
    def random_delay(self, min_sec: float, max_sec: float, reason: str = ""):
        """Sleep for a random duration and log it."""
        delay = random.uniform(min_sec, max_sec)
        if reason:
            print(f"  [DELAY] {reason}: {delay:.1f} seconds")
        time.sleep(delay)
    
    def crawl_subreddit(self, subreddit: str) -> int:
        """
        Crawl a single subreddit.
        
        Args:
            subreddit: Subreddit name
            
        Returns:
            Number of posts collected
        """
        self.random_delay(
            self.config.step_delay_min,
            self.config.step_delay_max,
            "Pre-subreddit delay"
        )
        
        try:
            if self.engine:
                posts = self.engine.poll_source(
                    source=subreddit,
                    sort="new",
                    max_pages=self.config.max_pages,
                    limit_per_page=self.config.limit_per_page,
                )
                return len(posts)
            else:
                # Mock/dry-run mode
                posts, _ = self.reddit.fetch_posts(
                    source=subreddit,
                    sort="new",
                    limit=self.config.limit_per_page,
                )
                return len(posts)
        except Exception as e:
            print(f"  ERROR processing r/{subreddit}: {e}")
            return 0
    
    def crawl_cycle(self) -> dict:
        """
        Run a single crawl cycle through all subreddits.
        
        Returns:
            Dictionary with cycle statistics
        """
        self.cycle += 1
        cycle_start = datetime.now()
        
        print()
        print("=" * 80)
        print(f"CYCLE {self.cycle} - Starting at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        self.random_delay(
            self.config.step_delay_min,
            self.config.step_delay_max,
            "Pre-cycle delay"
        )
        
        results = {
            "cycle": self.cycle,
            "start_time": cycle_start,
            "subreddits": {},
            "total_posts": 0,
            "errors": 0,
        }
        
        for idx, subreddit in enumerate(self.config.subreddits, 1):
            print()
            print("-" * 80)
            print(f"[{idx}/{len(self.config.subreddits)}] Processing r/{subreddit}")
            print("-" * 80)
            
            post_count = self.crawl_subreddit(subreddit)
            results["subreddits"][subreddit] = post_count
            results["total_posts"] += post_count
            
            if post_count == 0:
                results["errors"] += 1
            
            print(f"  Collected {post_count} posts from r/{subreddit}")
            
            # Delay between subreddits
            if idx < len(self.config.subreddits):
                next_subreddit = self.config.subreddits[idx]
                self.random_delay(
                    self.config.subreddit_delay_min,
                    self.config.subreddit_delay_max,
                    f"Between subreddits (next: r/{next_subreddit})"
                )
        
        cycle_end = datetime.now()
        results["end_time"] = cycle_end
        results["duration"] = (cycle_end - cycle_start).total_seconds()
        
        print()
        print("=" * 80)
        print(f"Cycle {self.cycle} complete. All {len(self.config.subreddits)} subreddits processed.")
        print(f"Total posts collected: {results['total_posts']}")
        print(f"Completed at {cycle_end.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {results['duration']:.1f} seconds")
        print("=" * 80)
        
        return results
    
    def run(self, on_cycle_complete: Optional[Callable[[dict], None]] = None):
        """
        Run the crawler continuously (or until max_cycles reached).
        
        Args:
            on_cycle_complete: Optional callback function called after each cycle
        """
        self.running = True
        
        print("=" * 80)
        print("REDDIT CRAWLER")
        print("=" * 80)
        print(f"Total subreddits: {len(self.config.subreddits)}")
        print(f"Max cycles: {self.config.max_cycles if self.config.max_cycles else 'Infinite'}")
        print(f"Request delays: {self.config.request_delay_min}-{self.config.request_delay_max} seconds")
        print(f"Subreddit delays: {self.config.subreddit_delay_min}-{self.config.subreddit_delay_max} seconds")
        print(f"Cycle delays: {self.config.cycle_delay_min}-{self.config.cycle_delay_max} seconds")
        if self.config.dry_run:
            print("DRY RUN MODE - No data will be written to database")
        if self.config.mock:
            print("MOCK MODE - Using mock data")
        print("=" * 80)
        print()
        
        try:
            while self.running:
                if self.config.max_cycles and self.cycle >= self.config.max_cycles:
                    print(f"\nReached max cycles ({self.config.max_cycles}). Stopping.")
                    break
                
                results = self.crawl_cycle()
                
                # Call callback if provided
                if on_cycle_complete:
                    on_cycle_complete(results)
                
                # Delay between cycles (if not at max)
                if not self.config.max_cycles or self.cycle < self.config.max_cycles:
                    self.random_delay(
                        self.config.cycle_delay_min,
                        self.config.cycle_delay_max,
                        "Between cycles"
                    )
                    
        except KeyboardInterrupt:
            print()
            print("=" * 80)
            print("Crawler stopped by user")
            print(f"Completed {self.cycle} cycle(s)")
            print("=" * 80)
        except Exception as e:
            print()
            print("=" * 80)
            print(f"FATAL ERROR: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.running = False
    
    def stop(self):
        """Stop the crawler gracefully."""
        self.running = False

