#!/usr/bin/env python3
"""
Create a unified Parquet dataset from the imageboard thread cache.
Supports filtering by time range (e.g., last 7 days).
"""
import os
import sys
import json
import pandas as pd
import pyarrow as pa
from pyarrow.parquet import write_table
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Configuration
CACHE_DIR = Path('/home/warby/Workspace/jupyter/cache/imageboard/threads')
OUTPUT_DIR = Path('/home/warby/Workspace/jupyter/datasets/parquet')

def create_dataset(days=7, output_name=None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"IMAGEBOARD PIPELINE: EXPORTING LAST {days} DAYS")
    print("=" * 70)
    
    cutoff_time = datetime.now() - timedelta(days=days)
    all_posts = []
    
    if not CACHE_DIR.exists():
        print(f"Error: Cache directory {CACHE_DIR} not found.")
        return

    thread_files = list(CACHE_DIR.glob('**/thread.json'))
    print(f"Found {len(thread_files)} total threads in cache.")

    threads_processed = 0
    posts_exported = 0

    for thread_file in thread_files:
        try:
            # Check file modification time as a quick filter
            mtime = datetime.fromtimestamp(thread_file.stat().st_mtime)
            if mtime < cutoff_time:
                continue

            with open(thread_file, 'r') as f:
                data = json.load(f)
            
            board = thread_file.parent.parent.name
            thread_id = thread_file.parent.name
            
            posts = data.get('posts', [])
            for post in posts:
                post_time = post.get('time', 0)
                post_dt = datetime.fromtimestamp(post_time)
                
                # Filter individual posts by time if needed, though usually we want the whole thread if active
                if post_dt < cutoff_time:
                    continue
                    
                post_data = {
                    'board': board,
                    'thread_id': thread_id,
                    'post_no': post.get('no'),
                    'timestamp': post_time,
                    'datetime_iso': post_dt.isoformat(),
                    'subject': post.get('sub', ''),
                    'comment': post.get('com', ''),
                    'image_id': post.get('tim'),
                    'image_ext': post.get('ext', ''),
                    'image_sha256': post.get('local_image', '').split('.')[0] if post.get('local_image') else None,
                    'local_path': post.get('local_image', ''),
                    'moderated': post.get('moderated', False),
                    'moderation_reason': post.get('moderation_reason', ''),
                    'is_op': post.get('no') == int(thread_id),
                    'export_date': datetime.now().date().isoformat()
                }
                all_posts.append(post_data)
                posts_exported += 1
            
            threads_processed += 1
        except Exception as e:
            print(f"Error processing {thread_file}: {e}")

    if not all_posts:
        print("No posts found matching criteria.")
        return

    # Create DataFrame with explicit schema
    df = pd.DataFrame(all_posts)
    
    # Save to Parquet
    if output_name:
        filename = f"{output_name}.parquet"
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"imageboard_weekly_{timestamp}.parquet"
    
    output_file = OUTPUT_DIR / filename
    latest_file = OUTPUT_DIR / "imageboard_weekly_latest.parquet"
    
    table = pa.Table.from_pandas(df)
    write_table(table, output_file)
    write_table(table, latest_file)
    
    print(f"Summary:")
    print(f"  Threads scanned: {threads_processed}")
    print(f"  Posts exported: {posts_exported}")
    print(f"  Saved to: {output_file}")
    print(f"  Linked to: {latest_file}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Imageboard Parquet Pipeline")
    parser.add_argument("--days", type=int, default=7, help="Number of days to include")
    parser.add_argument("--name", type=str, help="Custom output filename (without extension)")
    args = parser.parse_args()
    
    create_dataset(days=args.days, output_name=args.name)
