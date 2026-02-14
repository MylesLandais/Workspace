#!/usr/bin/env python3
"""Download all videos from a thread."""

import os
import sys
import requests
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("cache/imageboard")
IMAGES_DIR = CACHE_DIR / "shared_images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def get_file_sha256(file_path):
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_media(post, board):
    """Download a media file and use SHA256 de-duplication."""
    if 'tim' not in post:
        return None

    filename = f"{post['tim']}{post.get('ext', '.jpg')}"
    url = f"https://i.4cdn.org/{board}/{filename}"
    temp_path = CACHE_DIR / f"temp_{filename}"
    final_filename = f""

    import time

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Downloading: {filename} (attempt {attempt + 1}/{max_retries})")
            resp = requests.get(url, timeout=60, stream=True)
            if resp.status_code == 200:
                with open(temp_path, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                # Compute hash
                sha256 = get_file_sha256(temp_path)
                final_filename = f"{sha256}{post.get('ext', '.jpg')}"
                final_path = IMAGES_DIR / final_filename

                if final_path.exists():
                    print(f"  Duplicate found: {final_filename}")
                    os.remove(temp_path)
                    return final_filename, True # is_duplicate
                else:
                    print(f"  Saved: {final_filename}")
                    os.rename(temp_path, final_path)
                    return final_filename, False # is_duplicate
            elif resp.status_code == 429:
                print(f"  Rate limited (HTTP 429), waiting before retry...")
                wait_time = (attempt + 1) * 5
                time.sleep(wait_time)
                continue
            else:
                print(f"  HTTP {resp.status_code}")
                return None, False
        except Exception as e:
            print(f"  Error: {e}")
            if temp_path.exists():
                os.remove(temp_path)
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            return None, False

    return None, False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python download_thread_videos.py <thread_id>")
        sys.exit(1)

    thread_id = sys.argv[1]
    thread_json = CACHE_DIR / "threads" / "b" / thread_id / "thread.json"

    if not thread_json.exists():
        print(f"Thread not found: {thread_json}")
        sys.exit(1)

    with open(thread_json) as f:
        data = json.load(f)

    downloaded = 0
    for post in data['posts']:
        if post.get('tim') and post.get('ext') in ['.mp4', '.webm']:
            result = download_media(post, 'b')
            if result[0]:
                downloaded += 1
                # Update JSON with local_image
                post['local_image'] = result[0]

    # Save updated JSON
    if downloaded > 0:
        with open(thread_json, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nDownloaded {downloaded} videos")

    # Regenerate HTML
    print("\nRegenerating HTML...")
    os.system(f"nix-shell --run 'python3 fix_thread_video_links.py {thread_id}'")