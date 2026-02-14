#!/usr/bin/env python3
"""Fix HTML to handle videos even if they're remote URLs."""

import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
import time
import hashlib
import requests

CACHE_DIR = Path("cache/imageboard")
IMAGES_DIR = CACHE_DIR / "shared_images"

def get_file_sha256(file_path):
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_video_if_missing(post, board):
    """Download a video if not already cached."""
    if 'tim' not in post or post.get('ext') not in ['.mp4', '.webm']:
        return None

    # Check if already in image_map
    if 'local_image' in post and post['local_image']:
        return post['local_image']

    filename = f"{post['tim']}{post['ext']}"
    url = f"https://i.4cdn.org/{board}/{filename}"
    temp_path = CACHE_DIR / f"temp_{filename}"

    # Try download with retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=60, stream=True)
            if resp.status_code == 200:
                with open(temp_path, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                sha256 = get_file_sha256(temp_path)
                final_filename = f"{sha256}{post['ext']}"
                final_path = IMAGES_DIR / final_filename

                if final_path.exists():
                    print(f"  [video] Already cached: {final_filename}")
                    os.remove(temp_path)
                    return final_filename
                else:
                    print(f"  [video] Downloaded: {final_filename}")
                    os.rename(temp_path, final_path)
                    return final_filename
            elif resp.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"  [video] Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"  [video] HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"  [video] Error: {e}")
            if temp_path.exists():
                os.remove(temp_path)
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 5)
                continue
            return None

    return None

def fix_thread_html(html_file: Path, thread_json_file: Path, board='b'):
    """Fix HTML to handle both local and remote videos."""
    # Read thread JSON
    with open(thread_json_file) as f:
        thread_data = json.load(f)

    # Build image map (including trying to download missing videos)
    image_map = {}
    for post in thread_data.get('posts', []):
        if 'local_image' in post and post['local_image']:
            image_map[post['no']] = post['local_image']
        elif post.get('ext') in ['.mp4', '.webm']:
            # Try to download missing videos
            local_filename = download_video_if_missing(post, board)
            if local_filename:
                image_map[post['no']] = local_filename
                post['local_image'] = local_filename  # Update JSON

    # Save updated JSON
    with open(thread_json_file, 'w') as f:
        json.dump(thread_data, f, indent=2)

    # Read HTML
    with open(html_file) as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Determine prefix
    prefix = "../" if 'html/' in str(html_file) else "../../../"

    # Fix video tags
    fixed_videos = 0
    for post_no, local_filename in image_map.items():
        post_div = soup.find(id=f"pc{post_no}")
        if post_div:
            # Update thumbnail images
            thumb_link = post_div.find('a', class_='fileThumb')
            if thumb_link:
                thumb_link['href'] = f"{prefix}shared_images/{local_filename}"
                img = thumb_link.find('img')
                if img:
                    img['src'] = f"{prefix}shared_images/{local_filename}"
                    if img.has_attr('srcset'):
                        del img['srcset']

            # Update video tags (expanded webm/mp4)
            video = post_div.find('video', class_='expandedWebm')
            if video and video.has_attr('src'):
                old_src = video['src']
                video['src'] = f"{prefix}shared_images/{local_filename}"
                fixed_videos += 1
                print(f"  Fixed video post {post_no}: {old_src[:50]}... -> {prefix}shared_images/{local_filename}")

    # Write back
    with open(html_file, 'w') as f:
        f.write(soup.prettify())

    print(f"\nFixed {fixed_videos} video(s) in {html_file}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_thread_videos_comprehensive.py <thread_id> [--download-all]")
        print("  thread_id: Fix specific thread")
        print("  --download-all: Fix all threads")
        sys.exit(1)

    download_all = '--download-all' in sys.argv

    if download_all:
        # Fix all threads
        html_dir = Path("cache/imageboard/html")
        threads_dir = Path("cache/imageboard/threads")

        for html_file in html_dir.glob("b_*.html"):
            thread_id = html_file.stem.replace('b_', '')
            thread_json = threads_dir / "b" / thread_id / "thread.json"

            if thread_json.exists():
                print(f"\nProcessing thread {thread_id}...")
                fix_thread_html(html_file, thread_json)
    else:
        # Fix specific thread
        thread_id = sys.argv[1]
        html_file = Path(f"cache/imageboard/html/b_{thread_id}.html")
        thread_json = Path(f"cache/imageboard/threads/b/{thread_id}/thread.json")

        if not html_file.exists():
            print(f"HTML file not found: {html_file}")
            sys.exit(1)

        if not thread_json.exists():
            print(f"Thread JSON not found: {thread_json}")
            sys.exit(1)

        fix_thread_html(html_file, thread_json)