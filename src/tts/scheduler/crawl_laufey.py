#!/usr/bin/env python3
"""
Simple Reddit crawler for laufeyhot subreddit.
Bypasses PollingEngine import issues by directly storing to Neo4j.
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection
from feed.utils import filter_image_posts


def store_posts_directly(posts, subreddit_name, neo4j):
    """Store posts directly to Neo4j without PollingEngine."""
    if not posts:
        return
    
    # Create subreddit node
    subreddit_query = """
    MERGE (s:Subreddit {name: $name})
    ON CREATE SET s.created_at = datetime()
    RETURN s
    """
    neo4j.execute_write(subreddit_query, parameters={"name": subreddit_name})
    
    # Store each post
    for post in posts:
        created_timestamp = int(post.created_utc.timestamp())
        
        post_query = """
        MERGE (p:Post {id: $id})
        SET p.title = $title,
            p.created_utc = datetime({epochSeconds: $created_utc}),
            p.score = $score,
            p.num_comments = $num_comments,
            p.upvote_ratio = $upvote_ratio,
            p.over_18 = $over_18,
            p.url = $url,
            p.selftext = $selftext,
            p.permalink = $permalink,
            p.updated_at = datetime()
        WITH p
        MATCH (s:Subreddit {name: $subreddit})
        MERGE (p)-[:POSTED_IN]->(s)
        """
        
        neo4j.execute_write(
            post_query,
            parameters={
                "id": post.id,
                "title": post.title,
                "created_utc": created_timestamp,
                "score": post.score,
                "num_comments": post.num_comments,
                "upvote_ratio": post.upvote_ratio,
                "over_18": post.over_18,
                "url": post.url,
                "selftext": post.selftext,
                "permalink": post.permalink,
                "subreddit": post.subreddit,
            },
        )
        
        # Create user node if author exists
        if post.author:
            user_query = """
            MERGE (u:User {username: $username})
            ON CREATE SET u.created_at = datetime()
            WITH u
            MATCH (p:Post {id: $post_id})
            MERGE (u)-[:POSTED]->(p)
            """
            neo4j.execute_write(
                user_query,
                parameters={"username": post.author, "post_id": post.id},
            )


def crawl_laufeyhot(target_images=300, delay_min=30.0, delay_max=60.0):
    """Crawl r/laufeyhot for image posts."""
    subreddit = "laufeyhot"
    
    print("=" * 70)
    print("Reddit JSON API Crawler - r/laufeyhot")
    print("=" * 70)
    print(f"\nTarget: {target_images} image posts")
    print(f"Rate limit: {delay_min}-{delay_max} seconds between requests")
    
    try:
        neo4j = get_connection()
        print(f"\nConnected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return 1
    
    # Check existing posts
    result = neo4j.execute_read(
        "MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name}) RETURN count(p) as total",
        parameters={"name": subreddit}
    )
    existing_count = result[0]["total"] if result else 0
    print(f"Existing posts in database: {existing_count}")
    
    # Initialize adapter
    reddit = RedditAdapter(mock=False, delay_min=delay_min, delay_max=delay_max)
    
    all_posts = []
    image_posts = []
    after = None
    page = 0
    max_pages = 500  # Safety limit
    
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("Starting crawl...")
    print("=" * 70 + "\n")
    
    while len(image_posts) < target_images and page < max_pages:
        page += 1
        print(f"--- Page {page} ---")
        
        # Fetch posts
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
        print(f"Fetched {len(posts)} posts (total checked: {len(all_posts)})")
        
        # Filter for images
        page_images = filter_image_posts(posts)
        
        # Check for duplicates
        post_ids = [p.id for p in page_images]
        existing = neo4j.execute_read(
            "MATCH (p:Post) WHERE p.id IN $ids RETURN p.id as id",
            parameters={"ids": post_ids}
        )
        existing_ids = {r["id"] for r in existing}
        new_images = [p for p in page_images if p.id not in existing_ids]
        
        if new_images:
            image_posts.extend(new_images)
            print(f"  -> Found {len(new_images)} new image posts (total: {len(image_posts)})")
            
            # Store to database
            store_posts_directly(new_images, subreddit, neo4j)
            print(f"  -> Saved {len(new_images)} posts to database")
        else:
            print(f"  -> Found {len(page_images)} image posts (all duplicates)")
        
        if len(image_posts) >= target_images:
            image_posts = image_posts[:target_images]
            print(f"\n✓ Reached target of {target_images} image posts!")
            break
        
        after = next_after
        if not after:
            print("Reached end of available posts")
            break
        
        # Delay before next request
        delay = random.uniform(delay_min, delay_max)
        print(f"  Waiting {delay:.1f} seconds before next request...")
        time.sleep(delay)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("Crawl Complete")
    print("=" * 70)
    print(f"\nTotal posts checked: {len(all_posts)}")
    print(f"Image posts collected: {len(image_posts)}")
    print(f"Total time: {elapsed / 60:.1f} minutes")
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl r/laufeyhot")
    parser.add_argument("--target", type=int, default=300, help="Target image posts")
    parser.add_argument("--delay-min", type=float, default=30.0, help="Min delay (seconds)")
    parser.add_argument("--delay-max", type=float, default=60.0, help="Max delay (seconds)")
    
    args = parser.parse_args()
    
    sys.exit(crawl_laufeyhot(
        target_images=args.target,
        delay_min=args.delay_min,
        delay_max=args.delay_max
    ))






