import sys
import time
import random
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection

def store_post(neo4j, post):
    """Store post in Neo4j."""
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
        print(f"      ⚠ Error storing post {post.id}: {e}")
        return False

def get_low_data_subreddits(neo4j, limit=100):
    """Get subreddits with fewer than 100 posts, sorted by count."""
    query = """
    MATCH (s:Subreddit)
    OPTIONAL MATCH (p:Post)-[:POSTED_IN]->(s)
    WITH s, count(p) as post_count
    WHERE post_count < 100
    RETURN s.name as name, post_count
    ORDER BY post_count ASC
    """
    results = neo4j.execute_read(query)
    return [(record["name"], record["post_count"]) for record in results]

def sleep_random(min_s, max_s, label=""):
    delay = random.uniform(min_s, max_s)
    print(f"    ⏳ Sleeping {delay:.1f}s {label}...")
    time.sleep(delay)

def main():
    print("=" * 70)
    print("SLOW INDEXING: TOP POSTS (WEEK/MONTH/YEAR)")
    print("Target: Subreddits with < 100 posts")
    print("Strategy: Polite, slow delays, avoid rate limits")
    print("=" * 70)
    
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return

    # Get target list
    targets = get_low_data_subreddits(neo4j)
    print(f"Found {len(targets)} subreddits with < 100 posts.")
    
    if not targets:
        print("No subreddits need backfilling.")
        return

    adapter = RedditAdapter(delay_min=2.0, delay_max=5.0)
    
    # We'll limit how many subreddits we do in one run to avoid running for hours
    # Let's try to process all of them, but user said "go slow". 
    # With ~100 subs, 3 requests each + delays ~ 30-40s per sub = ~50 mins.
    # That fits within the tool timeout if we don't hit too many timeouts.
    
    for i, (sub, count) in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] Processing r/{sub} (Current posts: {count})")
        
        try:
            # 1. TOP WEEKLY
            print("  1. Fetching Top (Week)...")
            posts, _ = adapter.fetch_posts(source=sub, sort="top", time_filter="week", limit=25)
            if posts:
                stored = sum(1 for p in posts if store_post(neo4j, p))
                print(f"     ✓ Stored {stored} posts")
            else:
                print("     - No posts found")
            
            sleep_random(5, 10, "between filters")

            # 2. TOP MONTHLY
            print("  2. Fetching Top (Month)...")
            posts, _ = adapter.fetch_posts(source=sub, sort="top", time_filter="month", limit=25)
            if posts:
                stored = sum(1 for p in posts if store_post(neo4j, p))
                print(f"     ✓ Stored {stored} posts")
            else:
                print("     - No posts found")
            
            sleep_random(5, 10, "between filters")

            # 3. TOP YEARLY
            print("  3. Fetching Top (Year)...")
            posts, _ = adapter.fetch_posts(source=sub, sort="top", time_filter="year", limit=25)
            if posts:
                stored = sum(1 for p in posts if store_post(neo4j, p))
                print(f"     ✓ Stored {stored} posts")
            else:
                print("     - No posts found")
            
            # Longer delay between subreddits
            sleep_random(10, 20, "between subreddits")
            
        except Exception as e:
            print(f"  ✗ Error processing r/{sub}: {e}")
            sleep_random(10, 20, "after error")

    print("\n" + "=" * 70)
    print("Indexing Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
