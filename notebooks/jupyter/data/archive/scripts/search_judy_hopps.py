#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def search_judy_hopps():
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Search for Judy Hopps post
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'BunnyGirls'})
    WHERE toLower(p.title) CONTAINS toLower('Judy Hopps')
    RETURN p.id as id, p.title as title, p.created_utc as created, p.url as url
    ORDER BY p.created_utc DESC
    LIMIT 10
    """
    
    results = neo4j.execute_read(query)
    
    print(f"\nFound {len(results)} posts matching 'Judy Hopps' in r/BunnyGirls:")
    print("-" * 80)
    
    if not results:
        print("No Judy Hopps posts found.")
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
        search_judy_hopps()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
