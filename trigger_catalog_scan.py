#!/usr/bin/env python3
"""Trigger manual catalog scan for imageboard monitoring (DevOps recovery tool).

This script is designed for system recovery and restart scenarios.
It manually triggers a catalog scan and queues matching threads.

Usage:
    python3 trigger_catalog_scan.py                  # Scan and queue all matches
    python3 trigger_catalog_scan.py --dry-run        # Show what would be queued
    python3 trigger_catalog_scan.py --max-threads 20 # Limit threads queued
    python3 trigger_catalog_scan.py --min-replies 50 # Filter by activity
"""

import argparse
import os
import sys
import json
import redis
import requests
import time
from pathlib import Path
from datetime import datetime

# Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
DEFAULT_BOARD = 'b'
KEYWORDS = ["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss", "actresses", "tiny", "cosplay"]

def poll_catalog(board):
    """Fetch catalog and find matching threads."""
    url = f"https://a.4cdn.org/{board}/catalog.json"
    
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        catalog = resp.json()
    except Exception as e:
        print(f"ERROR: Failed to fetch catalog: {e}", file=sys.stderr)
        return []

    matched_threads = []
    for page in catalog:
        for thread in page.get("threads", []):
            sub = str(thread.get("sub", "")).lower()
            com = str(thread.get("com", "")).lower()
            text = f"{sub} {com}"
            
            if any(k.lower() in text for k in KEYWORDS):
                sub = thread.get("sub", "")
                if not sub:
                    com = thread.get("com", "")
                    preview = com[:100].replace('\n', ' ') if len(com) > 100 else com
                    sub = f"[{preview}]"
                
                matched_threads.append({
                    "board": board,
                    "thread_id": thread["no"],
                    "subject": sub[:100],
                    "replies": thread.get("replies", 0),
                    "last_modified": thread.get("last_modified", 0)
                })
    
    return matched_threads

def get_queue_depth():
    """Get current Redis queue depth."""
    try:
        r = redis.from_url(REDIS_URL)
        return r.llen('queue:monitors')
    except Exception as e:
        print(f"WARNING: Could not get queue depth: {e}", file=sys.stderr)
        return None

def queue_threads(threads, dry_run=False, max_threads=None, min_replies=0):
    """Push threads to Redis queue."""
    if not threads:
        return 0
    
    if max_threads:
        threads = threads[:max_threads]
    
    if min_replies > 0:
        threads = [t for t in threads if t.get('replies', 0) >= min_replies]
    
    if dry_run:
        return len(threads)
    
    r = redis.from_url(REDIS_URL)
    queued_count = 0
    
    for thread in threads:
        job_data = json.dumps(thread)
        r.rpush('queue:monitors', job_data)
        queued_count += 1
    
    return queued_count

def main():
    parser = argparse.ArgumentParser(description='Manual catalog scan trigger (DevOps recovery tool)')
    parser.add_argument('--dry-run', action='store_true', help='Show matches without queueing')
    parser.add_argument('--max-threads', type=int, help='Maximum threads to queue (default: unlimited)')
    parser.add_argument('--min-replies', type=int, default=0, help='Minimum reply count (default: 0)')
    parser.add_argument('--board', default=DEFAULT_BOARD, help=f'Board to scan (default: {DEFAULT_BOARD})')
    args = parser.parse_args()
    
    target_board = args.board
    
    print("=" * 70)
    print(f"IMAGEBOARD CATALOG SCAN - /{target_board}/ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"Keywords: {KEYWORDS}")
    
    # Get initial queue state
    initial_depth = get_queue_depth()
    if initial_depth is not None:
        print(f"Initial queue depth: {initial_depth}")
    print()
    
    # Poll catalog
    start_time = time.time()
    print(f"Polling catalog for /{target_board}/...")
    matched_threads = poll_catalog(board=target_board)
    fetch_time = time.time() - start_time
    
    if not matched_threads:
        print(f"No threads matched keywords.")
        return
    
    print(f"Catalog fetch completed in {fetch_time:.2f}s")
    print(f"Found {len(matched_threads)} matching threads")
    print()
    
    # Show sample of matched threads
    print("Sample matches (first 5):")
    for i, t in enumerate(matched_threads[:5]):
        print(f"  [{t['thread_id']}] {t['subject'][:60]} ({t['replies']} replies)")
    if len(matched_threads) > 5:
        print(f"  ... and {len(matched_threads) - 5} more")
    print()
    
    # Check if filtering applies
    if args.max_threads and args.max_threads < len(matched_threads):
        print(f"Filter: Will queue max {args.max_threads} threads (limit)")
    if args.min_replies > 0:
        filtered_count = len([t for t in matched_threads if t.get('replies', 0) >= args.min_replies])
        print(f"Filter: Will queue {filtered_count} threads (min {args.min_replies} replies)")
    
    # Queue threads
    queued = queue_threads(matched_threads, dry_run=args.dry_run, max_threads=args.max_threads, min_replies=args.min_replies)
    
    # Report results
    print()
    print("=" * 70)
    if args.dry_run:
        print(f"DRY RUN - Would queue {queued} threads")
    else:
        print(f"SUCCESS - Queued {queued} threads")
        final_depth = get_queue_depth()
        if final_depth is not None:
            print(f"Final queue depth: {final_depth}")
            if initial_depth is not None:
                delta = final_depth - initial_depth
                print(f"Queue change: +{delta} threads")
    print("=" * 70)

if __name__ == "__main__":
    main()
