#!/usr/bin/env python3
"""Slowly browse Triangl subreddit simulating user behavior."""

import sys
import time
import random
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection

def get_current_count(neo4j, subreddit):
    """Get current post count for subreddit."""
    query = """
    MATCH (s:Subreddit {name: $subreddit})<-[:POSTED_IN]-(p:Post)
    RETURN count(p) as count
    """
    result = neo4j.execute_read(query, parameters={"subreddit": subreddit})
    return result[0]["count"] if result else 0

def store_post(neo4j, post):
    """Store a post in Neo4j."""
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
        
        neo4j.execute_write(
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
        return True
    except Exception as e:
        return False

def simulate_browsing():
    """Simulate slow browsing behavior."""
    subreddit = "Triangl"
    target = 999
    
    print("=" * 60)
    print(f"SLOW BROWSER: r/{subreddit}")
    print(f"Target: {target} posts")
    print("Behavior: Random delays (3-15s) between requests")
    print("=" * 60)
    
    try:
        neo4j = get_connection()
        adapter = RedditAdapter(delay_min=2.0, delay_max=5.0)
        
        current = get_current_count(neo4j, subreddit)
        print(f"Starting with {current} posts\n")
        
        # Browsing strategies in random order
        strategies = [
            ("new", None, 50),
            ("hot", None, 50),
            ("top", "all", 50),
            ("top", "year", 50),
            ("top", "month", 50),
            ("top", "week", 50),
            ("rising", None, 25),
        ]
        
        iteration = 0
        
        while current < target:
            iteration += 1
            print(f"\n[{iteration}] Current: {current}/{target}")
            
            # Random strategy selection
            sort, time_filter, limit = random.choice(strategies)
            
            # Vary limit randomly too
            limit = random.randint(25, 75)
            
            print(f"  Strategy: {sort}" + (f"/{time_filter}" if time_filter else ""))
            print(f"  Limit: {limit}")
            
            # Random delay before fetch (simulating user reading time)
            delay = random.uniform(3.0, 15.0)
            print(f"  Reading for {delay:.1f}s...")
            time.sleep(delay)
            
            # Fetch posts
            try:
                posts, _ = adapter.fetch_posts(
                    source=subreddit,
                    sort=sort,
                    time_filter=time_filter,
                    limit=limit
                )
                
                print(f"  Fetched {len(posts)} posts")
                
                # Store them
                stored = 0
                for post in posts:
                    if store_post(neo4j, post):
                        stored += 1
                
                print(f"  Stored {stored} new posts")
                
                # Random delay after storing (simulating user interaction)
                post_delay = random.uniform(5.0, 20.0)
                print(f"  Pausing {post_delay:.1f}s...")
                time.sleep(post_delay)
                
                # Update count
                current = get_current_count(neo4j, subreddit)
                
                # Check if we've made significant progress
                if iteration % 10 == 0:
                    print(f"\n  Progress: {current}/{target} ({100*current/target:.1f}%)")
                
            except Exception as e:
                print(f"  Error: {e}")
                # Longer delay on error
                time.sleep(30.0)
                continue
            
            # Stop if we've reached target
            if current >= target:
                print(f"\n✓ Reached target of {target} posts!")
                break
        
        print(f"\nFinal count: {current} posts")
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        current = get_current_count(neo4j, subreddit)
        print(f"Final count: {current} posts")

if __name__ == "__main__":
    simulate_browsing()