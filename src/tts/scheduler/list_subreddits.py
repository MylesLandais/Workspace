import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def list_subreddits():
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    query = """
    MATCH (s:Subreddit)
    RETURN s.name as name, s.subscribers as subscribers
    ORDER BY s.name
    """
    
    results = neo4j.execute_read(query)
    
    print(f"\nFound {len(results)} subreddits in database:")
    print("-" * 40)
    
    found_jlaw = False
    
    for record in results:
        name = record["name"]
        subs = record.get("subscribers", "N/A")
        print(f"r/{name} ({subs} subs)")
        
        if name.lower() == "jenniferlawrence":
            found_jlaw = True
            
    print("-" * 40)
    if found_jlaw:
        print("✅ r/jenniferlawrence IS in the database.")
    else:
        print("❌ r/jenniferlawrence is NOT in the database.")

if __name__ == "__main__":
    try:
        list_subreddits()
    except Exception as e:
        print(f"Error: {e}")
