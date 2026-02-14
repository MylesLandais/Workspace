import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()) + '/src')
from feed.storage.neo4j_connection import get_connection

def analyze_subs():
    neo4j = get_connection()

    # Query all subreddit names
    query = """
    MATCH (s:Subreddit)
    RETURN s.name as name
    LIMIT 10
    """

    result = neo4j.execute_read(query)
    for record in result:
        name = record['name']
        print(f"Name: {repr(name)}")
        print(f"  Length: {len(name)}")
        print(f"  Chars: {[hex(ord(c)) for c in name]}")
 print(f"  Contains quote: {chr(34) in name or chr(39) in name}")

if __name__ == "__main__":
    analyze_subs()
