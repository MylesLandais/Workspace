import os
import sys
import json
from datetime import datetime, timedelta

# Temporarily add project root to path for imports
sys.path.insert(0, '/home/jovyan/workspaces')
sys.path.insert(0, '/home/jovyan/workspaces/src')

try:
    from feed.storage.neo4j_connection import get_connection
except ImportError:
    print("Error: Could not import Neo4j connection module. Ensure PYTHONPATH is correct.")
    sys.exit(1)

def count_new_threads():
    neo4j = get_connection()

    # Calculate ISO timestamp for 1 hour ago
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    one_hour_ago_iso = one_hour_ago.isoformat() + "Z"

    # Cypher query to find threads created within the last 1 hour
    query = """
    MATCH (t:Thread)
    WHERE t.created_at >= datetime($one_hour_ago)
    RETURN count(t) as new_threads
    """
    
    try:
        result = neo4j.execute_read(
            query,
            parameters={"one_hour_ago": one_hour_ago_iso}
        )
        
        if result:
            new_threads = result[0].get("new_threads", 0)
            print(f"New Threads Created in Last Hour: {new_threads}")
        else:
            print("New Threads Created in Last Hour: 0")
            
    except Exception as e:
        print(f"Error executing Neo4j query: {e}")
        print("Could not retrieve thread count.")

if __name__ == "__main__":
    count_new_threads()
