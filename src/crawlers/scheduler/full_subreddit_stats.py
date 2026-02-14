import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def get_stats():
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    query = """
    MATCH (s:Subreddit)
    OPTIONAL MATCH (p:Post)-[:POSTED_IN]->(s)
    RETURN s.name as name, count(p) as post_count, max(p.created_utc) as last_post
    ORDER BY post_count DESC, name ASC
    """
    
    results = neo4j.execute_read(query)
    
    print(f"\n{'Subreddit':<30} | {'Posts':<8} | {'Last Post UTC':<20}")
    print("-" * 65)
    
    total_tracked_posts = 0
    
    for record in results:
        name = record["name"]
        count = record["post_count"]
        last_post = record["last_post"]
        
        if last_post:
            # Clean up the date format if it's an ISO string or similar
            try:
                # Assuming standard ISO format string, just take the date/time part part
                last_post = str(last_post).replace('T', ' ')[:19]
            except:
                pass
        else:
            last_post = "No posts"
            
        print(f"r/{name:<28} | {count:<8} | {last_post:<20}")
        total_tracked_posts += count
        
    print("-" * 65)
    print(f"Total Subreddits: {len(results)}")
    print(f"Total Posts in DB: {total_tracked_posts}")

if __name__ == "__main__":
    try:
        get_stats()
    except Exception as e:
        print(f"Error: {e}")
