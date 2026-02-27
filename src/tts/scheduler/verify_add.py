
import sys
from pathlib import Path

# Add project root to path
project_root = Path(".").resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def main():
    post_id = "1q8t64q"
    subreddit = "flexibility"
    
    try:
        neo4j = get_connection()
        
        # Check for post
        query = """
        MATCH (p:Post {id: $post_id})
        OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
        RETURN p.id as id, p.title as title, s.name as subreddit
        """
        
        results = neo4j.execute_read(query, parameters={"post_id": post_id})
        
        if results:
            print(f"SUCCESS: Found post {post_id} in r/{results[0]['subreddit']}")
        else:
            print(f"FAILURE: Post {post_id} NOT found")
            
        # Check if subreddit exists
        sub_query = "MATCH (s:Subreddit {name: $name}) RETURN count(s) as c"
        sub_res = neo4j.execute_read(sub_query, parameters={"name": subreddit})
        if sub_res and sub_res[0]["c"] > 0:
            print(f"Subreddit r/{subreddit} is tracked.")
        else:
            print(f"Subreddit r/{subreddit} is NOT tracked.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
