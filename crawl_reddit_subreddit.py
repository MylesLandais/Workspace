"""Crawl a Reddit subreddit and track history properly."""

import sys
import time
from pathlib import Path
from datetime import datetime
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
import requests
from bs4 import BeautifulSoup


def ensure_schema(neo4j):
    """Ensure WebPage schema exists."""
    print("Checking schema...")
    
    # Try to create constraint (will fail silently if exists)
    try:
        neo4j.execute_write("""
        CREATE CONSTRAINT webpage_url_unique IF NOT EXISTS
        FOR (w:WebPage) REQUIRE w.normalized_url IS UNIQUE;
        """)
        print("✓ Schema constraint created/verified")
    except Exception as e:
        print(f"Schema check: {e}")
    
    # Create indexes
    try:
        neo4j.execute_write("""
        CREATE INDEX webpage_next_crawl_index IF NOT EXISTS
        FOR (w:WebPage) ON (w.next_crawl_at);
        """)
        neo4j.execute_write("""
        CREATE INDEX webpage_domain_index IF NOT EXISTS
        FOR (w:WebPage) ON (w.domain);
        """)
        neo4j.execute_write("""
        CREATE INDEX webpage_content_hash_index IF NOT EXISTS
        FOR (w:WebPage) ON (w.content_hash);
        """)
        print("✓ Schema indexes created/verified")
    except Exception as e:
        print(f"Index creation: {e}")


def crawl_reddit_post_json(post_id: str, neo4j, frontier, scheduler, deduplicator, content_analyzer, user_agent):
    """Crawl a Reddit post using JSON API and track history."""
    # Use Reddit JSON API instead of HTML
    json_url = f"https://www.reddit.com/comments/{post_id}.json"
    normalized = frontier.normalizer.normalize(json_url)
    domain = "www.reddit.com"
    
    start_time = time.time()
    
    try:
        # Fetch JSON data
        response = requests.get(
            json_url,
            headers={"User-Agent": user_agent},
            timeout=10,
            allow_redirects=True
        )
        response.raise_for_status()
        
        content = response.text
        content_hash = content_analyzer.compute_content_hash(content)
        simhash = content_analyzer.compute_simhash(content)
        content_length = len(content.encode('utf-8'))
        crawl_duration_ms = int((time.time() - start_time) * 1000)
        
        # Get previous content hash to detect changes
        webpage = neo4j.get_webpage(normalized)
        old_hash = webpage.get("content_hash") if webpage else None
        changed = content_hash != old_hash if old_hash else True
        
        # Store/update WebPage node
        query = """
        MERGE (w:WebPage {normalized_url: $normalized_url})
        ON CREATE SET
            w.original_url = $original_url,
            w.domain = $domain,
            w.content_hash = $content_hash,
            w.simhash = $simhash,
            w.last_crawled_at = datetime(),
            w.next_crawl_at = datetime(),
            w.crawl_interval_days = 0.042,
            w.change_count = 0,
            w.no_change_count = 0,
            w.http_status = $http_status,
            w.content_type = $content_type,
            w.content_length = $content_length,
            w.crawl_duration_ms = $crawl_duration_ms,
            w.robots_allowed = true,
            w.created_at = datetime(),
            w.updated_at = datetime()
        ON MATCH SET
            w.content_hash = $content_hash,
            w.simhash = $simhash,
            w.last_crawled_at = datetime(),
            w.http_status = $http_status,
            w.content_type = $content_type,
            w.content_length = $content_length,
            w.crawl_duration_ms = $crawl_duration_ms,
            w.updated_at = datetime()
        """
        
        neo4j.execute_write(
            query,
            parameters={
                "normalized_url": normalized,
                "original_url": json_url,
                "domain": domain,
                "content_hash": content_hash,
                "simhash": str(simhash) if simhash is not None else None,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", "").split(";")[0],
                "content_length": content_length,
                "crawl_duration_ms": crawl_duration_ms,
            }
        )
        
        # Record crawl history (self-relationship for history tracking)
        history_query = """
        MATCH (w:WebPage {normalized_url: $normalized_url})
        CREATE (w)-[r:CRAWLED_AT {
            crawled_at: datetime(),
            http_status: $http_status,
            content_hash: $content_hash,
            changed: $changed,
            content_length: $content_length,
            crawl_duration_ms: $crawl_duration_ms
        }]->(w)
        RETURN r
        """
        
        neo4j.execute_write(
            history_query,
            parameters={
                "normalized_url": normalized,
                "http_status": response.status_code,
                "content_hash": content_hash,
                "changed": changed,
                "content_length": content_length,
                "crawl_duration_ms": crawl_duration_ms,
            }
        )
        
        # Update schedule
        scheduler.update_schedule(
            normalized,
            scheduler.schedule_next_crawl(normalized, changed),
            scheduler.get_next_interval(
                webpage.get("crawl_interval_days") if webpage else None,
                changed
            ),
            changed
        )
        
        # Mark as crawled
        frontier.mark_crawled(normalized, domain)
        
        return True, f"OK ({crawl_duration_ms}ms, changed={changed})"
        
    except Exception as e:
        crawl_duration_ms = int((time.time() - start_time) * 1000)
        
        # Record failure
        try:
            query = """
            MERGE (w:WebPage {normalized_url: $normalized_url})
            ON CREATE SET
                w.original_url = $original_url,
                w.domain = $domain,
                w.last_crawled_at = datetime(),
                w.http_status = $http_status,
                w.crawl_duration_ms = $crawl_duration_ms,
                w.robots_allowed = true,
                w.created_at = datetime(),
                w.updated_at = datetime()
            ON MATCH SET
                w.last_crawled_at = datetime(),
                w.http_status = $http_status,
                w.crawl_duration_ms = $crawl_duration_ms,
                w.updated_at = datetime()
            """
            
            http_status = None
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                http_status = e.response.status_code
            
            neo4j.execute_write(
                query,
                parameters={
                    "normalized_url": normalized,
                    "original_url": json_url,
                    "domain": domain,
                    "http_status": http_status,
                    "crawl_duration_ms": crawl_duration_ms,
                }
            )
            
            frontier.mark_crawled(normalized, domain)
        except:
            pass
        
        return False, str(e)


def crawl_subreddit(subreddit_url: str, max_posts: int = 100):
    """Crawl a Reddit subreddit and track all posts."""
    print("=" * 70)
    print("REDDIT SUBREDDIT CRAWLER")
    print("=" * 70)
    print(f"Subreddit: {subreddit_url}")
    print(f"Max posts to crawl: {max_posts}")
    print()
    
    # Initialize
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Ensure schema exists
    ensure_schema(neo4j)
    print()
    
    # Initialize components
    reddit = RedditAdapter(delay_min=2.0, delay_max=5.0, mock=False)
    frontier = URLFrontier(neo4j)
    scheduler = AdaptiveScheduler(neo4j)
    deduplicator = DuplicateDetector(neo4j)
    content_analyzer = ContentAnalyzer()
    robots_parser = RobotsParser(neo4j, user_agent=reddit.user_agent)
    
    # Extract subreddit name
    subreddit_name = subreddit_url.rstrip("/").split("/r/")[-1]
    print(f"Subreddit name: {subreddit_name}")
    print()
    
    # Step 1: Get posts from subreddit (poll new or fetch existing)
    print("=" * 70)
    print("STEP 1: GETTING POSTS FROM SUBREDDIT")
    print("=" * 70)
    
    # First try to poll for new posts
    engine = PollingEngine(reddit, neo4j, dry_run=False)
    posts = engine.poll_source(
        source=subreddit_name,
        sort="new",
        max_pages=10,
        limit_per_page=100
    )
    
    # If no new posts, fetch existing posts from database
    if len(posts) == 0:
        print("No new posts found. Fetching existing posts from database...")
        query = """
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
        RETURN p.id as id, p.permalink as permalink, p.url as url
        ORDER BY p.created_utc DESC
        LIMIT $limit
        """
        result = neo4j.execute_read(
            query,
            parameters={"subreddit": subreddit_name, "limit": max_posts * 2}
        )
        
        # Convert to Post-like objects for processing
        from feed.models.post import Post
        from datetime import datetime
        posts = []
        for record in result:
            # Create minimal post object
            post = Post(
                id=record["id"],
                title="",  # Not needed for crawling
                created_utc=datetime.utcnow(),
                score=0,
                num_comments=0,
                upvote_ratio=0.0,
                over_18=False,
                url=record.get("url", ""),
                selftext="",
                author=None,
                subreddit=subreddit_name,
                permalink=record.get("permalink", ""),
            )
            posts.append(post)
        
        print(f"Fetched {len(posts)} existing posts from database")
    
    print(f"\nTotal posts to process: {len(posts)}")
    
    # Step 2: Extract post IDs
    print("\n" + "=" * 70)
    print("STEP 2: EXTRACTING POST IDs")
    print("=" * 70)
    
    post_ids = []
    external_urls = []
    
    for post in posts:
        # Extract post ID from permalink
        if post.permalink:
            # Permalink format: /r/subreddit/comments/POST_ID/title/
            parts = post.permalink.strip("/").split("/")
            if "comments" in parts:
                idx = parts.index("comments")
                if idx + 1 < len(parts):
                    post_id = parts[idx + 1]
                    post_ids.append(post_id)
        
        # Track external URLs separately
        if post.url and not post.url.startswith("/") and "reddit.com" not in post.url:
            external_urls.append(post.url)
            frontier.add_url(post.url)
    
    print(f"Extracted {len(post_ids)} Reddit post IDs")
    print(f"Extracted {len(external_urls)} external URLs")
    
    # Step 3: Crawl Reddit posts using JSON API
    print("\n" + "=" * 70)
    print("STEP 3: CRAWLING REDDIT POSTS (JSON API)")
    print("=" * 70)
    print("Using Reddit JSON API (robots.txt friendly)...")
    print()
    
    crawled_count = 0
    success_count = 0
    error_count = 0
    
    for i, post_id in enumerate(post_ids[:max_posts], 1):
        print(f"[{i}/{min(len(post_ids), max_posts)}] Post ID: {post_id}")
        
        success, message = crawl_reddit_post_json(
            post_id, neo4j, frontier, scheduler, deduplicator,
            content_analyzer, reddit.user_agent
        )
        
        if success:
            success_count += 1
            print(f"  ✓ {message}")
        else:
            error_count += 1
            print(f"  ✗ {message}")
        
        crawled_count += 1
        
        # Rate limiting - respect Reddit's limits (2 requests per second)
        if i < len(post_ids) and i < max_posts:
            delay = 0.6  # Slightly faster for JSON API
            time.sleep(delay)
        
        # Progress update every 10 posts
        if i % 10 == 0:
            print(f"\nProgress: {i}/{min(len(post_ids), max_posts)} crawled "
                  f"({success_count} success, {error_count} errors)\n")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Subreddit: r/{subreddit_name}")
    print(f"Posts collected: {len(posts)}")
    print(f"Post IDs extracted: {len(post_ids)}")
    print(f"External URLs: {len(external_urls)}")
    print(f"Posts crawled: {crawled_count}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print()
    print("All crawl history has been recorded in Neo4j.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl Reddit subreddit and track history")
    parser.add_argument(
        "subreddit_url",
        help="Subreddit URL (e.g., https://www.reddit.com/r/BrookeMonkNSFWHub/)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=100,
        help="Maximum posts to crawl (default: 100)"
    )
    
    args = parser.parse_args()
    
    try:
        crawl_subreddit(args.subreddit_url, args.max_posts)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. History saved.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

