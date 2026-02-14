#!/usr/bin/env python3
"""Find subreddits in Neo4j that don't have mock_data folders."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def main():
    """Find missing subreddits."""
    # Get subreddits from Neo4j
    env_path = Path("/home/jovyan/workspace/.env")
    neo4j = get_connection(env_path=env_path)
    
    query = """
    MATCH (s:Subreddit)<-[:POSTED_IN]-(p:Post)
    WITH s.name as name, count(p) as count
    RETURN name, count
    ORDER BY count DESC
    """
    
    result = neo4j.execute_read(query)
    subreddits_in_db = {record["name"]: record["count"] for record in result}
    
    # Get subreddits in mock_data
    mock_data_dir = Path("/home/jovyan/workspace/mock_data")
    existing_folders = set()
    if mock_data_dir.exists():
        for item in mock_data_dir.iterdir():
            if item.is_dir() and item.name not in ["json", "images"]:
                existing_folders.add(item.name)
    
    # Find missing ones
    missing = []
    for name, count in sorted(subreddits_in_db.items()):
        if name not in existing_folders:
            missing.append((name, count))
    
    print("=" * 80)
    print("MISSING SUBREDDITS (in Neo4j but not in mock_data)")
    print("=" * 80)
    print()
    
    if missing:
        print(f"Found {len(missing)} missing subreddits:\n")
        total_posts = 0
        for name, count in missing:
            print(f"  r/{name}: {count} posts")
            total_posts += count
        print(f"\nTotal posts to export: {total_posts}")
        print()
        print("Missing subreddits (for export command):")
        print(" ".join([name for name, _ in missing]))
    else:
        print("No missing subreddits! All subreddits in Neo4j have mock_data folders.")
    
    print()
    print("=" * 80)
    print(f"Summary:")
    print(f"  Subreddits in Neo4j: {len(subreddits_in_db)}")
    print(f"  Folders in mock_data: {len(existing_folders)}")
    print(f"  Missing: {len(missing)}")
    print("=" * 80)


if __name__ == "__main__":
    main()







