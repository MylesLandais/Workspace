#!/usr/bin/env python3
"""
Download missing images for a specific thread from thread.json data.
"""
import sys
import json
from pathlib import Path
import urllib.request
import urllib.error

# Container paths
PROJECT_ROOT = Path('/home/jovyan/workspaces')
CACHE_DIR = PROJECT_ROOT / 'cache/imageboard'
THREAD_ID = '944484125'
BOARD = 'b'
THREAD_JSON_PATH = CACHE_DIR / 'threads' / BOARD / THREAD_ID / 'thread.json'
SHARED_IMAGES_DIR = CACHE_DIR / 'shared_images'

def download_images():
    if not THREAD_JSON_PATH.exists():
        print(f"ERROR: Thread JSON not found: {THREAD_JSON_PATH}")
        return False

    try:
        with open(THREAD_JSON_PATH, 'r') as f:
            thread_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read thread.json: {e}")
        return False

    posts = thread_data.get('posts', [])
    
    total_files = 0
    downloaded = 0
    failed = 0

    for post in posts:
        # Skip deleted posts or posts without files
        if post.get('file_deleted', False) or post.get('tim', 0) == 0:
            continue
        
        total_files += 1
        tim = post.get('tim')
        ext = post.get('ext', '').split('.')[-1]
        filename = f"{tim}.{ext}"
        local_path = SHARED_IMAGES_DIR / filename

        # Check if already downloaded
        if local_path.exists():
            continue

        # Construct 4chan CDN URL
        image_url = f"https://i.4cdn.org/{BOARD}/{tim}.{ext}"
        
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            downloaded += 1
            if downloaded % 10 == 0 or downloaded == total_files:
                print(f"Downloaded {downloaded}/{total_files} files...")
        except Exception as e:
            failed += 1
            print(f"Failed to download {filename}: {e}")

    print("-" * 50)
    print(f"Image Download Summary for {BOARD}/{THREAD_ID}")
    print(f"Total Files in Thread: {total_files}")
    print(f"Successfully Downloaded: {downloaded}")
    print(f"Failed: {failed}")
    print("-" * 50)
    return failed == 0

if __name__ == "__main__":
    download_images()