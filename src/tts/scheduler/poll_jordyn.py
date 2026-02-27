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

JORDYN_SUBS = [
    "JordynJonesBooty", 
    "JordynJonesCandy", 
    "JordynJones_gooners", 
    "jordynjonesbody", 
    "JordynJonesSimp", 
    "JordynJonesSnark",
    "jordynjones"
]

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

def main():
    print("=" * 60)
    print("POLLING JORDYN JONES SUBREDDITS")
    print("Strategy: Newest 20 posts | Delay: 5s")
    print("=" * 60)
    
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return

    adapter = RedditAdapter(delay_min=1.0, delay_max=3.0)
    
    for i, sub in enumerate(JORDYN_SUBS, 1):
        print(f"\n[{i}/{len(JORDYN_SUBS)}] Processing r/{sub}...")
        try:
            # Fetch NEW posts, limit 20
            posts, _ = adapter.fetch_posts(
                source=sub,
                sort="new",
                limit=20
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
            time.sleep(5)

    print("\nDone!")

if __name__ == "__main__":
    main()
