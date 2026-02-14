#!/usr/bin/env python3
"""
Fast, optimized Reddit thread crawler with parallel processing and configurable speed.

Features:
- Parallel thread crawling (configurable workers)
- Configurable speed modes (slow/safe, medium, fast)
- Batch processing with queue management
- Resume capability (skip already-crawled threads)
- Progress tracking and statistics
- Smart rate limiting
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set, Dict, Any
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.thread_storage import store_thread_from_crawl_result
from feed.utils.reddit_url_extractor import extract_reddit_urls, extract_post_id_from_permalink
from reddit_thread_crawler import crawl_thread


# Speed presets
SPEED_PRESETS = {
    "slow": {
        "workers": 1,
        "delay_min": 10.0,
        "delay_max": 20.0,
        "batch_size": 1,
        "description": "Slow and safe (1 worker, 10-20s delays)",
    },
    "medium": {
        "workers": 3,
        "delay_min": 3.0,
        "delay_max": 6.0,
        "batch_size": 5,
        "description": "Medium speed (3 workers, 3-6s delays)",
    },
    "fast": {
        "workers": 5,
        "delay_min": 1.0,
        "delay_max": 3.0,
        "batch_size": 10,
        "description": "Fast (5 workers, 1-3s delays) - use with caution",
    },
    "aggressive": {
        "workers": 10,
        "delay_min": 0.5,
        "delay_max": 1.5,
        "batch_size": 20,
        "description": "Aggressive (10 workers, 0.5-1.5s delays) - may hit rate limits",
    },
}


class FastThreadCrawler:
    """Fast parallel thread crawler with queue management."""
    
    def __init__(
        self,
        neo4j,
        speed: str = "medium",
        workers: Optional[int] = None,
        delay_min: Optional[float] = None,
        delay_max: Optional[float] = None,
        resume: bool = True,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize fast crawler.
        
        Args:
            neo4j: Neo4j connection
            speed: Speed preset ("slow", "medium", "fast", "aggressive")
            workers: Override worker count
            delay_min: Override min delay
            delay_max: Override max delay
            resume: Skip already-crawled threads
            output_dir: Output directory for JSON files
        """
        self.neo4j = neo4j
        self.resume = resume
        self.output_dir = output_dir or Path("./data/reddit_threads/fast")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load speed preset
        preset = SPEED_PRESETS.get(speed, SPEED_PRESETS["medium"])
        self.workers = workers or preset["workers"]
        self.delay_min = delay_min or preset["delay_min"]
        self.delay_max = delay_max or preset["delay_max"]
        self.batch_size = preset["batch_size"]
        
        # State
        self.visited: Set[str] = set()
        self.queue: deque = deque()
        self.stats = {
            "total_crawled": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "total_relationships": 0,
            "start_time": datetime.utcnow(),
        }
        self.lock = Lock()
        
        # Load resume state
        if resume:
            self._load_resume_state()
        
        # Initialize Reddit adapter
        self.reddit = RedditAdapter(
            mock=False,
            delay_min=self.delay_min,
            delay_max=self.delay_max,
        )
        
        print(f"Fast Crawler initialized:")
        print(f"  Speed: {speed} ({preset['description']})")
        print(f"  Workers: {self.workers}")
        print(f"  Delays: {self.delay_min}-{self.delay_max}s")
        print(f"  Resume: {self.resume} ({len(self.visited)} already visited)")
    
    def _load_resume_state(self):
        """Load already-crawled threads from Neo4j."""
        try:
            query = """
            MATCH (p:Post)
            WHERE p.id IS NOT NULL
            RETURN DISTINCT p.id as id
            LIMIT 10000
            """
            result = self.neo4j.execute_read(query)
            self.visited = {row["id"] for row in result}
            print(f"  Loaded {len(self.visited)} already-crawled threads")
        except Exception as e:
            print(f"  Warning: Could not load resume state: {e}")
            self.visited = set()
    
    def _save_progress(self):
        """Save progress to file."""
        progress_file = self.output_dir / "crawl_progress.json"
        progress = {
            "visited": list(self.visited),
            "stats": {
                **self.stats,
                "start_time": self.stats["start_time"].isoformat(),
            },
        }
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)
    
    def add_seed(self, url: str):
        """Add seed URL to queue."""
        post_id = extract_post_id_from_permalink(url)
        if post_id and post_id not in self.visited:
            self.queue.append(url)
            print(f"  Added seed: {url} (post_id: {post_id})")
    
    def add_seeds(self, urls: List[str]):
        """Add multiple seed URLs."""
        for url in urls:
            self.add_seed(url)
    
    def _crawl_single_thread(self, url: str) -> Dict[str, Any]:
        """Crawl a single thread (worker function)."""
        post_id = extract_post_id_from_permalink(url)
        
        if not post_id:
            return {"success": False, "error": "Could not extract post ID", "url": url}
        
        # Check if already visited
        with self.lock:
            if post_id in self.visited:
                return {"success": False, "skipped": True, "post_id": post_id}
        
        try:
            # Crawl thread
            result = crawl_thread(
                self.reddit,
                url,
                self.output_dir,
                save_images=True,
                save_comments=True,
            )
            
            if not result.get("success"):
                with self.lock:
                    self.stats["total_errors"] += 1
                return result
            
            # Store in Neo4j
            try:
                store_thread_from_crawl_result(self.neo4j, result)
            except Exception as e:
                print(f"    Warning: Neo4j storage error: {e}")
            
            # Extract relationships
            relationships = 0
            post_data = result.get("post", {})
            if post_data.get("selftext"):
                urls = extract_reddit_urls(post_data["selftext"])
                relationships += len(urls)
            
            for comment in result.get("comments", []):
                if comment.get("body"):
                    urls = extract_reddit_urls(comment["body"])
                    relationships += len(urls)
            
            # Update stats
            with self.lock:
                self.visited.add(post_id)
                self.stats["total_crawled"] += 1
                self.stats["total_relationships"] += relationships
                
                # Add discovered URLs to queue
                all_urls = []
                if post_data.get("selftext"):
                    all_urls.extend(extract_reddit_urls(post_data["selftext"]))
                for comment in result.get("comments", []):
                    if comment.get("body"):
                        all_urls.extend(extract_reddit_urls(comment["body"]))
                
                # Deduplicate and add to queue
                for url_info in all_urls:
                    discovered_post_id = url_info.get("post_id")
                    if discovered_post_id and discovered_post_id not in self.visited:
                        permalink = url_info.get("permalink") or url_info.get("url")
                        if permalink:
                            if permalink.startswith("/"):
                                full_url = f"https://www.reddit.com{permalink}"
                            elif not permalink.startswith("http"):
                                continue
                            else:
                                full_url = permalink
                            
                            if full_url not in self.queue:
                                self.queue.append(full_url)
            
            return result
            
        except Exception as e:
            with self.lock:
                self.stats["total_errors"] += 1
            return {"success": False, "error": str(e), "url": url}
    
    def crawl(
        self,
        max_threads: Optional[int] = None,
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Start crawling with parallel workers.
        
        Args:
            max_threads: Maximum total threads to crawl
            max_depth: Maximum recursion depth (not yet implemented)
        
        Returns:
            Statistics dictionary
        """
        print("\n" + "=" * 80)
        print("Starting fast parallel crawl")
        print("=" * 80)
        print(f"Queue size: {len(self.queue)}")
        print(f"Workers: {self.workers}")
        print(f"Max threads: {max_threads or 'unlimited'}")
        print("=" * 80 + "\n")
        
        start_time = time.time()
        last_save = time.time()
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {}
            
            # Submit initial batch
            while len(futures) < self.workers and self.queue:
                url = self.queue.popleft()
                future = executor.submit(self._crawl_single_thread, url)
                futures[future] = url
            
            while futures or self.queue:
                # Check completed futures
                done, _ = as_completed(futures), None
                for future in list(futures.keys()):
                    if future.done():
                        url = futures.pop(future)
                        try:
                            result = future.result()
                            
                            if result.get("skipped"):
                                with self.lock:
                                    self.stats["total_skipped"] += 1
                                print(f"  [SKIP] {url}")
                            elif result.get("success"):
                                post_id = result.get("post_id", "unknown")
                                print(f"  [OK] {post_id} - {result.get('post', {}).get('title', '')[:60]}")
                            else:
                                error = result.get("error", "Unknown error")
                                print(f"  [ERROR] {url}: {error}")
                            
                        except Exception as e:
                            print(f"  [EXCEPTION] {url}: {e}")
                        
                        # Submit next from queue
                        if self.queue and (not max_threads or self.stats["total_crawled"] < max_threads):
                            url = self.queue.popleft()
                            future = executor.submit(self._crawl_single_thread, url)
                            futures[future] = url
                
                # Check limits
                if max_threads and self.stats["total_crawled"] >= max_threads:
                    print(f"\nReached max_threads limit ({max_threads})")
                    break
                
                # Save progress periodically
                if time.time() - last_save > 60:  # Every minute
                    self._save_progress()
                    last_save = time.time()
                
                # Small sleep to prevent busy waiting
                time.sleep(0.1)
        
        # Final save
        self._save_progress()
        
        elapsed = time.time() - start_time
        self.stats["elapsed_seconds"] = elapsed
        self.stats["end_time"] = datetime.utcnow()
        
        # Print summary
        print("\n" + "=" * 80)
        print("CRAWL COMPLETE")
        print("=" * 80)
        print(f"Total crawled: {self.stats['total_crawled']}")
        print(f"Total skipped: {self.stats['total_skipped']}")
        print(f"Total errors: {self.stats['total_errors']}")
        print(f"Total relationships: {self.stats['total_relationships']}")
        print(f"Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
        if self.stats['total_crawled'] > 0:
            print(f"Average time per thread: {elapsed/self.stats['total_crawled']:.1f}s")
        print("=" * 80)
        
        return self.stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fast parallel Reddit thread crawler with relationship discovery"
    )
    parser.add_argument(
        "--seed",
        action="append",
        help="Seed URL(s) to start from (can be used multiple times)",
    )
    parser.add_argument(
        "--seeds-file",
        type=Path,
        help="File with seed URLs (one per line)",
    )
    parser.add_argument(
        "--speed",
        choices=list(SPEED_PRESETS.keys()),
        default="medium",
        help="Speed preset (default: medium)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Override worker count",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        help="Override minimum delay (seconds)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        help="Override maximum delay (seconds)",
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        help="Maximum threads to crawl",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't skip already-crawled threads",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory",
    )
    parser.add_argument(
        "--no-neo4j",
        action="store_true",
        help="Skip Neo4j storage",
    )
    
    args = parser.parse_args()
    
    # Collect seeds
    seeds = []
    if args.seed:
        seeds.extend(args.seed)
    if args.seeds_file and args.seeds_file.exists():
        with open(args.seeds_file) as f:
            seeds.extend(line.strip() for line in f if line.strip())
    
    if not seeds:
        print("ERROR: No seed URLs provided. Use --seed or --seeds-file")
        return 1
    
    # Initialize Neo4j
    neo4j = None
    if not args.no_neo4j:
        try:
            neo4j = get_connection()
            print(f"Connected to Neo4j: {neo4j.uri}")
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j: {e}")
            if not args.no_neo4j:
                print("ERROR: Neo4j required for relationship storage")
                return 1
    
    # Initialize crawler
    crawler = FastThreadCrawler(
        neo4j=neo4j,
        speed=args.speed,
        workers=args.workers,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        resume=not args.no_resume,
        output_dir=args.output,
    )
    
    # Add seeds
    crawler.add_seeds(seeds)
    
    # Start crawling
    stats = crawler.crawl(max_threads=args.max_threads)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())







