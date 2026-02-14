import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def search_ravenclaws():
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'HogwartsGoneWild'})
    WHERE toLower(p.title) CONTAINS toLower('ravenclaw') 
       OR toLower(p.title) CONTAINS toLower('ravenclaw')
       OR toLower(p.title) CONTAINS toLower('raven claw')
       OR toLower(p.title) CONTAINS toLower('raven-claw')
    RETURN p.id as id, p.title as title, p.created_utc as created, p.url as url
    ORDER BY p.created_utc DESC
    LIMIT 20
    """
    
    results = neo4j.execute_read(query)
    
    print(f"\nFound {len(results)} Ravenclaw-related posts in r/HogwartsGoneWild:")
    print("-" * 60)
    
    if not results:
        print("No Ravenclaw-related posts found.")
        return
    
    for i, record in enumerate(results, 1):
        title = record["title"]
        created = record.get("created", "N/A")
        url = record.get("url", "N/A")
        print(f"{i}. [{created}]")
        print(f"   {title}")
        print(f"   {url}")
        print()

if __name__ == "__main__":
    try:
        search_ravenclaws()
    except Exception as e:
        print(f"Error: {e}")
