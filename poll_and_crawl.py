"""Poll a new subreddit and process crawl queue with rate limiting."""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection
from feed.crawler.frontier import URLFrontier
from feed.crawler.scheduler import AdaptiveScheduler
from feed.crawler.deduplication import DuplicateDetector
from feed.crawler.content import ContentAnalyzer
from feed.crawler.robots import RobotsParser
from feed.services.bio_crawler import BioCrawler


def poll_subreddit_and_crawl(subreddit_name: str, max_posts: int = 100, max_duration_minutes: Optional[int] = None):
    """
    Poll a subreddit, extract URLs, and process crawl queue.
    
    Args:
        subreddit_name: Subreddit name (with or without r/ prefix)
        max_posts: Maximum number of posts to collect and crawl before pausing
        max_duration_minutes: Maximum duration to run in minutes (None = no time limit)
    """
    print("=" * 70)
    print("POLLING SUBREDDIT AND PROCESSING CRAWL QUEUE")
    print("=" * 70)
    print(f"Subreddit: {subreddit_name}")
    print(f"Max posts: {max_posts}")
    if max_duration_minutes:
        print(f"Max duration: {max_duration_minutes} minutes")
    print()
    
    # Track start time for duration limit
    start_time = datetime.utcnow()
    end_time = None
    if max_duration_minutes:
        from datetime import timedelta
        end_time = start_time + timedelta(minutes=max_duration_minutes)
        print(f"Will run until: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
    
    # Initialize connections
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Initialize Reddit adapter with rate limiting
    reddit = RedditAdapter(
        delay_min=2.0,
        delay_max=5.0,
        mock=False
    )
    
    # Initialize polling engine
    engine = PollingEngine(reddit, neo4j, dry_run=False)
    
    # Initialize crawler components
    frontier = URLFrontier(neo4j)
    scheduler = AdaptiveScheduler(neo4j)
    deduplicator = DuplicateDetector(neo4j)
    content_analyzer = ContentAnalyzer()
    robots_parser = RobotsParser(neo4j, user_agent=reddit.user_agent)
    
    # Step 1: Poll the subreddit (limit to max_posts)
    print("\n" + "=" * 70)
    print("STEP 1: POLLING SUBREDDIT")
    print("=" * 70)
    
    subreddit_clean = subreddit_name.replace("r/", "").replace("/r/", "")
    
    # Poll with limit to collect exactly max_posts
    all_posts = []
    after = None
    page = 0
    
    print(f"Collecting up to {max_posts} posts from r/{subreddit_clean}...")
    
    while len(all_posts) < max_posts:
        page += 1
        print(f"--- Page {page} ---")
        
        # Calculate how many posts we still need
        remaining = max_posts - len(all_posts)
        limit_this_page = min(100, remaining)  # Reddit max is 100 per page
        
        posts, next_after = reddit.fetch_posts(
            source=subreddit_clean,
            sort="new",
            limit=limit_this_page,
            after=after
        )
        
        if not posts:
            print("No more posts available")
            break
        
        # Deduplicate
        new_posts = engine._deduplicate_posts(posts)
        if new_posts:
            print(f"Fetched {len(posts)} posts this page ({len(new_posts)} new, total so far: {len(all_posts) + len(new_posts)})")
            engine._store_posts(new_posts, subreddit_clean)
            all_posts.extend(new_posts)
        else:
            print(f"  -> All posts already exist on this page")
        
        # Stop if we've reached our limit
        if len(all_posts) >= max_posts:
            break
        
        after = next_after
        if not after:
            print("Reached end of available posts")
            break
    
    # Trim to exactly max_posts if we got more
    posts = all_posts[:max_posts]
    
    print(f"\nCollected {len(posts)} posts from r/{subreddit_clean}")
    
    # Step 2: Extract URLs and add to frontier
    print("\n" + "=" * 70)
    print("STEP 2: EXTRACTING URLs AND ADDING TO CRAWL QUEUE")
    print("=" * 70)
    
    urls_added = 0
    urls_skipped = 0
    
    for post in posts:
        # Add post URL if it's external
        if post.url and not post.url.startswith("/"):
            if frontier.add_url(post.url):
                urls_added += 1
            else:
                urls_skipped += 1
        
        # Add permalink
        if post.permalink:
            full_permalink = f"https://www.reddit.com{post.permalink}"
            if frontier.add_url(full_permalink):
                urls_added += 1
            else:
                urls_skipped += 1
    
    print(f"URLs added to queue: {urls_added}")
    print(f"URLs already in queue: {urls_skipped}")
    
    # Step 3: Process crawl queue
    print("\n" + "=" * 70)
    print("STEP 3: PROCESSING CRAWL QUEUE")
    print("=" * 70)
    print("Respecting rate limits and crawl delays...")
    print("Tracking last hits and setting next-allowed scan times...")
    print()
    
    urls_crawled = 0
    total_crawls = 0
    errors = 0
    
    # Limit crawling to max_posts URLs to avoid infinite loops
    # Also respect time limit if specified
    while urls_crawled < max_posts:
        # Check time limit
        if end_time and datetime.utcnow() >= end_time:
            print(f"\nTime limit reached ({max_duration_minutes} minutes). Pausing...")
            break
        # Get next batch of URLs ready for crawling
        ready_urls = frontier.get_next_urls(limit=10)
        
        if not ready_urls:
            print("\nNo URLs ready for crawling. Checking scheduled crawls...")
            # Check if there are any scheduled for later
            scheduled = scheduler.get_pages_due_for_crawl(limit=10)
            if not scheduled:
                print("No more URLs in queue. Done!")
                break
            else:
                print(f"Found {len(scheduled)} URLs scheduled for later.")
                print("Waiting for next crawl window...")
                time.sleep(5)
                continue
        
        print(f"\n--- Processing batch (URLs crawled: {urls_crawled}/{max_posts}) ---")
        print(f"Found {len(ready_urls)} URLs ready for crawling")
        
        for url_info in ready_urls:
            # Check if we've reached the limit
            if urls_crawled >= max_posts:
                print(f"\nReached limit of {max_posts} URLs. Pausing...")
                break
            
            # Check time limit
            if end_time and datetime.utcnow() >= end_time:
                print(f"\nTime limit reached ({max_duration_minutes} minutes). Pausing...")
                break
            
            url = url_info["url"]
            domain = url_info["domain"]
            
            # Check robots.txt
            if not robots_parser.is_allowed(url, domain):
                print(f"  [SKIP] {domain}: Disallowed by robots.txt")
                robots_parser.update_page_robots_status(url, False)
                continue
            
            # Get crawl delay for domain
            crawl_delay = robots_parser.get_crawl_delay(domain) or 1.0
            frontier.set_domain_crawl_delay(domain, crawl_delay)
            
            # Crawl the page
            try:
                print(f"  [CRAWL] {domain}: {url[:60]}...")
                start_time = time.time()
                
                # Use BioCrawler to fetch and analyze
                # This will:
                # - Record CRAWLED_AT relationship with timestamp
                # - Update last_crawled_at on WebPage node
                # - Schedule next crawl via AdaptiveScheduler (sets next_crawl_at)
                bio_crawler = BioCrawler(
                    neo4j=neo4j,
                    timeout=10,
                    user_agent=reddit.user_agent,
                    use_crawler_components=True
                )
                
                # Discover handles (this also crawls and stores metadata)
                candidates = bio_crawler.discover_handles(url)
                
                crawl_duration_ms = int((time.time() - start_time) * 1000)
                
                # Mark as crawled (updates last_crawled_at timestamp)
                frontier.mark_crawled(url, domain)
                
                urls_crawled += 1
                total_crawls += 1
                print(f"    ✓ Crawled in {crawl_duration_ms}ms ({len(candidates)} handles found)")
                print(f"    ✓ Last hit logged, next crawl scheduled")
                
                # Respect crawl delay
                if crawl_delay > 0:
                    time.sleep(crawl_delay)
                
            except Exception as e:
                errors += 1
                print(f"    ✗ Error: {e}")
                # Still mark as crawled to update timestamp
                try:
                    frontier.mark_crawled(url, domain)
                    urls_crawled += 1
                except:
                    pass
                continue
        
        # Progress update
        print(f"\nProgress: {urls_crawled}/{max_posts} URLs crawled")
        print(f"Total crawls: {total_crawls}, Errors: {errors}")
        
        # Small delay between batches
        if urls_crawled < max_posts:
            time.sleep(2)
        
        # Break if we've reached the limit
        if urls_crawled >= max_posts:
            break
    
    # Final summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Subreddit polled: r/{subreddit_clean}")
    print(f"Posts collected: {len(posts)}")
    print(f"URLs added to queue: {urls_added}")
    print(f"URLs crawled: {urls_crawled}")
    print(f"Total crawls: {total_crawls}")
    print(f"Errors: {errors}")
    print()
    print("Crawl queue processing paused after reaching limit.")
    print("All crawl hits have been logged with timestamps.")
    print("Next-allowed scan times have been set via adaptive scheduler.")
    print("Run again to continue crawling more posts.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Poll subreddit and process crawl queue")
    parser.add_argument(
        "subreddit",
        help="Subreddit name (e.g., BrookeMonkNSFWHub or r/BrookeMonkNSFWHub)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=100,
        help="Maximum posts to collect and crawl before pausing (default: 100)"
    )
    parser.add_argument(
        "--max-duration",
        type=int,
        default=None,
        help="Maximum duration to run in minutes (default: no time limit)"
    )
    
    args = parser.parse_args()
    
    try:
        poll_subreddit_and_crawl(args.subreddit, args.max_posts, args.max_duration)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Pausing...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

