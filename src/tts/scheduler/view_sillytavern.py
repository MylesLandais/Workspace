
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

def view_sillytavern_posts():
    print("=" * 80)
    print("r/SillyTavernAI - Recent Posts (Last 24h)")
    print("=" * 80)

    neo4j = get_connection()
    
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'SillyTavernAI'})
    RETURN p.title as title, 
           p.score as score, 
           p.num_comments as comments, 
           p.url as url, 
           p.created_utc as created,
           p.author as author
    ORDER BY p.created_utc DESC
    LIMIT 20
    """
    
    try:
        results = neo4j.execute_read(query)
        
        if not results:
            print("No posts found. Please run the crawler first.")
            return

        for i, post in enumerate(results, 1):
            title = post['title']
            if len(title) > 75:
                title = title[:72] + "..."
                
            print(f"{i}. [{post['score']}pts] {title}")
            print(f"   Author: {post['author']} | Comments: {post['comments']}")
            print(f"   Link: {post['url']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    view_sillytavern_posts()
