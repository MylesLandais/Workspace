import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
# Import the list from the updated file
from run_crawler import SUBREDDITS

def sync_subs():
    print(f"Syncing {len(SUBREDDITS)} subreddits to Neo4j...")
    
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
        
        query = """
        UNWIND $subs as sub_name
        MERGE (s:Subreddit {name: sub_name})
        ON CREATE SET s.created_at = datetime()
        RETURN count(s) as merged
        """
        
        res = neo4j.execute_write(query, parameters={"subs": SUBREDDITS})
        print(f"✓ Merged/Verified {res[0]['merged']} subreddits.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync_subs()
