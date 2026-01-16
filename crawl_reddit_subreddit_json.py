"""Crawl a Reddit subreddit using JSON API to extract rich thread context."""

import sys
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection


def compute_sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def download_and_cache_image(
    image_url: str,
    cache_dir: Path
) -> Optional[Path]:
    """Download and cache a Reddit image."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; RedditCrawler/1.0)"
        }
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        img_hash = compute_sha256_hash(response.content)
        url_path = image_url.split('?')[0]
        ext = Path(url_path).suffix or '.jpg'
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{img_hash}{ext}"
        cache_path = cache_dir / filename
        
        if not cache_path.exists():
            cache_path.write_bytes(response.content)
        
        return cache_path
    except Exception as e:
        print(f"    ⚠ Error downloading {image_url}: {e}")
        return None


def crawl_subreddit_json(
    subreddit: str,
    max_posts: int = 100,
    include_comments: bool = True,
    download_images: bool = True,
    cache_dir: Optional[Path] = None,
    request_delay: float = 3.0,
):
    """
    Crawl a Reddit subreddit using JSON API.
    
    Args:
        subreddit: Subreddit name (without r/ prefix)
        max_posts: Maximum number of posts to crawl
        include_comments: Whether to fetch full comment threads
        download_images: Whether to download and cache images
        cache_dir: Directory for image cache
        request_delay: Delay between requests in seconds (default: 3.0)
    """
    print("=" * 70)
    print("REDDIT SUBREDDIT JSON CRAWLER")
    print("=" * 70)
    print(f"Subreddit: r/{subreddit}/")
    print(f"Max posts: {max_posts}")
    print(f"Include comments: {include_comments}")
    print(f"Download images: {download_images}")
    print(f"Request delay: {request_delay}s")
    print()
    
    if cache_dir is None:
        cache_dir = Path("cache/reddit/images")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    print()
    
    adapter = RedditAdapter(delay_min=request_delay, delay_max=request_delay + 2.0)
    
    total_posts = 0
    total_comments = 0
    total_images = 0
    cached_images = 0
    start_time = time.time()
    
    print(f"Fetching up to {max_posts} posts from r/{subreddit}...")
    print()
    
    after = None
    posts_crawled = 0
    retry_count = 0
    max_retries = 3
    
    while posts_crawled < max_posts and retry_count < max_retries:
        try:
            limit = min(100, max_posts - posts_crawled)
                
            print(f"Fetching batch of {limit} posts...")
            posts, after = adapter.fetch_posts(
                subreddit,
                sort="new",
                limit=limit,
                after=after
            )
            
            if not posts:
                print("  No more posts found")
                break
            
            print(f"  Got {len(posts)} posts")
            retry_count = 0
            
            for post in posts:
                posts_crawled += 1
                print(f"\n[{posts_crawled}/{max_posts}] {post.title[:60]}...")
                print(f"  ID: {post.id}")
                print(f"  Author: {post.author}")
                print(f"  Score: {post.score}")
                print(f"  URL: {post.url}")
                
                store_post_query = """
                MERGE (p:Post {id: $id})
                SET p.title = $title,
                    p.author = $author,
                    p.score = $score,
                    p.num_comments = $num_comments,
                    p.url = $url,
                    p.selftext = $selftext,
                    p.subreddit = $subreddit,
                    p.permalink = $permalink,
                    p.over_18 = $over_18,
                    p.upvote_ratio = $upvote_ratio,
                    p.created_utc = $created_utc,
                    p.updated_at = datetime()
                MERGE (s:Subreddit {name: $subreddit})
                MERGE (p)-[:POSTED_IN]->(s)
                """
                
                neo4j.execute_write(
                    store_post_query,
                    parameters={
                        "id": post.id,
                        "title": post.title,
                        "author": post.author,
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "url": post.url,
                        "selftext": post.selftext,
                        "subreddit": post.subreddit,
                        "permalink": post.permalink,
                        "over_18": post.over_18,
                        "upvote_ratio": post.upvote_ratio,
                        "created_utc": post.created_utc.isoformat() if post.created_utc else None,
                    }
                )
                
                total_posts += 1
                
                if include_comments:
                    print(f"  Fetching full thread (comments + images)...")
                    
                    thread_post, comments, raw_post_data = adapter.fetch_thread(
                        post.permalink,
                        limit=500
                    )
                    
                    if comments:
                        print(f"    Found {len(comments)} comments")
                        
                        for comment in comments:
                            comment_query = """
                            MERGE (c:Comment {id: $id})
                            SET c.body = $body,
                                c.author = $author,
                                c.score = $score,
                                c.depth = $depth,
                                c.is_submitter = $is_submitter,
                                c.created_utc = $created_utc,
                                c.link_id = $link_id,
                                c.updated_at = datetime()
                            MERGE (p:Post {id: $post_id})
                            MERGE (c)-[:REPLIED_TO]->(p)
                            """
                            
                            neo4j.execute_write(
                                comment_query,
                                parameters={
                                    "id": comment.id,
                                    "body": comment.body,
                                    "author": comment.author,
                                    "score": comment.score,
                                    "depth": comment.depth,
                                    "is_submitter": comment.is_submitter,
                                    "created_utc": comment.created_utc.isoformat() if comment.created_utc else None,
                                    "link_id": comment.link_id,
                                    "post_id": post.id,
                                }
                            )
                            total_comments += 1
                    
                    post_images = adapter.extract_all_images(thread_post, raw_post_data)
                    comment_images = adapter.extract_images_from_comments(comments)
                    all_images = post_images + [ci['url'] for ci in comment_images]
                    
                    total_images += len(all_images)
                    print(f"    Found {len(post_images)} post images, {len(comment_images)} comment images")
                    
                    if download_images and all_images:
                        for img_url in all_images:
                            cache_path = download_and_cache_image(img_url, cache_dir)
                            if cache_path:
                                cached_images += 1
                        
                        for img_url in all_images:
                            image_query = """
                            MERGE (i:Image {url: $url})
                            SET i.updated_at = datetime()
                            MERGE (p:Post {id: $post_id})
                            MERGE (p)-[:HAS_IMAGE]->(i)
                            """
                            
                            neo4j.execute_write(
                                image_query,
                                parameters={
                                    "url": img_url,
                                    "post_id": post.id,
                                }
                            )
                        
                        print(f"    Cached {cached_images} images total")
                
                time.sleep(request_delay)
            
            if not after:
                break
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_count += 1
                wait_time = (2 ** retry_count) * 10
                print(f"\n⚠ Rate limited (429). Waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            break
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("CRAWL COMPLETE")
    print("=" * 70)
    print(f"\nTotal time: {elapsed / 60:.1f} minutes")
    print(f"\nPosts crawled: {total_posts}")
    print(f"Comments stored: {total_comments}")
    print(f"Images found: {total_images}")
    print(f"Images cached: {cached_images}")
    print(f"\nCache directory: {cache_dir}")
    cache_files = list(cache_dir.glob('*'))
    if cache_files:
        cache_size = sum(f.stat().st_size for f in cache_files if f.is_file()) / (1024*1024)
        print(f"Cache size: {cache_size:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Crawl a Reddit subreddit using JSON API for rich context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl 20 posts with full comments and images
  python crawl_reddit_subreddit_json.py JordynJonesCandy --max-posts 20

  # Crawl with slower rate limiting (5 second delays)
  python crawl_reddit_subreddit_json.py JordynJonesCandy --max-posts 50 --delay 5

  # Crawl without comments (faster)
  python crawl_reddit_subreddit_json.py JordynJonesCandy --max-posts 100 --no-comments

  # Crawl without downloading images
  python crawl_reddit_subreddit_json.py JordynJonesCandy --max-posts 100 --no-images
        """
    )
    parser.add_argument(
        "subreddit",
        help="Subreddit name (with or without r/ prefix)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=20,
        help="Maximum posts to crawl (default: 20)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Delay between requests in seconds (default: 3.0)"
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Don't fetch comments (faster, less data)"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't download images"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache/reddit/images"),
        help="Directory for caching images"
    )
    
    args = parser.parse_args()
    
    try:
        crawl_subreddit_json(
            subreddit=args.subreddit,
            max_posts=args.max_posts,
            include_comments=not args.no_comments,
            download_images=not args.no_images,
            cache_dir=args.cache_dir,
            request_delay=args.delay,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
