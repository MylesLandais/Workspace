import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def check_subreddit_analytics(subreddit_name: str):
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Check if subreddit exists and get stats
    stats_query = """
    MATCH (s:Subreddit {name: $name})
    OPTIONAL MATCH (p:Post)-[:POSTED_IN]->(s)
    WITH s, count(p) as post_count, 
         max(p.updated_at) as last_updated,
         min(p.created_utc) as first_posted,
         max(p.created_utc) as latest_posted
    RETURN s.name as name, 
           post_count,
           last_updated,
           first_posted,
           latest_posted
    """
    
    results = neo4j.execute_read(stats_query, parameters={"name": subreddit_name})
    
    if not results:
        print(f"\n❌ Subreddit 'r/{subreddit_name}' NOT found in database.")
        return
    
    record = results[0]
    
    print(f"\n{'=' * 60}")
    print(f"ANALYTICS: r/{subreddit_name}")
    print(f"{'=' * 60}")
    print()
    print(f"Total Posts Indexed:    {record['post_count']}")
    print(f"First Post Indexed:    {record['first_posted']}")
    print(f"Latest Post Indexed:   {record['latest_posted']}")
    print(f"Last Updated:          {record['last_updated']}")
    print()
    
    # Calculate time since last update
    last_updated = record.get("last_updated")
    if last_updated:
        now = datetime.now(timezone.utc)
        # Convert Neo4j DateTime to Python datetime
        if hasattr(last_updated, 'isoformat'):
            last_updated_str = last_updated.isoformat()
            if last_updated_str:
                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
        
        time_diff = now - last_updated
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        
        print(f"Time since last update: {days}d {hours}h {minutes}m")
        print()
    
    # Show latest posts
    latest_posts_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name})
    RETURN p.id as id, p.title as title, p.created_utc as created, p.score as score
    ORDER BY p.created_utc DESC
    LIMIT 10
    """
    
    latest_posts = neo4j.execute_read(latest_posts_query, parameters={"name": subreddit_name})
    
    print(f"{'=' * 60}")
    print("LATEST 10 POSTS:")
    print(f"{'=' * 60}")
    print()
    
    for i, post in enumerate(latest_posts, 1):
        created = post.get("created", "N/A")
        score = post.get("score", "N/A")
        title = post.get("title", "N/A")[:50]
        if len(title) == 50:
            title += "..."
        
        print(f"{i:2}. [{created}] ({score:4}⬆)")
        print(f"    {title}")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check subreddit analytics.")
    parser.add_argument("subreddit", help="Subreddit name (without r/)")
    
    args = parser.parse_args()
    
    try:
        check_subreddit_analytics(args.subreddit)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
