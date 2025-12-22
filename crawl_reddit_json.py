#!/usr/bin/env python3
"""
Reddit JSON API Crawler - Alternative to RSS feed method.

Uses Reddit's public JSON API endpoints which provide:
- Direct image URLs (i.redd.it, imgur, etc.)
- Better metadata (scores, comments, upvote_ratio)
- Ability to filter for image posts specifically

This is slower but more reliable for getting image posts.
"""

import sys
import time
import random
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection
from feed.utils import filter_image_posts


def crawl_subreddit_images(
    subreddit: str,
    target_images: int = 100,
    delay_min: float = 30.0,
    delay_max: float = 60.0,
    save_to_db: bool = True,
):
    """
    Crawl a subreddit using JSON API, collecting image posts.
    
    Args:
        subreddit: Subreddit name (with or without r/ prefix)
        target_images: Target number of image posts to collect
        delay_min: Minimum delay between requests (seconds)
        delay_max: Maximum delay between requests (seconds)
        save_to_db: If True, save posts to Neo4j database
    """
    # Clean subreddit name
    subreddit = subreddit.replace("r/", "").replace("/r/", "").strip()
    
    print("=" * 70)
    print("Reddit JSON API Crawler (Image Posts)")
    print("=" * 70)
    print(f"\nTarget: Collect {target_images} image posts from r/{subreddit}")
    print(f"Rate limit: {delay_min}-{delay_max} seconds between requests")
    print(f"Method: Reddit JSON API (gets direct image URLs)")
    
    if save_to_db:
        try:
            neo4j = get_connection()
            print(f"\nConnected to Neo4j: {neo4j.uri}")
        except Exception as e:
            print(f"\nError connecting to Neo4j: {e}")
            return 1
    else:
        print("\nDRY RUN MODE - Posts will not be saved to database")
        neo4j = None
    
    # Initialize adapter with slow, respectful delays
    reddit = RedditAdapter(
        mock=False,
        delay_min=delay_min,
        delay_max=delay_max,
    )
    
    if save_to_db:
        engine = PollingEngine(reddit, neo4j, dry_run=False)
    
    all_posts = []
    image_posts = []
    after = None
    page = 0
    max_pages = 50  # Safety limit
    
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("Starting crawl...")
    print("=" * 70 + "\n")
    
    while len(image_posts) < target_images and page < max_pages:
        page += 1
        print(f"--- Page {page} ---")
        
        # Fetch posts from Reddit JSON API
        posts, next_after = reddit.fetch_posts(
            source=subreddit,
            sort="new",
            limit=100,  # Max per page
            after=after,
        )
        
        if not posts:
            print("No more posts available")
            break
        
        all_posts.extend(posts)
        print(f"Fetched {len(posts)} posts (total checked: {len(all_posts)})")
        
        # Filter for image posts
        page_images = filter_image_posts(posts)
        
        # Deduplicate against what we already have
        existing_ids = {p.id for p in image_posts}
        new_images = [p for p in page_images if p.id not in existing_ids]
        
        if new_images:
            image_posts.extend(new_images)
            print(f"  -> Found {len(new_images)} new image posts (total images: {len(image_posts)})")
            
            # Save to database if requested
            if save_to_db and neo4j:
                try:
                    engine._store_posts(new_images, subreddit)
                    print(f"  -> Saved {len(new_images)} posts to database")
                except Exception as e:
                    print(f"  -> Warning: Error saving posts: {e}")
        else:
            print(f"  -> Found {len(page_images)} image posts (all duplicates)")
        
        # Check if we've reached our target
        if len(image_posts) >= target_images:
            image_posts = image_posts[:target_images]
            print(f"\n✓ Reached target of {target_images} image posts!")
            break
        
        after = next_after
        if not after:
            print("Reached end of available posts")
            break
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("Crawl Complete")
    print("=" * 70)
    print(f"\nTotal posts checked: {len(all_posts)}")
    print(f"Image posts collected: {len(image_posts)}")
    print(f"Total time: {elapsed_time / 60:.1f} minutes")
    
    if image_posts:
        print(f"\nSample image URLs collected:")
        for i, post in enumerate(image_posts[:5], 1):
            print(f"  {i}. {post.title[:60]}")
            print(f"     {post.url[:80]}")
    
    return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Crawl Reddit using JSON API to collect image posts"
    )
    parser.add_argument(
        "subreddit",
        help="Subreddit name (e.g., BrookeMonkTheSecond)",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=100,
        help="Target number of image posts (default: 100)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=30.0,
        help="Minimum delay between requests (default: 30 seconds)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=60.0,
        help="Maximum delay between requests (default: 60 seconds)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save to database (dry run mode)",
    )
    
    args = parser.parse_args()
    
    return crawl_subreddit_images(
        subreddit=args.subreddit,
        target_images=args.target,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        save_to_db=not args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())

