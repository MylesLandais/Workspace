import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()) + '/src')
from feed.storage.neo4j_connection import get_connection

def fix_all_subreddits():
    neo4j = get_connection()

    # Query all subreddit names
    query = """
    MATCH (s:Subreddit)
    RETURN s.name as name
    """

    result = neo4j.execute_read(query)
    fixed_count = 0

    for record in result:
        name = record['name']

        # Remove quotes
        clean_name = name.replace('"', '').replace("'", "")

        if clean_name != name:
            # Update the subreddit name
            neo4j.execute_write('''
                MATCH (s:Subreddit {name: $old_name})
                SET s.name = $new_name
            ''', parameters={'old_name': name, 'new_name': clean_name})
            print(f"Fixed: {name} -> {clean_name}")
            fixed_count += 1

    print(f"\nTotal fixed: {fixed_count}")

if __name__ == "__main__":
    fix_all_subreddits()
