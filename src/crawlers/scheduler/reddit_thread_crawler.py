#!/usr/bin/env python3
"""Reddit thread crawler for slow crawling specific subreddits with full comment and image extraction."""

import sys
import time
import random
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.models.post import Post
from feed.models.comment import Comment
from feed.storage.neo4j_connection import get_connection
from feed.storage.thread_storage import store_thread_from_crawl_result


# Slow delay settings (in seconds)
THREAD_DELAY_MIN = 15.0
THREAD_DELAY_MAX = 30.0

# Between subreddit listings
LISTING_DELAY_MIN = 10.0
LISTING_DELAY_MAX = 20.0


def random_delay(min_sec: float, max_sec: float, reason: str = ""):
    """Sleep for a random duration and log it."""
    delay = random.uniform(min_sec, max_sec)
    if reason:
        print(f"  [DELAY] {reason}: {delay:.1f} seconds")
    time.sleep(delay)


def extract_post_id_from_url(url: str) -> Optional[str]:
    """Extract post ID from Reddit URL."""
    # Format: https://www.reddit.com/r/subreddit/comments/POST_ID/title/
    parts = url.rstrip("/").split("/")
    if "comments" in parts:
        idx = parts.index("comments")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def crawl_thread(
    reddit: RedditAdapter,
    permalink: str,
    output_dir: Path,
    save_images: bool = True,
    save_comments: bool = True,
) -> dict:
    """
    Crawl a single Reddit thread and extract all images and comments.
    
    Args:
        reddit: RedditAdapter instance
        permalink: Reddit thread permalink or URL
        output_dir: Directory to save data
        save_images: Whether to save image metadata
        save_comments: Whether to save comments
    
    Returns:
        Dictionary with crawl results
    """
    print(f"\n{'='*80}")
    print(f"Crawling thread: {permalink}")
    print(f"{'='*80}")
    
    # Fetch thread with comments
    post, comments, raw_post_data = reddit.fetch_thread(permalink)
    
    if not post:
        print(f"ERROR: Failed to fetch thread {permalink}")
        return {"success": False, "permalink": permalink}
    
    print(f"Post: {post.title[:80]}...")
    print(f"Author: {post.author}")
    print(f"Subreddit: r/{post.subreddit}")
    print(f"Score: {post.score}, Comments: {len(comments)}")
    print(f"OP selftext: {post.selftext[:100] if post.selftext else '(none)'}...")
    
    result = {
        "success": True,
        "permalink": permalink,
        "post_id": post.id,
        "timestamp": datetime.utcnow().isoformat(),
        "post": {
            "id": post.id,
            "title": post.title,
            "author": post.author,
            "subreddit": post.subreddit,
            "created_utc": post.created_utc.isoformat(),
            "score": post.score,
            "num_comments": post.num_comments,
            "upvote_ratio": post.upvote_ratio,
            "selftext": post.selftext,
            "url": post.url,
            "permalink": post.permalink,
        },
        "images": [],
        "comments": [],
        "op_comments": [],
    }
    
    # Extract all images from the post
    if save_images and raw_post_data:
        images = reddit.extract_all_images(post, raw_post_data)
        print(f"\nFound {len(images)} image(s) from post:")
        for idx, img_url in enumerate(images, 1):
            print(f"  {idx}. {img_url}")
            result["images"].append({
                "url": img_url,
                "source": "post",
            })
        
        # Extract images from comments
        if comments:
            comment_images = reddit.extract_images_from_comments(comments)
            if comment_images:
                print(f"\nFound {len(comment_images)} image(s) from comments:")
                for idx, img_info in enumerate(comment_images, 1):
                    print(f"  {idx}. {img_info['url']} (from comment {img_info['comment_id']} by {img_info['author']})")
                    result["images"].append({
                        "url": img_info["url"],
                        "source": "comment",
                        "comment_id": img_info["comment_id"],
                        "comment_author": img_info["author"],
                    })
    
    # Extract OP context
    op_context = {
        "selftext": post.selftext,
        "title": post.title,
    }
    
    # Extract comments, especially OP's comments
    if save_comments:
        op_comments_list = []
        all_comments_list = []
        
        for comment in comments:
            comment_data = {
                "id": comment.id,
                "body": comment.body,
                "author": comment.author,
                "created_utc": comment.created_utc.isoformat(),
                "score": comment.score,
                "ups": comment.ups,
                "downs": comment.downs,
                "depth": comment.depth,
                "is_submitter": comment.is_submitter,
                "parent_id": comment.parent_id,
                "permalink": comment.permalink,
            }
            all_comments_list.append(comment_data)
            
            # Capture OP comments separately
            if comment.is_submitter:
                op_comments_list.append(comment_data)
        
        result["comments"] = all_comments_list
        result["op_comments"] = op_comments_list
        
        print(f"\nComments summary:")
        print(f"  Total comments: {len(all_comments_list)}")
        print(f"  OP comments: {len(op_comments_list)}")
        
        # Print OP comments
        if op_comments_list:
            print(f"\nOP Comments ({len(op_comments_list)}):")
            for idx, op_comment in enumerate(op_comments_list, 1):
                print(f"  {idx}. [{op_comment['score']} pts] {op_comment['body'][:100]}...")
    
    # Save to JSON file
    output_file = output_dir / f"thread_{post.id}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to: {output_file}")
    
    return result


def crawl_subreddit_threads(
    subreddit: str,
    sort: str = "new",
    limit: int = 25,
    output_dir: Optional[Path] = None,
    delay_min: float = THREAD_DELAY_MIN,
    delay_max: float = THREAD_DELAY_MAX,
    target_permalink: Optional[str] = None,
    store_to_neo4j: bool = True,
):
    """
    Crawl threads from a subreddit, fetching full comments and images.
    
    Args:
        subreddit: Subreddit name (with or without r/ prefix)
        sort: Sort order ("new", "hot", "top", "rising")
        limit: Number of threads to process
        output_dir: Output directory (default: ./data/reddit_threads/{subreddit})
        delay_min: Minimum delay between threads
        delay_max: Maximum delay between threads
        target_permalink: Optional specific permalink to crawl (overrides subreddit listing)
    """
    # Setup output directory
    if output_dir is None:
        output_dir = Path("./data/reddit_threads") / subreddit.replace("r/", "")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("REDDIT THREAD CRAWLER")
    print("=" * 80)
    print(f"Subreddit: r/{subreddit}")
    print(f"Sort: {sort}")
    print(f"Output: {output_dir}")
    print(f"Delays: {delay_min}-{delay_max} seconds between threads")
    print("=" * 80)
    
    # Initialize Reddit adapter with slow delays
    reddit = RedditAdapter(
        mock=False,
        delay_min=2.0,  # Base delay for API calls
        delay_max=5.0,
    )
    
    # Initialize Neo4j connection if storing to graph
    neo4j = None
    if store_to_neo4j:
        try:
            neo4j = get_connection()
            print(f"Connected to Neo4j: {neo4j.uri}")
            
            # Run migration if needed
            migration_path = Path(__file__).parent / "src" / "feed" / "storage" / "migrations" / "006_thread_comments_images.cypher"
            if migration_path.exists():
                print("Running schema migration...")
                with open(migration_path) as f:
                    migration = f.read()
                statements = [s.strip() for s in migration.split(";") if s.strip()]
                for stmt in statements:
                    if stmt:
                        try:
                            neo4j.execute_write(stmt)
                        except Exception as e:
                            if "already exists" not in str(e).lower() and "constraint" not in str(e).lower():
                                print(f"  Migration warning: {e}")
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j: {e}")
            print("Continuing without graph storage...")
            store_to_neo4j = False
    
    # If targeting a specific permalink, just crawl that
    if target_permalink:
        print(f"\nTargeting specific thread: {target_permalink}")
        result = crawl_thread(reddit, target_permalink, output_dir)
        if store_to_neo4j and neo4j and result.get("success"):
            print("\nStoring thread in Neo4j...")
            try:
                store_thread_from_crawl_result(neo4j, result)
                print("  Successfully stored in Neo4j")
            except Exception as e:
                print(f"  Error storing in Neo4j: {e}")
        return
    
    # Otherwise, fetch subreddit listing and crawl each thread
    print(f"\nFetching r/{subreddit} ({sort})...")
    posts, _ = reddit.fetch_posts(source=subreddit, sort=sort, limit=limit)
    
    if not posts:
        print(f"No posts found in r/{subreddit}")
        return
    
    print(f"Found {len(posts)} posts. Crawling threads...")
    
    results = []
    for idx, post in enumerate(posts, 1):
        print(f"\n[{idx}/{len(posts)}] Processing post: {post.id}")
        
        if not post.permalink:
            print(f"  Skipping post {post.id} - no permalink")
            continue
        
        try:
            # Build full permalink
            permalink = post.permalink
            if not permalink.startswith("http"):
                permalink = f"https://www.reddit.com{permalink}"
            
            result = crawl_thread(reddit, permalink, output_dir)
            results.append(result)
            
            # Store in Neo4j if enabled
            if store_to_neo4j and neo4j and result.get("success"):
                try:
                    store_thread_from_crawl_result(neo4j, result)
                    print(f"  Stored in Neo4j")
                except Exception as e:
                    print(f"  Error storing in Neo4j: {e}")
            
        except Exception as e:
            print(f"  ERROR processing thread {post.id}: {e}")
            results.append({"success": False, "post_id": post.id, "error": str(e)})
        
        # Delay between threads (except for the last one)
        if idx < len(posts):
            random_delay(delay_min, delay_max, f"Before next thread")
    
    # Save summary
    summary = {
        "subreddit": subreddit,
        "sort": sort,
        "timestamp": datetime.utcnow().isoformat(),
        "total_posts": len(posts),
        "results": results,
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
    }
    
    summary_file = output_dir / "crawl_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("CRAWL COMPLETE")
    print("=" * 80)
    print(f"Total threads: {len(results)}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Summary saved to: {summary_file}")
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl Reddit threads with full comments and images")
    parser.add_argument("subreddit", help="Subreddit name (with or without r/ prefix)")
    parser.add_argument("--sort", default="new", choices=["new", "hot", "top", "rising"],
                       help="Sort order (default: new)")
    parser.add_argument("--limit", type=int, default=25, help="Number of threads to crawl (default: 25)")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--delay-min", type=float, default=THREAD_DELAY_MIN,
                       help=f"Minimum delay between threads (default: {THREAD_DELAY_MIN})")
    parser.add_argument("--delay-max", type=float, default=THREAD_DELAY_MAX,
                       help=f"Maximum delay between threads (default: {THREAD_DELAY_MAX})")
    parser.add_argument("--permalink", help="Specific thread permalink/URL to crawl (overrides subreddit listing)")
    parser.add_argument("--no-neo4j", action="store_true", help="Skip storing results in Neo4j")
    
    args = parser.parse_args()
    
    try:
        crawl_subreddit_threads(
            subreddit=args.subreddit,
            sort=args.sort,
            limit=args.limit,
            output_dir=args.output,
            delay_min=args.delay_min,
            delay_max=args.delay_max,
            target_permalink=args.permalink,
            store_to_neo4j=not args.no_neo4j,
        )
    except KeyboardInterrupt:
        print("\n\nCrawler interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

