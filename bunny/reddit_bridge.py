#!/usr/bin/env python3
"""
Reddit-to-Bunny Bridge Script

This script bridges the Reddit post data stored by the feed system
to the Bunny application's data model.

The Bunny app expects:
- Media nodes (for posts)
- Source nodes (for tracking data sources like subreddits)

Our feed system stores:
- Post nodes (Reddit posts)
- Subreddit nodes (Reddit communities)
"""

import sys
from pathlib import Path

# Add project roots to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
from datetime import datetime, timedelta

def check_bunny_compatibility():
    """Check if Bunny can query our Reddit data."""
    neo4j = get_connection()
    
    print("=" * 80)
    print("🐰 BUNNY APP COMPATIBILITY CHECK")
    print("=" * 80)
    print(f"Connected to Neo4j: {neo4j.uri}\n")
    
    # Check if we have Reddit posts that Bunny could use
    print("📊 Checking Reddit Data Availability:\n")
    
    # Count posts by subreddit
    subreddit_count_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE datetime(p.created_utc) >= datetime() - duration('P7D')
    RETURN s.name as subreddit, count(p) as post_count
    ORDER BY post_count DESC
    LIMIT 20
    """
    
    try:
        results = neo4j.execute_read(subreddit_count_query)
        
        print("📈 Posts per subreddit (last 7 days):")
        print("-" * 80)
        for record in results[:10]:
            subreddit = record["subreddit"]
            count = record["post_count"]
            bar = "█" * min(50, count // 5)
            print(f"r/{subreddit:25} | {bar:50} {count}")
        
        print(f"\n✅ Total: {sum(r['post_count'] for r in results)} posts across {len(results)} subreddits")
        
    except Exception as e:
        print(f"❌ Error querying subreddits: {e}")
    
    # Check for unixporn specifically (since they mentioned it)
    print("\n🖥️ Unixporn subreddit data:\n")
    
    unixporn_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'unixporn'})
    WHERE datetime(p.created_utc) >= datetime() - duration('P7D')
    RETURN p.id, p.title, p.url, p.created_utc, p.score
    ORDER BY p.created_utc DESC
    LIMIT 10
    """
    
    try:
        results = neo4j.execute_read(unixporn_query)
        
        if results:
            print("Recent unixporn posts:")
            for i, post in enumerate(results[:5], 1):
                print(f"  {i}. [{post['p.created_utc']}] {post['p.title'][:60]}")
                print(f"     {post['p.url']}")
        else:
            print("No unixporn posts found in last 7 days")
            
    except Exception as e:
        print(f"❌ Error querying unixporn: {e}")
    
    # Check for BunnyGirls
    print("\n🐰 BunnyGirls subreddit data:\n")
    
    bunny_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'BunnyGirls'})
    WHERE datetime(p.created_utc) >= datetime() - duration('P30D')
    RETURN p.id, p.title, p.url, p.created_utc
    ORDER BY p.created_utc DESC
    LIMIT 10
    """
    
    try:
        results = neo4j.execute_read(bunny_query)
        
        if results:
            print("Recent BunnyGirls posts:")
            for i, post in enumerate(results[:5], 1):
                print(f"  {i}. [{post['p.created_utc']}] {post['p.title'][:60]}")
                print(f"     {post['p.url']}")
        else:
            print("No BunnyGirls posts found in last 30 days")
            
    except Exception as e:
        print(f"❌ Error querying BunnyGirls: {e}")
    
    # Check Maddie-related subreddits
    print("\n💃 Maddie Ziegler subreddits:\n")
    
    maddie_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE s.name IN ['MaddieZiegler1', 'dancemoms', 'DanceMoms', 'MaddieZiegler']
      AND datetime(p.created_utc) >= datetime() - duration('P30D')
    RETURN s.name as subreddit, count(p) as post_count
    """
    
    try:
        results = neo4j.execute_read(maddie_query)
        
        if results:
            print("Maddie Ziegler related posts (30 days):")
            for record in results:
                print(f"  r/{record['subreddit']:25} - {record['post_count']} posts")
        else:
            print("No Maddie-related posts found")
            
    except Exception as e:
        print(f"❌ Error querying Maddie subreddits: {e}")
    
    # Check if Bunny's expected indexes exist
    print("\n🔍 Checking Bunny Schema Compatibility:\n")
    
    index_check = """
    CALL db.indexes() YIELD name, tokenNames
    WHERE name CONTAINS 'post' OR name CONTAINS 'media' OR name CONTAINS 'source'
    RETURN name, tokenNames
    """
    
    try:
        indexes = neo4j.execute_read(index_check)
        
        print("Relevant indexes found:")
        for idx in indexes:
            print(f"  • {idx['name']}")
            print(f"    Tokens: {', '.join(idx['tokenNames'])}")
            
    except Exception as e:
        print(f"❌ Error checking indexes: {e}")
    
    neo4j.close()
    
    print("\n" + "=" * 80)
    print("📋 RECOMMENDATIONS FOR BUNNY INTEGRATION")
    print("=" * 80)
    print("""
1. ✅ Reddit posts are stored and accessible via Post nodes
2. ⚠️ Bunny expects Media nodes with a different structure
3. 💡 Options to integrate:
   
   Option A: Extend Bunny schema to query Post nodes directly
      - Add queries for Post nodes in Bunny resolvers
      - Map Post properties to Media GraphQL types
   
   Option B: Create Media nodes from Posts
      - Run migration script to duplicate Posts as Media nodes
      - Keep both schemas in sync
   
   Option C: Use Bunny's Source system for subreddits
      - Create Source nodes for tracked subreddits
      - Use Bunny's existing Media ingestion pipeline
""")
    print("=" * 80)

if __name__ == "__main__":
    try:
        check_bunny_compatibility()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
