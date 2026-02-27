#!/usr/bin/env python3
"""Crawl a specific 4chan thread and save to JSON."""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.fourchan import ImageboardAdapter


def crawl_thread(board: str, thread_id: int, output_dir: str = "./output"):
    """Crawl a single thread and save to JSON."""
    adapter = ImageboardAdapter(delay_min=1.0, delay_max=2.0)
    
    print(f"Fetching thread /{board}/{thread_id}...")
    thread_data = adapter.fetch_thread(board, thread_id)
    
    if not thread_data:
        print(f"Thread not found or archived: /{board}/{thread_id}")
        return False
    
    # Create output directory
    out_path = Path(output_dir) / board / str(thread_id)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Save thread JSON
    json_path = out_path / "thread.json"
    with open(json_path, "w") as f:
        json.dump(thread_data, f, indent=2)
    
    posts = thread_data.get("posts", [])
    print(f"Saved {len(posts)} posts to {json_path}")
    
    # Count images
    images = [p for p in posts if p.get("tim")]
    print(f"Thread has {len(images)} images")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl a specific 4chan thread")
    parser.add_argument("board", help="Board name (e.g., 'b', 'pol')")
    parser.add_argument("thread_id", type=int, help="Thread ID number")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    
    args = parser.parse_args()
    
    success = crawl_thread(args.board, args.thread_id, args.output)
    sys.exit(0 if success else 1)
