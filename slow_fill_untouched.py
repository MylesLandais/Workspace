import sys
import time
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
        print(f"    ⚠ Warning: Error storing post {post.id}: {e}")
        return False

def get_untouched_subreddits(neo4j):
    """Get subreddits with 0 posts."""
    query = """
    MATCH (s:Subreddit)
    OPTIONAL MATCH (p:Post)-[:POSTED_IN]->(s)
    WITH s, count(p) as post_count
    WHERE post_count = 0
    RETURN s.name as name
    ORDER BY s.name
    """
    results = neo4j.execute_read(query)
    return [record["name"] for record in results]

def main():
    print("=" * 60)
    print("SLOW FILL UNTOUCHED SUBREDDITS")
    print("Strategy: Top 33 posts (Month) | Delay: 5s")
    print("=" * 60)
    
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return

    # Get target list
    targets = get_untouched_subreddits(neo4j)
    print(f"Found {len(targets)} subreddits with 0 posts.")
    
    if not targets:
        print("No subreddits to update.")
        return

    adapter = RedditAdapter(delay_min=1.0, delay_max=3.0)
    
    for i, sub in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] Processing r/{sub}...")
        try:
            # Fetch TOP posts from this MONTH, limit 33
            posts, _ = adapter.fetch_posts(
                source=sub,
                sort="top",
                time_filter="month",
                limit=33
            )
            
            if not posts:
                print(f"  No posts found for {sub}")
            else:
                print(f"  Fetched {len(posts)} posts. Storing...")
                count = 0
                for post in posts:
                    if store_post(neo4j, post):
                        count += 1
                print(f"  ✓ Stored {count} posts for r/{sub}")
            
            # SLOW PASS - Sleep 5 seconds
            print("  Sleeping 5s...")
            time.sleep(5)
            
        except Exception as e:
            print(f"  ✗ Error processing {sub}: {e}")
            # Still sleep on error to be safe
            time.sleep(5)

    print("\nDone!")

if __name__ == "__main__":
    main()
