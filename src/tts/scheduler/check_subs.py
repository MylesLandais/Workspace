import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()) + '/src')
from feed.storage.neo4j_connection import get_connection

def check_subreddits():
    neo4j = get_connection()

    # Query all subreddit names
    query = """
    MATCH (s:Subreddit)
    RETURN DISTINCT s.name as name
    ORDER BY name
    LIMIT 20
    """

    result = neo4j.execute_read(query)
    print(f"Found {len(result)} subreddits:")
    for record in result:
        name = record['name']
        print(f"  {repr(name)}")

if __name__ == "__main__":
    check_subreddits()
