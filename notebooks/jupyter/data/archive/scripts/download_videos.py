#!/usr/bin/env python3
"""
Download videos from coomer.st using FlareSolverr
"""

import os
import re
import json
import time
import requests

COOMER_URL = "https://coomer.st"
FLARESOLVERR = "http://localhost:8191/v1"
OUTPUT_DIR = "/home/warby/Workspace/jupyter/downloads/videos"

def fetch_with_flaresolverr(url):
    """Fetch URL via FlareSolverr"""
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    }

    response = requests.post(FLARESOLVERR, json=payload, timeout=120)
    result = response.json()

    if result.get("status") == "ok":
        return result.get("solution", {}).get("response", "")
    return None

def get_creator_posts(creator_id):
    """Get all post IDs for a creator"""
    url = f"{COOMER_URL}/onlyfans/user/{creator_id}"
    html = fetch_with_flaresolverr(url)

    if not html:
        print("❌ Failed to fetch creator page")
        return []

    # Extract post IDs from HTML
    post_ids = re.findall(rf'/onlyfans/user/{re.escape(creator_id)}/post/(\d+)', html)
    return list(set(post_ids))

def extract_videos_from_post(html):
    """Extract video download URLs from post HTML"""
    videos = []

    # Method 1: Extract from Downloads section
    download_matches = re.findall(r'href="(https://n\d+\.coomer\.st/data/[^"]+\.mp4\?f=[^"]+)"', html)
    videos.extend(download_matches)

    # Method 2: Extract from Videos section source tags
    source_matches = re.findall(r'<source[^>]+src="(https://n\d+\.coomer\.st/data/[^"]+\.mp4[^"]*)"', html)
    videos.extend(source_matches)

    # Method 3: Direct mp4 links
    direct_matches = re.findall(r'(https://n\d+\.coomer\.st/data/[^"]+\.mp4[^"\s]*)', html)
    videos.extend(direct_matches)

    # Deduplicate
    return list(set(videos))

def download_video(url, output_dir, post_id):
    """Download a video file"""
    filename = url.split('?')[0].split('/')[-1]
    local_path = os.path.join(output_dir, f"{post_id}_{filename}")

    if os.path.exists(local_path):
        size = os.path.getsize(local_path)
        if size > 1024 * 1024:  # 1MB minimum
            print(f"    ✓ {filename} ({size/1024/1024:.1f} MB) - exists")
            return True

    print(f"    ↓ {filename}...", end=" ", flush=True)

    try:
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": COOMER_URL,
        }, timeout=300, stream=True)

        if response.status_code == 200:
            content_length = int(response.headers.get("content-length", 0))

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = content_length / 1024 / 1024 if content_length > 0 else os.path.getsize(local_path) / 1024 / 1024
            print(f"✓ ({size_mb:.1f} MB)")
            return True
        else:
            print(f"✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ {str(e)[:50]}")

    return False

def download_creator_videos(creator_id, max_posts=None):
    """Download all videos for a creator"""
    output_dir = os.path.join(OUTPUT_DIR, creator_id)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n🎯 Finding posts for @{creator_id}...")

    post_ids = get_creator_posts(creator_id)
    print(f"   Found {len(post_ids)} posts")

    if max_posts:
        post_ids = post_ids[:max_posts]

    total_videos = 0
    total_downloaded = 0
    total_failed = 0

    for i, post_id in enumerate(post_ids):
        print(f"\n[{i+1}/{len(post_ids)}] Post {post_id}")

        url = f"{COOMER_URL}/onlyfans/user/{creator_id}/post/{post_id}"
        html = fetch_with_flaresolverr(url)

        if not html:
            print("    ❌ Failed to fetch post")
            total_failed += 1
            continue

        videos = extract_videos_from_post(html)

        if not videos:
            print("    → No videos found")
            continue

        print(f"    → {len(videos)} video(s)")

        for video_url in videos:
            if download_video(video_url, output_dir, post_id):
                total_downloaded += 1
            else:
                total_failed += 1
            total_videos += 1

        time.sleep(0.5)

    print(f"\n✅ Complete!")
    print(f"   Posts: {len(post_ids)}")
    print(f"   Videos found: {total_videos}")
    print(f"   Downloaded: {total_downloaded}")
    print(f"   Failed: {total_failed}")
    print(f"   Output: {output_dir}")

    return {
        "posts": len(post_ids),
        "videos_found": total_videos,
        "downloaded": total_downloaded,
        "failed": total_failed,
        "output_dir": output_dir
    }

if __name__ == "__main__":
    import sys

    creator = sys.argv[1] if len(sys.argv) > 1 else "myla.feet"
    max_posts = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"🚀 Downloading videos from @{creator}")

    result = download_creator_videos(creator, max_posts)

    print(f"\n📁 Videos saved to: {result['output_dir']}")
