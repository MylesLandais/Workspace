#!/usr/bin/env python3
"""
Reddit RSS Feed Crawler

Alternative method for crawling Reddit using RSS feeds (instead of JSON API).
This is a slower, more rate-limited approach suitable for long-running background
data collection. The primary production system uses Reddit's JSON API endpoints
(see src/feed/platforms/reddit.py).

Note: RSS feeds are a valid alternative but provide less metadata (no scores,
comment counts, etc.) compared to the JSON API approach.

Rate limits to 1-2 requests per minute, collecting 50-100 posts over ~1 hour.
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import feedparser

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.models.post import Post
from feed.storage.neo4j_connection import get_connection
from feed.polling.engine import PollingEngine


class RedditRSSAdapter:
    """Adapter for fetching Reddit posts via RSS feeds."""
    
    def __init__(self, delay_min: float = 30.0, delay_max: float = 60.0):
        """
        Initialize RSS adapter with slow rate limiting.
        
        Args:
            delay_min: Minimum delay between requests (seconds, default 30 = 2/min)
            delay_max: Maximum delay between requests (seconds, default 60 = 1/min)
        """
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; RSS Reader 1.0; +http://example.com/bot)"
        }
    
    def _delay(self):
        """Add random delay between requests."""
        delay = random.uniform(self.delay_min, self.delay_max)
        print(f"  Waiting {delay:.1f} seconds before next request...")
        time.sleep(delay)
    
    def fetch_posts_from_rss(
        self, 
        subreddit: str, 
        use_old_reddit: bool = False
    ) -> List[Post]:
        """
        Fetch posts from a subreddit RSS feed.
        
        Args:
            subreddit: Subreddit name (with or without r/ prefix)
            use_old_reddit: If True, use old.reddit.com RSS endpoint as fallback.
                          Some RSS feeds may be more reliable on old.reddit.com.
                          This is for RSS feed compatibility only, not HTML scraping.
        
        Returns:
            List of Post objects
        """
        # Clean subreddit name
        subreddit = subreddit.replace("r/", "").replace("/r/", "").strip()
        
        # Build RSS URL
        base_url = "https://old.reddit.com" if use_old_reddit else "https://www.reddit.com"
        rss_url = f"{base_url}/r/{subreddit}/.rss"
        
        print(f"  Fetching RSS feed: {rss_url}")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo and feed.bozo_exception:
                print(f"  Warning: RSS parsing issue: {feed.bozo_exception}")
                if not use_old_reddit:
                    print(f"  Trying old.reddit.com instead...")
                    return self.fetch_posts_from_rss(subreddit, use_old_reddit=True)
            
            if not feed.entries:
                print(f"  No entries found in RSS feed")
                return []
            
            posts = []
            for entry in feed.entries:
                try:
                    # Extract post ID from link or title
                    # Reddit RSS links look like: https://www.reddit.com/r/Subreddit/comments/ID/title/
                    link = entry.get("link", "")
                    post_id = None
                    
                    # Try to extract ID from link
                    if "/comments/" in link:
                        parts = link.split("/comments/")
                        if len(parts) > 1:
                            post_id = parts[1].split("/")[0]
                    
                    if not post_id:
                        # Fallback: use a hash of the title
                        post_id = f"rss_{hash(entry.get('title', '')) % (10**10)}"
                    
                    # Parse published date
                    published_time = entry.get("published_parsed")
                    if published_time:
                        created_utc = datetime(*published_time[:6])
                    else:
                        created_utc = datetime.utcnow()
                    
                    # Extract subreddit from link if possible
                    subreddit_from_link = subreddit
                    if "/r/" in link:
                        try:
                            subreddit_part = link.split("/r/")[1].split("/")[0]
                            subreddit_from_link = subreddit_part
                        except:
                            pass
                    
                    # Try to extract author (may be in author field or tags)
                    author = None
                    if hasattr(entry, "author"):
                        author = entry.author
                    elif hasattr(entry, "tags") and entry.tags:
                        # Sometimes author is in tags
                        for tag in entry.tags:
                            if hasattr(tag, "term") and tag.term.startswith("author:"):
                                author = tag.term.replace("author:", "")
                                break
                    
                    # Extract URL (link to post or content URL)
                    url = entry.get("link", "")
                    
                    # Check for content links (e.g., i.redd.it images)
                    if hasattr(entry, "links"):
                        for link_obj in entry.links:
                            href = link_obj.get("href", "")
                            # Prefer image URLs
                            if "i.redd.it" in href or "i.imgur.com" in href:
                                url = href
                                break
                    
                    # Create Post object
                    post = Post(
                        id=post_id,
                        title=entry.get("title", "")[:500],  # Limit title length
                        created_utc=created_utc,
                        score=0,  # RSS doesn't include score
                        num_comments=0,  # RSS may not include comments
                        upvote_ratio=0.0,  # RSS doesn't include ratio
                        over_18=False,  # Can't determine from RSS
                        url=url,
                        selftext=entry.get("summary", "")[:5000],  # Limit selftext length
                        author=author,
                        subreddit=subreddit_from_link,
                        permalink=entry.get("link", ""),
                    )
                    posts.append(post)
                    
                except Exception as e:
                    print(f"  Error parsing entry: {e}")
                    continue
            
            print(f"  Successfully parsed {len(posts)} posts from RSS feed")
            return posts
            
        except Exception as e:
            print(f"  Error fetching RSS feed: {e}")
            return []


def crawl_subreddits(
    subreddits: List[str],
    target_posts: int = 75,
    delay_min: float = 30.0,
    delay_max: float = 60.0,
    save_to_db: bool = True,
):
    """
    Crawl multiple subreddits via RSS feeds with slow rate limiting.
    
    Args:
        subreddits: List of subreddit names to crawl
        target_posts: Target number of posts to collect (default: 75)
        delay_min: Minimum delay between requests (seconds)
        delay_max: Maximum delay between requests (seconds)
        save_to_db: If True, save posts to Neo4j database
    """
    print("=" * 70)
    print("Reddit RSS Feed Crawler")
    print("=" * 70)
    print(f"\nTarget: Collect {target_posts} new posts")
    print(f"Rate limit: {delay_min}-{delay_max} seconds between requests")
    print(f"Estimated time: ~{(target_posts * (delay_min + delay_max) / 2) / 60:.1f} minutes")
    print(f"\nSubreddits to crawl: {', '.join([f'r/{s}' for s in subreddits])}")
    
    if save_to_db:
        try:
            neo4j = get_connection()
            print(f"\nConnected to Neo4j: {neo4j.uri}")
        except Exception as e:
            print(f"\nError connecting to Neo4j: {e}")
            print("Make sure NEO4J_URI and NEO4J_PASSWORD are set in .env")
            return 1
    else:
        print("\nDRY RUN MODE - Posts will not be saved to database")
        neo4j = None
    
    adapter = RedditRSSAdapter(delay_min=delay_min, delay_max=delay_max)
    
    all_posts = []
    subreddit_index = 0
    iteration = 0
    
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("Starting crawl...")
    print("=" * 70 + "\n")
    
    while len(all_posts) < target_posts:
        iteration += 1
        subreddit = subreddits[subreddit_index % len(subreddits)]
        
        print(f"\n--- Iteration {iteration} ---")
        print(f"Fetching posts from r/{subreddit}...")
        
        posts = adapter.fetch_posts_from_rss(subreddit)
        
        if posts:
            # Deduplicate
            existing_ids = {p.id for p in all_posts}
            new_posts = [p for p in posts if p.id not in existing_ids]
            
            if new_posts:
                all_posts.extend(new_posts)
                print(f"  Added {len(new_posts)} new posts (total: {len(all_posts)})")
                
                # Save to database if requested
                if save_to_db and neo4j:
                    engine = PollingEngine(None, neo4j, dry_run=False)
                    # Manually store posts (we bypass the platform adapter)
                    for post in new_posts:
                        try:
                            engine._store_posts([post], post.subreddit)
                        except Exception as e:
                            print(f"  Warning: Error saving post {post.id}: {e}")
            else:
                print(f"  All {len(posts)} posts already collected")
        else:
            print(f"  No posts retrieved")
        
        # Check if we've reached our target
        if len(all_posts) >= target_posts:
            print(f"\n✓ Reached target of {target_posts} posts!")
            break
        
        # Move to next subreddit for round-robin
        subreddit_index += 1
        
        # Delay before next request
        if len(all_posts) < target_posts:
            adapter._delay()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("Crawl Complete")
    print("=" * 70)
    print(f"\nTotal posts collected: {len(all_posts)}")
    print(f"Total time: {elapsed_time / 60:.1f} minutes")
    if elapsed_time > 0:
        print(f"Average posts per minute: {len(all_posts) / (elapsed_time / 60):.1f}")
    
    if all_posts:
        print(f"\nPosts by subreddit:")
        from collections import Counter
        subreddit_counts = Counter(p.subreddit for p in all_posts)
        for subreddit, count in subreddit_counts.items():
            print(f"  r/{subreddit}: {count} posts")
        
        print(f"\nDate range:")
        dates = [p.created_utc for p in all_posts]
        print(f"  Oldest: {min(dates)}")
        print(f"  Newest: {max(dates)}")
    
    return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Crawl Reddit RSS feeds with slow rate limiting"
    )
    parser.add_argument(
        "subreddits",
        nargs="+",
        help="Subreddit names to crawl (e.g., Sjokz BrookeMonkTheSecond)",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=75,
        help="Target number of posts to collect (default: 75)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=30.0,
        help="Minimum delay between requests in seconds (default: 30 = 2 req/min)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=60.0,
        help="Maximum delay between requests in seconds (default: 60 = 1 req/min)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save to database (dry run mode)",
    )
    
    args = parser.parse_args()
    
    return crawl_subreddits(
        subreddits=args.subreddits,
        target_posts=args.target,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        save_to_db=not args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())


