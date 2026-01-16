"""Check requests made today and count Reddit pages polled."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def check_today_requests():
    """Check all requests made today."""
    neo4j = get_connection()
    
    # Get start of today (UTC)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_epoch = int(today_start.timestamp())
    
    print("=" * 60)
    print("REQUEST SUMMARY FOR TODAY")
    print("=" * 60)
    print(f"Date: {today_start.strftime('%Y-%m-%d')}")
    print(f"Time range: {today_start.isoformat()} to now")
    print()
    
    # 1. Check Reddit posts created today (from polling)
    print("--- REDDIT POLLING ---")
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE p.created_utc >= datetime({epochSeconds: $today_start})
    OR p.updated_at >= datetime({epochSeconds: $today_start})
    RETURN s.name as subreddit, 
           count(p) as post_count,
           collect(DISTINCT p.id)[0..5] as sample_post_ids
    ORDER BY post_count DESC
    """
    
    result = neo4j.execute_read(
        query,
        parameters={"today_start": today_start_epoch}
    )
    
    total_reddit_posts = 0
    subreddit_counts = {}
    
    for record in result:
        subreddit = record["subreddit"]
        count = record["post_count"]
        subreddit_counts[subreddit] = count
        total_reddit_posts += count
        print(f"  r/{subreddit}: {count} posts")
    
    print(f"\nTotal Reddit posts collected today: {total_reddit_posts}")
    print(f"Number of subreddits polled: {len(subreddit_counts)}")
    print()
    
    # 2. Check WebPage crawls today (from new crawler system)
    print("--- WEB PAGE CRAWLS ---")
    query = """
    MATCH (w:WebPage)-[r:CRAWLED_AT]->()
    WHERE r.crawled_at >= datetime({epochSeconds: $today_start})
    RETURN w.normalized_url as url,
           w.domain as domain,
           r.crawled_at as crawled_at,
           r.http_status as http_status,
           r.changed as changed
    ORDER BY r.crawled_at DESC
    LIMIT 100
    """
    
    result = neo4j.execute_read(
        query,
        parameters={"today_start": today_start_epoch}
    )
    
    total_crawls = len(result)
    reddit_crawls = 0
    domain_counts = {}
    
    print(f"Total web page crawls today: {total_crawls}")
    print("\nRecent crawls:")
    for record in result[:20]:  # Show first 20
        url = record["url"]
        domain = record["domain"]
        status = record.get("http_status", "N/A")
        changed = record.get("changed", False)
        
        if "reddit.com" in domain.lower():
            reddit_crawls += 1
        
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        status_icon = "✓" if status == 200 else "✗"
        change_icon = "🔄" if changed else "➖"
        print(f"  {status_icon} {change_icon} {domain}: {url[:60]}...")
    
    print(f"\nReddit pages crawled today: {reddit_crawls}")
    print(f"\nCrawls by domain (top 10):")
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {domain}: {count} crawls")
    print()
    
    # 3. Check WebPages updated today (scheduled crawls)
    print("--- WEB PAGES UPDATED TODAY ---")
    query = """
    MATCH (w:WebPage)
    WHERE w.last_crawled_at >= datetime({epochSeconds: $today_start})
    OR w.updated_at >= datetime({epochSeconds: $today_start})
    RETURN w.domain as domain,
           count(w) as page_count,
           sum(CASE WHEN w.domain CONTAINS 'reddit' THEN 1 ELSE 0 END) as reddit_count
    ORDER BY page_count DESC
    """
    
    result = neo4j.execute_read(
        query,
        parameters={"today_start": today_start_epoch}
    )
    
    if result:
        for record in result:
            domain = record["domain"]
            count = record["page_count"]
            reddit_count = record.get("reddit_count", 0)
            if count > 0:
                print(f"  {domain}: {count} pages ({reddit_count} Reddit)")
    print()
    
    # 4. Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Reddit posts collected: {total_reddit_posts}")
    print(f"Reddit pages crawled: {reddit_crawls}")
    print(f"Total web page crawls: {total_crawls}")
    print(f"Subreddits polled: {len(subreddit_counts)}")
    print()
    
    # 5. List all subreddits with activity today
    if subreddit_counts:
        print("Subreddits polled today:")
        for subreddit, count in sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  r/{subreddit}: {count} posts")


if __name__ == "__main__":
    try:
        check_today_requests()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()








