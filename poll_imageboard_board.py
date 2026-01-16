"""Poll imageboard board for threads matching keywords and process images."""

import sys
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import argparse

# Add both project root and src to path for proper imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.fourchan import ImageboardAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection
from feed.models.post import Post


def poll_imageboard_board(
    board: str,
    keywords: Optional[List[str]] = None,
    max_threads: int = 10,
    max_posts: int = 100,
    dry_run: bool = False,
):
    """
    Poll an imageboard board for threads matching keywords and process images.
    
    Args:
        board: Board name (e.g., "b", "pol")
        keywords: List of keywords to filter threads (default: ["irl"])
        max_threads: Maximum number of threads to process per run
        max_posts: Maximum number of posts to collect
        dry_run: If True, don't write to database
    """
    print("=" * 70)
    print("IMAGEBOARD BOARD POLLER")
    print("=" * 70)
    print(f"Board: /{board}/")
    print(f"Keywords: {keywords or ['irl']}")
    print(f"Max threads: {max_threads}")
    print(f"Max posts: {max_posts}")
    if dry_run:
        print("DRY RUN MODE - No data will be written to database")
    print()
    
    # Initialize connections
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Initialize imageboard adapter with keyword filtering
    imageboard = ImageboardAdapter(
        delay_min=2.0,
        delay_max=5.0,
        keywords=keywords or ["irl"],
        mock=False
    )
    
    # Initialize polling engine
    engine = PollingEngine(
        platform=imageboard,
        neo4j=neo4j,
        dry_run=dry_run,
        hash_images=True,
        enable_deduplication=True,
    )
    
    # Step 1: Fetch threads matching keywords
    print("\n" + "=" * 70)
    print("STEP 1: FETCHING THREADS FROM CATALOG")
    print("=" * 70)
    
    threads = imageboard.fetch_threads(board)
    print(f"Found {len(threads)} threads matching keywords")
    
    if not threads:
        print("No threads found. Exiting.")
        return
    
    # Limit threads to process
    threads_to_process = threads[:max_threads]
    print(f"Processing {len(threads_to_process)} threads...")
    print()
    
    # Step 2: Fetch posts from matching threads
    print("\n" + "=" * 70)
    print("STEP 2: FETCHING POSTS FROM THREADS")
    print("=" * 70)
    
    all_posts = []
    threads_processed = 0
    threads_archived = 0
    
    for thread_data in threads_to_process:
        thread_id = thread_data.get("no")
        subject = thread_data.get("sub", "") or "No subject"
        
        print(f"\nThread {thread_id}: {subject[:60]}...")
        
        # Fetch thread
        thread = imageboard.fetch_thread(board, thread_id)
        if not thread:
            threads_archived += 1
            print(f"  -> Thread archived or not found, skipping")
            continue
        
        posts = thread.get("posts", [])
        image_posts = [p for p in posts if p.get("tim")]
        
        print(f"  -> Found {len(image_posts)} posts with images")
        
        # Convert posts to Post objects
        for post_data in posts:
            if not post_data.get("tim"):
                continue
            
            tim = post_data.get("tim")
            ext = post_data.get("ext", ".jpg")
            image_url = f"https://i.4cdn.org/{board}/{tim}{ext}"
            
            post_id = f"{board}_{thread_id}_{post_data.get('no', '')}"
            created_timestamp = post_data.get("time", 0)
            created_utc = datetime.fromtimestamp(created_timestamp)
            
            # Get comment text (remove HTML tags)
            comment = post_data.get("com", "")
            if comment and "<" in comment:
                comment = re.sub(r'<[^>]+>', '', comment)
            
            post = Post(
                id=post_id,
                title=subject or f"Thread {thread_id}",
                created_utc=created_utc,
                score=post_data.get("replies", 0),
                num_comments=post_data.get("replies", 0),
                upvote_ratio=0.0,
                over_18=True,
                url=image_url,
                selftext=comment,
                author=None,
                subreddit=board,
                permalink=f"/{board}/thread/{thread_id}#p{post_data.get('no', '')}",
            )
            all_posts.append(post)
            
            if len(all_posts) >= max_posts:
                break
        
        threads_processed += 1
        
        if len(all_posts) >= max_posts:
            break
    
    print(f"\nProcessed {threads_processed} threads ({threads_archived} archived)")
    print(f"Collected {len(all_posts)} posts with images")
    
    # Step 3: Deduplicate and store posts
    if all_posts:
        print("\n" + "=" * 70)
        print("STEP 3: DEDUPLICATING AND STORING POSTS")
        print("=" * 70)
        
        # Deduplicate
        new_posts = engine._deduplicate_posts(all_posts)
        print(f"After deduplication: {len(new_posts)} new posts")
        
        if new_posts and not dry_run:
            engine._store_posts(new_posts, board)
            print(f"Stored {len(new_posts)} posts in database")
        elif new_posts:
            print(f"Would store {len(new_posts)} posts (dry run)")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Board: /{board}/")
    print(f"Keywords: {keywords or ['irl']}")
    print(f"Threads found: {len(threads)}")
    print(f"Threads processed: {threads_processed}")
    print(f"Threads archived: {threads_archived}")
    print(f"Posts collected: {len(all_posts)}")
    if all_posts:
        print(f"New posts: {len(new_posts) if all_posts else 0}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll imageboard board for threads matching keywords")
    parser.add_argument(
        "board",
        help="Board name (e.g., 'b', 'pol')"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default="irl",
        help="Comma-separated keywords to filter threads (default: 'irl')"
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=10,
        help="Maximum threads to process per run (default: 10)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=100,
        help="Maximum posts to collect (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't write to database)"
    )
    
    args = parser.parse_args()
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    
    try:
        poll_imageboard_board(
            board=args.board,
            keywords=keywords,
            max_threads=args.max_threads,
            max_posts=args.max_posts,
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
