#!/usr/bin/env python3
"""
Crawl related threads and build relationship graph.

This script:
1. Starts with a seed thread URL
2. Crawls the thread and extracts all Reddit URLs from comments/posts
3. Recursively crawls discovered threads (with depth limit)
4. Builds a knowledge graph of thread relationships

Example usage:
    python crawl_related_threads.py \
        --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
        --depth 2 \
        --max-threads 50
"""

import sys
import argparse
from pathlib import Path
from typing import Set, List, Dict, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.thread_storage import store_thread_from_crawl_result
from feed.utils.reddit_url_extractor import extract_reddit_urls, extract_post_id_from_permalink
from reddit_thread_crawler import crawl_thread, random_delay

# Delay settings (can be overridden with --speed)
THREAD_DELAY_MIN = 15.0
THREAD_DELAY_MAX = 30.0


def find_related_threads(
    neo4j,
    seed_url: str,
    max_depth: int = 2,
    max_threads: int = 50,
    visited: Set[str] = None,
    current_depth: int = 0,
) -> Dict[str, Any]:
    """
    Recursively crawl threads starting from a seed URL.
    
    Args:
        neo4j: Neo4j connection
        seed_url: Starting Reddit thread URL
        max_depth: Maximum recursion depth
        max_threads: Maximum total threads to crawl
        visited: Set of already visited post IDs
        current_depth: Current recursion depth
    
    Returns:
        Dictionary with crawl statistics
    """
    if visited is None:
        visited = set()
    
    stats = {
        "total_crawled": 0,
        "total_relationships": 0,
        "depth_reached": current_depth,
        "errors": [],
    }
    
    # Extract post ID from seed URL
    seed_post_id = extract_post_id_from_permalink(seed_url)
    if not seed_post_id:
        print(f"ERROR: Could not extract post ID from {seed_url}")
        stats["errors"].append(f"Invalid seed URL: {seed_url}")
        return stats
    
    if seed_post_id in visited:
        print(f"Already visited {seed_post_id}, skipping")
        return stats
    
    # Check if we've hit limits
    if len(visited) >= max_threads:
        print(f"Hit max_threads limit ({max_threads}), stopping")
        return stats
    
    if current_depth >= max_depth:
        print(f"Hit max_depth limit ({max_depth}), stopping")
        return stats
    
    visited.add(seed_post_id)
    stats["total_crawled"] = 1
    
    print("\n" + "=" * 80)
    print(f"[Depth {current_depth}] Crawling seed thread: {seed_url}")
    print(f"Post ID: {seed_post_id}")
    print("=" * 80)
    
    # Initialize Reddit adapter
    reddit = RedditAdapter(
        mock=False,
        delay_min=2.0,
        delay_max=5.0,
    )
    
    # Crawl the thread
    output_dir = Path("./data/reddit_threads/related")
    try:
        result = crawl_thread(reddit, seed_url, output_dir, save_images=True, save_comments=True)
        
        if not result.get("success"):
            print(f"Failed to crawl {seed_url}")
            stats["errors"].append(f"Failed to crawl: {seed_url}")
            return stats
        
        # Store in Neo4j (this will automatically extract relationships)
        try:
            store_thread_from_crawl_result(neo4j, result)
            print("  Stored in Neo4j with relationships")
        except Exception as e:
            print(f"  Error storing in Neo4j: {e}")
            stats["errors"].append(f"Neo4j storage error: {e}")
        
        # Extract URLs from the crawled thread
        discovered_urls = []
        
        # From post selftext
        post_data = result.get("post", {})
        if post_data.get("selftext"):
            urls = extract_reddit_urls(post_data["selftext"])
            discovered_urls.extend(urls)
        
        # From comments
        for comment in result.get("comments", []):
            if comment.get("body"):
                urls = extract_reddit_urls(comment["body"])
                discovered_urls.extend(urls)
        
        # Deduplicate by post_id
        unique_threads = {}
        for url_info in discovered_urls:
            post_id = url_info.get("post_id")
            if post_id and post_id not in unique_threads:
                unique_threads[post_id] = url_info
        
        print(f"\n  Discovered {len(unique_threads)} unique related threads")
        stats["total_relationships"] = len(unique_threads)
        
        # Recursively crawl discovered threads
        if current_depth < max_depth - 1:
            for idx, (post_id, url_info) in enumerate(unique_threads.items(), 1):
                if len(visited) >= max_threads:
                    break
                
                if post_id in visited:
                    continue
                
                permalink = url_info.get("permalink") or url_info.get("url")
                if not permalink:
                    continue
                
                # Build full URL if needed
                if permalink.startswith("/"):
                    full_url = f"https://www.reddit.com{permalink}"
                elif not permalink.startswith("http"):
                    continue
                else:
                    full_url = permalink
                
                print(f"\n  [{idx}/{len(unique_threads)}] Following link to: {full_url}")
                
                # Delay before next crawl
                random_delay(THREAD_DELAY_MIN, THREAD_DELAY_MAX, f"Before crawling related thread")
                
                # Recursively crawl
                sub_stats = find_related_threads(
                    neo4j=neo4j,
                    seed_url=full_url,
                    max_depth=max_depth,
                    max_threads=max_threads,
                    visited=visited,
                    current_depth=current_depth + 1,
                )
                
                stats["total_crawled"] += sub_stats["total_crawled"]
                stats["total_relationships"] += sub_stats["total_relationships"]
                stats["depth_reached"] = max(stats["depth_reached"], sub_stats["depth_reached"])
                stats["errors"].extend(sub_stats["errors"])
        
    except Exception as e:
        print(f"ERROR crawling {seed_url}: {e}")
        stats["errors"].append(f"Error: {e}")
    
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Crawl related Reddit threads and build relationship graph"
    )
    parser.add_argument(
        "--seed",
        required=True,
        help="Seed Reddit thread URL to start from",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum recursion depth (default: 2)",
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=50,
        help="Maximum total threads to crawl (default: 50)",
    )
    parser.add_argument(
        "--no-neo4j",
        action="store_true",
        help="Skip storing results in Neo4j",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use fast parallel crawler instead of sequential",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of parallel workers (default: 3, only with --fast)",
    )
    
    args = parser.parse_args()
    
    # Initialize Neo4j
    neo4j = None
    if not args.no_neo4j:
        try:
            neo4j = get_connection()
            print(f"Connected to Neo4j: {neo4j.uri}")
            
            # Run migrations
            migration_paths = [
                Path(__file__).parent / "src" / "feed" / "storage" / "migrations" / "006_thread_comments_images.cypher",
                Path(__file__).parent / "src" / "feed" / "storage" / "migrations" / "007_thread_relationships.cypher",
            ]
            
            for migration_path in migration_paths:
                if migration_path.exists():
                    print(f"Running migration: {migration_path.name}")
                    with open(migration_path) as f:
                        migration = f.read()
                    statements = [s.strip() for s in migration.split(";") if s.strip()]
                    for stmt in statements:
                        if stmt:
                            try:
                                neo4j.execute_write(stmt)
                            except Exception as e:
                                if "already exists" not in str(e).lower() and "constraint" not in str(e).lower():
                                    print(f"  Migration warning: {e}")
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j: {e}")
            print("Continuing without graph storage...")
            neo4j = None
    
    if not neo4j and not args.no_neo4j:
        print("ERROR: Neo4j required for relationship storage")
        return 1
    
    # Start crawling
    print("\n" + "=" * 80)
    print("RELATED THREAD CRAWLER")
    print("=" * 80)
    print(f"Seed URL: {args.seed}")
    print(f"Max depth: {args.depth}")
    print(f"Max threads: {args.max_threads}")
    print("=" * 80)
    
    stats = find_related_threads(
        neo4j=neo4j,
        seed_url=args.seed,
        max_depth=args.depth,
        max_threads=args.max_threads,
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print("CRAWL COMPLETE")
    print("=" * 80)
    print(f"Total threads crawled: {stats['total_crawled']}")
    print(f"Total relationships discovered: {stats['total_relationships']}")
    print(f"Max depth reached: {stats['depth_reached']}")
    if stats["errors"]:
        print(f"Errors: {len(stats['errors'])}")
        for error in stats["errors"][:10]:  # Show first 10
            print(f"  - {error}")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

