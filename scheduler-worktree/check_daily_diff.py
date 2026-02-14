#!/usr/bin/env python3
"""
Check daily diff - compare posts collected since a specific timestamp.
Useful for tracking what was collected today vs yesterday.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def check_daily_diff(subreddit_name: str, since_timestamp: datetime = None):
    """
    Check posts collected since a specific timestamp.
    
    Args:
        subreddit_name: Subreddit name (without r/)
        since_timestamp: Datetime to compare from (defaults to 24 hours ago)
    """
    neo4j = get_connection()
    
    if since_timestamp is None:
        since_timestamp = datetime.utcnow() - timedelta(hours=24)
    
    since_epoch = int(since_timestamp.timestamp())
    
    # Query posts updated since the timestamp
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name})
    WHERE p.updated_at >= datetime({epochSeconds: $since_epoch})
    RETURN count(p) as total,
           min(p.updated_at) as oldest_new,
           max(p.updated_at) as newest_new
    """
    result = neo4j.execute_read(
        query,
        parameters={"name": subreddit_name, "since_epoch": since_epoch}
    )
    
    if not result or result[0]["total"] == 0:
        print(f"No new posts collected since {since_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        return
    
    total = result[0]["total"]
    oldest_obj = result[0]["oldest_new"]
    newest_obj = result[0]["newest_new"]
    
    oldest_dt = oldest_obj.to_native() if hasattr(oldest_obj, 'to_native') else oldest_obj
    newest_dt = newest_obj.to_native() if hasattr(newest_obj, 'to_native') else newest_obj
    
    print(f"=" * 70)
    print(f"Daily Diff Report - r/{subreddit_name}")
    print(f"=" * 70)
    print(f"\nTime window: Since {since_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"New posts collected: {total}")
    
    if oldest_dt and newest_dt:
        print(f"First new post: {oldest_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Last new post: {newest_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Get image count
    img_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name})
    WHERE p.updated_at >= datetime({epochSeconds: $since_epoch})
    AND (p.url CONTAINS "i.redd.it" OR p.url CONTAINS "i.imgur.com")
    RETURN count(p) as image_count
    """
    img_result = neo4j.execute_read(
        img_query,
        parameters={"name": subreddit_name, "since_epoch": since_epoch}
    )
    image_count = img_result[0]["image_count"] if img_result else 0
    print(f"Image posts: {image_count}")
    
    # Get total count for context
    total_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name})
    RETURN count(p) as total
    """
    total_result = neo4j.execute_read(
        total_query,
        parameters={"name": subreddit_name}
    )
    grand_total = total_result[0]["total"] if total_result else 0
    print(f"\nTotal posts in archive: {grand_total}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check daily diff for subreddit collection")
    parser.add_argument("--subreddit", default="laufeyhot", help="Subreddit name (without r/)")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")
    parser.add_argument("--since", help="Since timestamp (ISO format: YYYY-MM-DDTHH:MM:SS)")
    
    args = parser.parse_args()
    
    if args.since:
        since_timestamp = datetime.fromisoformat(args.since.replace('Z', '+00:00'))
    else:
        since_timestamp = datetime.utcnow() - timedelta(hours=args.hours)
    
    check_daily_diff(args.subreddit, since_timestamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())






