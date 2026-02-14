#!/usr/bin/env python3
"""
Quick query helper for thread relationships in Neo4j.

Usage:
    python query_relationships.py --post-id 1ptxm3x
    python query_relationships.py --subreddit LocalLLaMA --related-to SillyTavernAI
    python query_relationships.py --stats
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def query_post_relationships(neo4j, post_id: str):
    """Find all threads that reference or are referenced by a post."""
    query = """
    MATCH (main:Post {id: $post_id})
    OPTIONAL MATCH (main)<-[:RELATES_TO]-(discussed:Post)
    OPTIONAL MATCH (main)-[:RELATES_TO]->(references:Post)
    RETURN 
      main.title as main_thread,
      main.subreddit as main_subreddit,
      main.permalink as main_permalink,
      collect(DISTINCT {
        title: discussed.title,
        subreddit: discussed.subreddit,
        permalink: discussed.permalink,
        id: discussed.id
      }) as discussed_in,
      collect(DISTINCT {
        title: references.title,
        subreddit: references.subreddit,
        permalink: references.permalink,
        id: references.id
      }) as references
    """
    
    result = neo4j.execute_read(query, parameters={"post_id": post_id})
    
    if result:
        row = result[0]
        print(f"\nMain Thread: {row['main_thread']}")
        print(f"Subreddit: r/{row['main_subreddit']}")
        print(f"Permalink: {row['main_permalink']}")
        
        discussed = [d for d in row['discussed_in'] if d.get('title')]
        if discussed:
            print(f"\nDiscussed in {len(discussed)} thread(s):")
            for d in discussed:
                print(f"  - r/{d['subreddit']}: {d['title'][:60]}")
                print(f"    https://www.reddit.com{d['permalink']}")
        
        references = [r for r in row['references'] if r.get('title')]
        if references:
            print(f"\nReferences {len(references)} thread(s):")
            for r in references:
                print(f"  - r/{r['subreddit']}: {r['title'][:60]}")
                print(f"    https://www.reddit.com{r['permalink']}")
    else:
        print(f"No post found with ID: {post_id}")


def query_cross_subreddit(neo4j, subreddit1: str, subreddit2: str):
    """Find relationships between two subreddits."""
    query = """
    MATCH (p1:Post)-[r:RELATES_TO]->(p2:Post)
    WHERE p1.subreddit = $sub1 AND p2.subreddit = $sub2
    RETURN 
      p1.id as source_id,
      p1.title as source_title,
      p1.permalink as source_permalink,
      p2.id as target_id,
      p2.title as target_title,
      p2.permalink as target_permalink,
      r.source_type as source_type,
      r.discovered_at as discovered_at
    ORDER BY r.discovered_at DESC
    LIMIT 50
    """
    
    result = neo4j.execute_read(
        query,
        parameters={"sub1": subreddit1, "sub2": subreddit2}
    )
    
    if result:
        print(f"\nFound {len(result)} relationship(s) from r/{subreddit1} to r/{subreddit2}:")
        for row in result:
            print(f"\n  Source: {row['source_title'][:60]}")
            print(f"    https://www.reddit.com{row['source_permalink']}")
            print(f"  Target: {row['target_title'][:60]}")
            print(f"    https://www.reddit.com{row['target_permalink']}")
            print(f"  Found in: {row['source_type']}")
    else:
        print(f"No relationships found between r/{subreddit1} and r/{subreddit2}")


def show_stats(neo4j):
    """Show relationship statistics."""
    queries = {
        "Total Posts": "MATCH (p:Post) RETURN count(p) as count",
        "Total Relationships": "MATCH ()-[r:RELATES_TO]->() RETURN count(r) as count",
        "Posts by Subreddit": """
            MATCH (p:Post)
            RETURN p.subreddit as subreddit, count(p) as count
            ORDER BY count DESC
            LIMIT 10
        """,
        "Top Relationship Pairs": """
            MATCH (p1:Post)-[:RELATES_TO]->(p2:Post)
            WHERE p1.subreddit <> p2.subreddit
            RETURN p1.subreddit as source, p2.subreddit as target, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """,
    }
    
    print("\n" + "=" * 80)
    print("Relationship Statistics")
    print("=" * 80)
    
    for name, query in queries.items():
        result = neo4j.execute_read(query)
        if result:
            if name in ["Posts by Subreddit", "Top Relationship Pairs"]:
                print(f"\n{name}:")
                for row in result:
                    if "subreddit" in row:
                        print(f"  r/{row['subreddit']}: {row['count']}")
                    else:
                        print(f"  {row['source']} -> {row['target']}: {row['count']}")
            else:
                count = result[0].get("count", 0)
                print(f"{name}: {count}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query thread relationships in Neo4j"
    )
    parser.add_argument(
        "--post-id",
        help="Post ID to query relationships for",
    )
    parser.add_argument(
        "--subreddit",
        help="Source subreddit for cross-subreddit query",
    )
    parser.add_argument(
        "--related-to",
        help="Target subreddit for cross-subreddit query",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show relationship statistics",
    )
    
    args = parser.parse_args()
    
    if not any([args.post_id, args.subreddit, args.stats]):
        parser.print_help()
        return 1
    
    # Connect to Neo4j
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"ERROR: Could not connect to Neo4j: {e}")
        return 1
    
    # Execute queries
    if args.stats:
        show_stats(neo4j)
    elif args.post_id:
        query_post_relationships(neo4j, args.post_id)
    elif args.subreddit and args.related_to:
        query_cross_subreddit(neo4j, args.subreddit, args.related_to)
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())







