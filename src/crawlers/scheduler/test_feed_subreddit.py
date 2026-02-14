#!/usr/bin/env python3
"""Fetch latest image posts from any subreddit with slow, human-like polling."""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection
from feed.utils import filter_image_posts


def main():
    """Fetch latest image posts from a subreddit."""
    parser = argparse.ArgumentParser(description="Fetch image posts from a subreddit")
    parser.add_argument(
        "subreddit",
        nargs="?",
        default="BrookeMonkTheSecond",
        help="Subreddit name (with or without r/ prefix)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of image posts to collect (default: 10)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save posts to Neo4j database",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=5.0,
        help="Minimum delay between requests in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=10.0,
        help="Maximum delay between requests in seconds (default: 10.0)",
    )
    
    args = parser.parse_args()
    
    # Clean subreddit name
    subreddit = args.subreddit.replace("r/", "").replace("/r/", "").replace("https://www.reddit.com/r/", "").replace("/", "")
    
    print("=" * 70)
    print(f"feed.me - Fetching Latest {args.count} Image Posts from r/{subreddit}")
    print("=" * 70)
    print(f"\nUsing SLOW mode with human-like delays ({args.delay_min}-{args.delay_max} seconds between requests)")
    print("This will take approximately 1-2 minutes to complete...\n")
    
    # Initialize adapter with slow delays
    reddit = RedditAdapter(
        mock=False,  # Use real API
        delay_min=args.delay_min,
        delay_max=args.delay_max,
    )
    
    # Initialize Neo4j connection
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        print("Make sure NEO4J_URI and NEO4J_PASSWORD are set in .env")
        return 1
    
    # Run migration if needed
    try:
        migration_path = Path(__file__).parent / "src" / "feed" / "storage" / "migrations" / "001_initial_schema.cypher"
        if migration_path.exists():
            with open(migration_path) as f:
                migration = f.read()
            statements = [s.strip() for s in migration.split(";") if s.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        neo4j.execute_write(stmt)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            pass  # Silent for migration
    except Exception:
        pass
    
    # Initialize polling engine
    engine = PollingEngine(reddit, neo4j, dry_run=not args.save)
    
    # Poll the subreddit, collecting until we have enough images
    print(f"\nPolling r/{subreddit} for image posts...")
    print("This may take a while as we filter for images only...\n")
    
    all_posts = []
    image_posts = []
    after = None
    page = 0
    max_pages = 20  # Safety limit
    
    while len(image_posts) < args.count and page < max_pages:
        page += 1
        print(f"--- Page {page} ---")
        
        posts, next_after = reddit.fetch_posts(
            source=subreddit,
            sort="new",
            limit=100,
            after=after,
        )
        
        if not posts:
            print("No more posts available")
            break
        
        all_posts.extend(posts)
        print(f"Fetched {len(posts)} posts (total: {len(all_posts)})")
        
        # Filter for images
        page_images = filter_image_posts(posts)
        image_posts.extend(page_images)
        
        print(f"  -> Found {len(page_images)} image posts (total images: {len(image_posts)})")
        
        if len(image_posts) >= args.count:
            image_posts = image_posts[:args.count]  # Keep only requested count
            print(f"\n✓ Collected {args.count} image posts!")
            break
        
        after = next_after
        if not after:
            print("Reached end of available posts")
            break
    
    # Display results
    print("\n" + "=" * 70)
    print(f"Latest {len(image_posts)} Image Posts")
    print("=" * 70)
    
    if not image_posts:
        print(f"\nNo image posts found in the latest posts.")
        print(f"Total posts checked: {len(all_posts)}")
        return 0
    
    print(f"\nFound {len(image_posts)} image posts:\n")
    
    for i, post in enumerate(image_posts, 1):
        print(f"{i}. {post.title[:70]}")
        print(f"   URL: {post.url}")
        print(f"   Score: {post.score} | Comments: {post.num_comments} | Ratio: {post.upvote_ratio:.2f}")
        print(f"   Created: {post.created_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if post.author:
            print(f"   Author: u/{post.author}")
        print()
    
    # Save to database if requested
    if args.save:
        print("Saving to database...")
        engine.dry_run = False
        engine._store_posts(image_posts, subreddit)
        print("Saved to Neo4j!")
    else:
        print("(Add --save flag to store these posts in Neo4j)")
    
    print("\n" + "=" * 70)
    print("Complete!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())








