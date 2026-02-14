#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def search_judy_posts():
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Search posts from last 3 days with Judy/Hopps keywords
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
    
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'BunnyGirls'})
    WHERE datetime(p.created_utc) >= datetime($cutoff)
      AND (toLower(p.title) CONTAINS toLower('judy') 
           OR toLower(p.title) CONTAINS toLower('hopps') 
           OR toLower(p.title) CONTAINS toLower('judys'))
    RETURN p.id as id, p.title as title, p.created_utc as created, p.url as url
    ORDER BY p.created_utc DESC
    LIMIT 20
    """
    
    results = neo4j.execute_read(query, parameters={"cutoff": cutoff})
    
    print(f"\nFound {len(results)} posts matching Judy/Hopps keywords in r/BunnyGirls (last 3 days):")
    print("-" * 80)
    
    if not results:
        print("No Judy/Hopps posts found.")
        return
    
    for record in results:
        created = record.get("created", "N/A")
        title = record.get("title", "N/A")
        url = record.get("url", "N/A")
        print(f"[{created}]")
        print(f"  {title}")
        print(f"  {url}")
        print()

if __name__ == "__main__":
    try:
        search_judy_posts()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
