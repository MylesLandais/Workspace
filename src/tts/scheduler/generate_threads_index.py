#!/usr/bin/env python3
"""Generate threads.json index for imageboard gallery."""

import json
from pathlib import Path
from typing import List, Dict, Any

THREADS_DIR = Path("cache/imageboard/threads")
OUTPUT_PATH = Path("cache/imageboard/threads.json")

def main():
    threads: List[Dict[str, Any]] = []

    # Process all board directories
    for board_dir in THREADS_DIR.iterdir():
        if not board_dir.is_dir():
            continue

        board = board_dir.name
        print(f"Processing board: {board}")

        # Process thread directories
        for thread_dir in board_dir.iterdir():
            if not thread_dir.is_dir():
                continue

            json_file = thread_dir / "thread.json"
            if not json_file.exists():
                continue

            try:
                with open(json_file, 'r') as f:
                    thread_data = json.load(f)
            except Exception as e:
                print(f"  Error reading {thread_dir.name}: {e}")
                continue

            # Get first image
            first_image = None
            for post in thread_data.get('posts', []):
                if post.get('local_image'):
                    first_image = post.get('local_image')
                    break

            # Get OP data
            op = thread_data.get('posts', [{}])[0]
            thread_id = thread_dir.name

            # Check for HTML file
            html_file = THREADS_DIR / "html" / f"{board}_{thread_id}.html"
            html_path = f"/html/{html_file.name}" if html_file.exists() else None

            threads.append({
                "board": board,
                "thread_id": int(thread_id),
                "title": op.get('sub', 'No subject')[:100],
                "reply_count": op.get('replies', 0),
                "post_count": thread_data.get('post_count', 0),
                "first_image": first_image,
                "html_path": html_path,
                "created_at": op.get('time'),
            })

    # Sort by creation time (newest first)
    threads.sort(key=lambda x: (x.get('created_at') or 0), reverse=True)

    # Write index
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(threads, f, indent=2)

    print(f"Generated index with {len(threads)} threads")
    print(f"Output: {OUTPUT_PATH}")

if __name__ == '__main__':
    main()