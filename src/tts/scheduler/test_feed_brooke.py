#!/usr/bin/env python3
"""Test feed engine with r/BrookeMonkTheSecond subreddit."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection


def main():
    """Test polling r/BrookeMonkTheSecond."""
    print("=" * 60)
    print("feed.me - Testing with r/BrookeMonkTheSecond")
    print("=" * 60)
    
    # Initialize with mock mode for first test
    use_mock = "--real" not in sys.argv
    if use_mock:
        print("\nUsing MOCK mode (no real network requests)")
        print("Add --real flag to use real Reddit API")
    else:
        print("\nUsing REAL Reddit API (will make network requests)")
    
    # Initialize adapter
    reddit = RedditAdapter(mock=use_mock, delay_min=2.0, delay_max=5.0)
    
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
            print("\nRunning schema migration...")
            with open(migration_path) as f:
                migration = f.read()
            # Split by semicolons and execute each statement
            statements = [s.strip() for s in migration.split(";") if s.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        neo4j.execute_write(stmt)
                    except Exception as e:
                        # Ignore "already exists" errors
                        if "already exists" not in str(e).lower():
                            print(f"  Migration note: {e}")
            print("Schema migration complete")
    except Exception as e:
        print(f"Warning: Could not run migration: {e}")
    
    # Initialize polling engine
    dry_run = "--dry-run" in sys.argv or use_mock
    engine = PollingEngine(reddit, neo4j, dry_run=dry_run)
    
    # Poll the subreddit
    subreddit = "BrookeMonkTheSecond"
    print(f"\nPolling r/{subreddit}...")
    
    posts = engine.poll_source(
        source=subreddit,
        sort="new",
        max_pages=3 if use_mock else None,  # Limit pages in mock mode
        limit_per_page=100,
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    print(f"Total posts collected: {len(posts)}")
    
    if posts:
        # Show sample posts
        print("\nSample posts:")
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post.title[:60]}...")
            print(f"   ID: {post.id} | Score: {post.score} | Comments: {post.num_comments}")
            print(f"   Created: {post.created_utc}")
        
        if len(posts) > 5:
            print(f"\n... and {len(posts) - 5} more posts")
        
        # Get subreddit metadata
        print("\nFetching subreddit metadata...")
        metadata = reddit.fetch_source_metadata(subreddit)
        if metadata:
            print(f"Subreddit: r/{metadata.name}")
            if metadata.subscribers:
                print(f"Subscribers: {metadata.subscribers:,}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())








