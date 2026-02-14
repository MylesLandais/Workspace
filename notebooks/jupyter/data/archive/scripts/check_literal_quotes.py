import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()) + '/src')
from feed.storage.neo4j_connection import get_connection

def check_actual_names():
    neo4j = get_connection()

    # Query to check if names really have quotes in DB
    query = """
    MATCH (s:Subreddit)
    WHERE s.name CONTAINS '\\"'
    RETURN s.name as name
    """

    result = neo4j.execute_read(query)
    print(f"Found {len(result)} subreddits with literal quotes in DB:")
    for record in result:
        name = record['name']
        print(f"  Actual name: {repr(name)}")
        print(f"  Length: {len(name)}")
        print(f"  Starts with quote: {name.startswith('\\\"')}")
        print(f"  Ends with quote: {name.endswith('\\\"')}")

if __name__ == "__main__":
    check_actual_names()
