#!/usr/bin/env python3
"""
Crawl Jordyn Jones subreddits using Reddit JSON API.
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


def ensure_creator_node(neo4j, creator_slug="jordyn-jones", creator_name="Jordyn Jones"):
    """Ensure Creator node exists for the entity."""
    from uuid import uuid4
    
    creator_query = """
    MERGE (c:Creator {slug: $slug})
    ON CREATE SET
        c.uuid = $uuid,
        c.name = $name,
        c.slug = $slug,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.updated_at = datetime()
    RETURN c
    """
    
    neo4j.execute_write(
        creator_query,
        parameters={
            "slug": creator_slug,
            "uuid": str(uuid4()),
            "name": creator_name,
        },
    )


def link_subreddit_to_creator(neo4j, subreddit_name, creator_slug="jordyn-jones"):
    """Link subreddit to Creator node."""
    link_query = """
    MATCH (c:Creator {slug: $creator_slug})
    MATCH (s:Subreddit {name: $subreddit})
    MERGE (c)-[r:HAS_SOURCE]->(s)
    ON CREATE SET
        r.source_type = 'reddit',
        r.discovered_at = datetime(),
        r.created_at = datetime()
    ON MATCH SET
        r.updated_at = datetime()
    RETURN r
    """
    
    neo4j.execute_write(
        link_query,
        parameters={
            "creator_slug": creator_slug,
            "subreddit": subreddit_name,
        },
    )


def store_posts_directly(posts, subreddit_name, neo4j, creator_slug="jordyn-jones"):
    """Store posts directly to Neo4j without PollingEngine."""
    if not posts:
        return 0
    
    stored = 0
    
    # Create subreddit node
    subreddit_query = """
    MERGE (s:Subreddit {name: $name})
    ON CREATE SET s.created_at = datetime()
    RETURN s
    """
    neo4j.execute_write(subreddit_query, parameters={"name": subreddit_name})
    
    # Link subreddit to creator
    link_subreddit_to_creator(neo4j, subreddit_name, creator_slug)
    
    # Store each post
    for post in posts:
        try:
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
                p.entity_matched = $entity,
                p.updated_at = datetime()
            WITH p
            MATCH (s:Subreddit {name: $subreddit})
            MERGE (p)-[:POSTED_IN]->(s)
            WITH p
            MATCH (c:Creator {slug: $creator_slug})
            MERGE (p)-[:ABOUT]->(c)
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
                    "entity": "Jordyn Jones",
                    "creator_slug": creator_slug,
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
            
            stored += 1
        except Exception as e:
            print(f"  Warning: Error storing post {post.id}: {e}")
            continue
    
    return stored


def crawl_subreddit(subreddit, target_images=100, delay_min=30.0, delay_max=60.0, creator_slug="jordyn-jones"):
    """Crawl a subreddit for image posts."""
    print(f"\n{'='*70}")
    print(f"r/{subreddit}")
    print(f"{'='*70}")
    print(f"Target: {target_images} image posts")
    print(f"Rate limit: {delay_min}-{delay_max} seconds between requests")
    print(f"Creator: {creator_slug}")
    
    try:
        neo4j = get_connection()
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return 0
    
    # Ensure Creator node exists
    ensure_creator_node(neo4j, creator_slug)
    
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
    max_pages = 500
    
    while len(image_posts) < target_images and page < max_pages:
        page += 1
        print(f"  Page {page}...")
        
        # Fetch posts
        posts, next_after = reddit.fetch_posts(
            source=subreddit,
            sort="new",
            limit=100,
            after=after,
        )
        
        if not posts:
            print("  No more posts available")
            break
        
        all_posts.extend(posts)
        
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
            print(f"  -> {len(new_images)} new image posts (total: {len(image_posts)})")
            
            # Store to database
            stored = store_posts_directly(new_images, subreddit, neo4j)
            print(f"  -> Stored {stored} posts")
        else:
            print(f"  -> {len(page_images)} image posts (all duplicates)")
        
        if len(image_posts) >= target_images:
            print(f"  ✓ Reached target of {target_images} image posts!")
            break
        
        after = next_after
        if not after:
            print("  Reached end of available posts")
            break
        
        # Delay before next request
        delay = random.uniform(delay_min, delay_max)
        print(f"  Waiting {delay:.1f} seconds...")
        time.sleep(delay)
    
    # Final count
    result = neo4j.execute_read(
        "MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name}) RETURN count(p) as total",
        parameters={"name": subreddit}
    )
    final_count = result[0]["total"] if result else 0
    
    print(f"\n  Complete: {final_count} total posts ({len(image_posts)} new image posts this run)")
    return final_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl Jordyn Jones subreddits")
    parser.add_argument("--target", type=int, default=100, help="Target image posts per subreddit")
    parser.add_argument("--delay-min", type=float, default=30.0, help="Min delay (seconds)")
    parser.add_argument("--delay-max", type=float, default=60.0, help="Max delay (seconds)")
    
    args = parser.parse_args()
    
    subreddits = [
        'JordynJonesCandy',
        'JordynJonesBooty',
        'jordynjonesbody',
        'JordynJones_gooners'
    ]
    
    print("="*70)
    print("Jordyn Jones Subreddits Crawler")
    print("="*70)
    print(f"\nSubreddits: {', '.join([f'r/{s}' for s in subreddits])}")
    print(f"Target: {args.target} image posts per subreddit")
    print(f"Rate limit: {args.delay_min}-{args.delay_max} seconds between requests")
    print(f"\nStarting crawl...")
    
    results = {}
    for subreddit in subreddits:
        try:
            count = crawl_subreddit(subreddit, target_images=args.target, delay_min=args.delay_min, delay_max=args.delay_max)
            results[subreddit] = count
        except Exception as e:
            print(f"\nError crawling r/{subreddit}: {e}")
            results[subreddit] = -1
            continue
    
    print("\n" + "="*70)
    print("All Crawls Complete")
    print("="*70)
    for subreddit, count in results.items():
        if count >= 0:
            print(f"r/{subreddit}: {count} posts")
        else:
            print(f"r/{subreddit}: Failed")
    
    sys.exit(0)

