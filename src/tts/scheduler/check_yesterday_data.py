#!/usr/bin/env python3
"""Check Neo4j for posts collected yesterday."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def main():
    """Check for posts from yesterday."""
    print("=" * 80)
    print("Checking Neo4j for posts from yesterday")
    print("=" * 80)
    print()
    
    # Calculate yesterday's date range
    now = datetime.now()
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday_start + timedelta(days=1)
    
    print(f"Checking for posts between:")
    print(f"  Start: {yesterday_start}")
    print(f"  End: {yesterday_end}")
    print()
    
    try:
        # Use explicit .env path
        env_path = Path("/home/jovyan/workspace/.env")
        neo4j = get_connection(env_path=env_path)
        print(f"Connected to Neo4j: {neo4j.uri}")
        print()
        
        # Query for posts updated yesterday
        query = """
        MATCH (p:Post)
        WHERE p.updated_at >= datetime({epochSeconds: $start_epoch})
        AND p.updated_at < datetime({epochSeconds: $end_epoch})
        RETURN count(p) as post_count
        """
        
        result = neo4j.execute_read(
            query,
            parameters={
                "start_epoch": int(yesterday_start.timestamp()),
                "end_epoch": int(yesterday_end.timestamp()),
            }
        )
        
        if result:
            count = result[0].get("post_count", 0)
            print(f"Posts updated yesterday: {count}")
        else:
            print("Posts updated yesterday: 0")
        
        print()
        
        # Query for posts created yesterday (by created_utc)
        query2 = """
        MATCH (p:Post)
        WHERE p.created_utc >= datetime({epochSeconds: $start_epoch})
        AND p.created_utc < datetime({epochSeconds: $end_epoch})
        RETURN count(p) as post_count
        """
        
        result2 = neo4j.execute_read(
            query2,
            parameters={
                "start_epoch": int(yesterday_start.timestamp()),
                "end_epoch": int(yesterday_end.timestamp()),
            }
        )
        
        if result2:
            count2 = result2[0].get("post_count", 0)
            print(f"Posts created on Reddit yesterday: {count2}")
        else:
            print("Posts created on Reddit yesterday: 0")
        
        print()
        
        # Get recent posts with details
        query3 = """
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
        WHERE p.updated_at >= datetime({epochSeconds: $start_epoch})
        AND p.updated_at < datetime({epochSeconds: $end_epoch})
        RETURN s.name as subreddit, count(p) as count
        ORDER BY count DESC
        LIMIT 20
        """
        
        result3 = neo4j.execute_read(
            query3,
            parameters={
                "start_epoch": int(yesterday_start.timestamp()),
                "end_epoch": int(yesterday_end.timestamp()),
            }
        )
        
        if result3:
            print("Top subreddits by posts collected yesterday:")
            print("-" * 80)
            for record in result3:
                print(f"  r/{record['subreddit']}: {record['count']} posts")
        else:
            print("No posts found by subreddit")
        
        print()
        
        # Get total post count
        query4 = """
        MATCH (p:Post)
        RETURN count(p) as total_posts
        """
        
        result4 = neo4j.execute_read(query4)
        if result4:
            total = result4[0].get("total_posts", 0)
            print(f"Total posts in database: {total}")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

