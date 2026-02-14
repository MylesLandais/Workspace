import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.models.post import Post
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

def pull_recent_posts(subreddit_name: str, hours: int, ingest: bool = False):
    print(f"Pulling posts from r/{subreddit_name} for the last {hours} hours...")
    
    adapter = RedditAdapter()
    neo4j = get_connection() if ingest else None
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    all_posts = []
    after = None
    page = 0
    stored_count = 0
    
    while True:
        page += 1
        print(f"Fetching page {page}...")
        
        posts, next_after = adapter.fetch_posts(
            source=subreddit_name,
            sort="new",
            limit=100,
            after=after
        )
        
        if not posts:
            print("No posts returned.")
            break
            
        # Check timestamps
        new_posts = []
        stop_fetching = False
        
        for post in posts:
            if post.created_utc >= cutoff_time:
                new_posts.append(post)
            else:
                # We found a post older than the cutoff, so we can stop
                stop_fetching = True
        
        if ingest and neo4j:
            print(f"  -> Ingesting {len(new_posts)} posts to Neo4j...")
            for post in new_posts:
                if store_post(neo4j, post):
                    stored_count += 1
        
        all_posts.extend(new_posts)
        print(f"  -> Found {len(new_posts)} recent posts in this batch.")
        
        if stop_fetching:
            print(f"Reached posts older than {cutoff_time}. Stopping.")
            break
            
        if not next_after:
            print("No more pages available.")
            break
            
        after = next_after
        time.sleep(2) # Politeness
        
    print(f"\nTotal posts found in the last {hours} hours: {len(all_posts)}")
    if ingest:
        print(f"Total posts stored in Neo4j: {stored_count}")
    
    for i, post in enumerate(all_posts, 1):
        print(f"{i}. [{post.created_utc}] {post.title} ({post.url})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull recent Reddit posts.")
    parser.add_argument("subreddit", help="Subreddit name")
    parser.add_argument("--hours", type=int, default=12, help="Hours to look back")
    parser.add_argument("--ingest", action="store_true", help="Store posts in Neo4j")
    
    args = parser.parse_args()
    
    try:
        pull_recent_posts(args.subreddit, args.hours, args.ingest)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
