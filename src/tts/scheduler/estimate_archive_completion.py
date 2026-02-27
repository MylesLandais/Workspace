#!/usr/bin/env python3
"""
Estimate archive completion percentage for subreddits based on statistics schema.
Uses concepts from 012_subreddit_statistics.cypher to calculate completion estimates.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def estimate_archive_completion(subreddit_name: str):
    """
    Estimate archive completion percentage for a subreddit.
    
    Based on the statistics schema concepts:
    - monthly_counts: Posts per month
    - yearly_counts: Posts per year  
    - all_time_estimate: Estimated total posts
    - post_velocity: Average posts per day
    
    Returns completion estimate and statistics.
    """
    neo4j = get_connection()
    
    # Get current collection stats
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name})
    RETURN count(p) as total, 
           min(p.created_utc) as oldest_date, 
           max(p.created_utc) as newest_date
    """
    result = neo4j.execute_read(query, parameters={"name": subreddit_name})
    
    if not result or result[0]["total"] == 0:
        return {
            "subreddit": subreddit_name,
            "current_posts": 0,
            "image_posts": 0,
            "completion_pct": 0,
            "estimated_total": 0,
            "status": "No posts collected"
        }
    
    current_count = result[0]["total"]
    oldest = result[0]["oldest_date"]
    newest = result[0]["newest_date"]
    
    # Handle Neo4j DateTime objects - convert to Python datetime
    try:
        if hasattr(oldest, 'to_native'):
            oldest_dt = oldest.to_native()
        elif hasattr(oldest, 'year'):
            # Neo4j DateTime object - create datetime from attributes
            oldest_dt = datetime(
                oldest.year, oldest.month, oldest.day,
                oldest.hour, oldest.minute, oldest.second
            )
        elif isinstance(oldest, datetime):
            oldest_dt = oldest
        else:
            oldest_dt = None
    except Exception as e:
        oldest_dt = None
    
    try:
        if hasattr(newest, 'to_native'):
            newest_dt = newest.to_native()
        elif hasattr(newest, 'year'):
            # Neo4j DateTime object - create datetime from attributes
            newest_dt = datetime(
                newest.year, newest.month, newest.day,
                newest.hour, newest.minute, newest.second
            )
        elif isinstance(newest, datetime):
            newest_dt = newest
        else:
            newest_dt = None
    except Exception as e:
        newest_dt = None
    
    # Get image count
    img_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name})
    WHERE p.url CONTAINS "i.redd.it" OR p.url CONTAINS "i.imgur.com"
    RETURN count(p) as image_count
    """
    img_result = neo4j.execute_read(img_query, parameters={"name": subreddit_name})
    image_count = img_result[0]["image_count"] if img_result else 0
    
    if not oldest_dt or not newest_dt:
        return {
            "subreddit": subreddit_name,
            "current_posts": current_count,
            "image_posts": image_count,
            "completion_pct": 0,
            "estimated_total": 0,
            "status": "Invalid date range"
        }
    
    # Calculate time span
    time_span = (newest_dt - oldest_dt).days
    if time_span <= 0:
        time_span = 1  # Avoid division by zero
    
    # Calculate post velocity (posts per day) from our sample
    post_velocity = current_count / time_span
    
    # Estimate total archive with smarter logic based on time span
    estimated_yearly_posts = post_velocity * 365
    
    # Adjust estimation based on how much data we have:
    # - Use actual time span as minimum subreddit age
    # - For longer spans, assume subreddit is at least that old
    # - Add buffer for potential older history
    
    if time_span >= 730:  # 2+ years
        # We have 2+ years of data - subreddit is at least that old, add 25% buffer
        subreddit_age_years = (time_span / 365) * 1.25
        estimated_total = estimated_yearly_posts * subreddit_age_years
        estimate_note = f"Based on {time_span} day sample ({subreddit_age_years:.1f}yr estimate)"
    elif time_span >= 365:  # 1-2 years
        # We have a year+ of data - subreddit likely has 1.5-2x that history
        subreddit_age_years = (time_span / 365) * 1.5
        estimated_total = estimated_yearly_posts * subreddit_age_years
        estimate_note = f"Based on {time_span} day sample ({subreddit_age_years:.1f}yr estimate)"
    elif time_span >= 90:  # 3-12 months
        # 3+ months of data - reasonable estimate
        subreddit_age_years = (time_span / 365) * 2.0  # Assume 2x our span
        estimated_total = estimated_yearly_posts * subreddit_age_years
        estimate_note = f"Based on {time_span} day sample ({subreddit_age_years:.1f}yr estimate)"
    elif time_span >= 30:  # 1-3 months
        # 1-3 months - moderate estimate
        subreddit_age_years = 1.5  # Assume 1.5 years minimum
        estimated_total = estimated_yearly_posts * subreddit_age_years
        estimate_note = f"Based on {time_span} day sample ({subreddit_age_years:.1f}yr estimate)"
    else:  # < 30 days
        # < 30 days - very conservative, incomplete sample
        subreddit_age_years = 1.0  # Assume 1 year minimum
        estimated_total = estimated_yearly_posts * subreddit_age_years
        estimate_note = f"Based on {time_span} day sample ({subreddit_age_years:.1f}yr min, estimate unreliable)"
    
    # Calculate completion percentage
    completion_pct = (current_count / estimated_total * 100) if estimated_total > 0 else 0
    
    return {
        "subreddit": subreddit_name,
        "current_posts": current_count,
        "image_posts": image_count,
        "post_velocity": round(post_velocity, 2),
        "time_span_days": time_span,
        "date_range": {
            "oldest": oldest_dt.strftime("%Y-%m-%d"),
            "newest": newest_dt.strftime("%Y-%m-%d")
        },
        "estimated_yearly_posts": int(estimated_yearly_posts),
        "estimated_total": int(estimated_total),
        "completion_pct": round(completion_pct, 1),
        "estimate_note": estimate_note,
        "status": "Estimate"
    }


def main():
    """Generate completion estimates for tracked subreddits."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Estimate archive completion percentages")
    parser.add_argument(
        "--subreddit",
        help="Estimate for specific subreddit",
    )
    parser.add_argument(
        "--all-recent",
        action="store_true",
        help="Estimate for all recently crawled subreddits",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("ARCHIVE COMPLETION ESTIMATES")
    print("=" * 70)
    print()
    print("Based on subreddit statistics schema concepts:")
    print("- post_velocity: Average posts per day")
    print("- yearly_counts: Estimated posts per year")
    print("- all_time_estimate: Estimated total archive size")
    print()
    print("Note: Estimates are conservative, assuming 2 years of subreddit history")
    print("=" * 70)
    print()
    
    if args.subreddit:
        subreddits = [args.subreddit]
    elif args.all_recent:
        subreddits = ['laufeyhot', 'Triangl', 'OvileeWorship', 'Sjokz', 'BrookeMonkTheSecond']
    else:
        subreddits = ['laufeyhot', 'Triangl', 'OvileeWorship']
    
    results = []
    for subreddit in subreddits:
        estimate = estimate_archive_completion(subreddit)
        results.append(estimate)
        
        print(f"r/{estimate['subreddit']}:")
        print("-" * 70)
        print(f"  Current Posts: {estimate['current_posts']:,} ({estimate['image_posts']} images)")
        
        if estimate['status'] == "Estimate":
            print(f"  Date Range: {estimate['date_range']['oldest']} to {estimate['date_range']['newest']} ({estimate['time_span_days']} days)")
            print(f"  Post Velocity: {estimate['post_velocity']:.2f} posts/day")
            print(f"  Estimated Yearly: {estimate['estimated_yearly_posts']:,} posts")
            print(f"  Estimated Total Archive: {estimate['estimated_total']:,} posts")
            print(f"  Completion Estimate: {estimate['completion_pct']:.1f}%")
            if 'estimate_note' in estimate:
                print(f"  Note: {estimate['estimate_note']}")
        else:
            print(f"  Status: {estimate['status']}")
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    valid_estimates = [r for r in results if r['status'] == 'Estimate']
    if valid_estimates:
        avg_completion = sum(r['completion_pct'] for r in valid_estimates) / len(valid_estimates)
        total_current = sum(r['current_posts'] for r in valid_estimates)
        total_estimated = sum(r['estimated_total'] for r in valid_estimates)
        
        print(f"Average Completion: {avg_completion:.1f}%")
        print(f"Total Current Posts: {total_current:,}")
        print(f"Total Estimated Archive: {total_estimated:,}")
        print(f"Overall Progress: {(total_current/total_estimated*100):.1f}%")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

