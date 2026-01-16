#!/usr/bin/env python3
"""Reddit catalog orchestrator - polls subreddit and stores new posts."""
import os
import sys
import time
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection

SUBREDDIT = os.environ.get('REDDIT_SUBREDDIT', 'lululemon')
POLL_INTERVAL = int(os.environ.get('REDDIT_POLL_INTERVAL', 1800)) # 30 minutes default
MIN_SCORE = int(os.environ.get('REDDIT_MIN_SCORE', 0)) # Minimum score to include
STORE_IMAGES = os.environ.get('REDDIT_STORE_IMAGES', 'true').lower() == 'true'

def fetch_new_posts():
    """Fetch new posts from subreddit."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetching new posts from r/{SUBREDDIT}...")
    
    try:
        adapter = RedditAdapter(delay_min=1.0, delay_max=2.0)
        posts, after = adapter.fetch_posts(
            SUBREDDIT,
            sort="new",
            limit=100
        )
        
        if not posts:
            print("  No posts found")
            return []
        
        print(f"  Fetched {len(posts)} posts")
        return posts
        
    except Exception as e:
        print(f"  Error fetching posts: {e}")
        return []

def store_posts(posts):
    """Store posts in Neo4j."""
    if not posts:
        return
    
    neo4j = get_connection()
    stored_count = 0
    skipped_count = 0
    
    for post in posts:
        try:
            # Check if already exists
            query = """
            MATCH (p:Post {id: $id})
            RETURN p.id as id
            """
            existing = neo4j.execute_read(query, parameters={"id": post.id})
            if existing:
                skipped_count += 1
                continue
            
            # Skip below minimum score
            if post.score < MIN_SCORE:
                skipped_count += 1
                continue
            
            # Convert datetime to ISO format
            created_utc = post.created_utc.isoformat() if post.created_utc else None
            
            # Store post
            store_query = """
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
            
            neo4j.execute_write(
                store_query,
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
                    "created_utc": created_utc,
                }
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
                    parameters={"username": post.author, "post_id": post.id}
                )
            
            # Store image if present
            if STORE_IMAGES and post.url:
                is_image = any(
                    ext in post.url.lower()
                    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', 'i.redd.it', 'preview.redd.it']
                )
                
                if is_image:
                    image_query = """
                    MERGE (i:Image {url: $url})
                    SET i.updated_at = datetime()
                    MERGE (p:Post {id: $post_id})
                    MERGE (p)-[:HAS_IMAGE]->(i)
                    """
                    neo4j.execute_write(
                        image_query,
                        parameters={"url": post.url, "post_id": post.id}
                    )
            
            stored_count += 1
            
        except Exception as e:
            print(f"    Warning: Error storing post {post.id}: {e}")
    
    print(f"  Stored {stored_count} new posts, skipped {skipped_count}")

def main():
    print(f"Reddit Catalog Orchestrator started for r/{SUBREDDIT}/")
    print(f"Poll interval: {POLL_INTERVAL} seconds ({POLL_INTERVAL / 60:.1f} minutes)")
    print(f"Minimum score: {MIN_SCORE}")
    print(f"Store images: {STORE_IMAGES}")
    print()
    
    while True:
        posts = fetch_new_posts()
        if posts:
            print(f"Processing {len(posts)} posts...")
            store_posts(posts)
        
        print(f"Sleeping for {POLL_INTERVAL} seconds...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
