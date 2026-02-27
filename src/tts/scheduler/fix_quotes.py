import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()) + '/src')
from feed.storage.neo4j_connection import get_connection

def fix_subreddit_quotes():
    neo4j = get_connection()

    # Query to find Subreddit nodes with quotes in name
    query = """
    MATCH (s:Subreddit)
    WHERE s.name CONTAINS '"' OR s.name STARTS WITH '"' OR s.name ENDS WITH '"'
    RETURN s.name as name
    """

    result = neo4j.execute_read(query)
    if result:
        print(f"Found {len(result)} subreddits with quotes:")
        for record in result:
            name = record['name']
            print(f"  {name}")

            # Remove quotes by merging with clean name
            clean_name = name.replace('"', '')

            neo4j.execute_write('''
                MATCH (s:Subreddit {name: $old_name})
                SET s.name = $new_name
            ''', parameters={'old_name': name, 'new_name': clean_name})

            print(f"  Fixed: {name} -> {clean_name}")
    else:
        print("No subreddits found with quotes.")

if __name__ == "__main__":
    fix_subreddit_quotes()
