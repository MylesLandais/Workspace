#!/usr/bin/env python3
"""Regenerate HTML for a specific thread to fix video links."""

import json
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def fix_video_links(html_file: Path, thread_json_file: Path):
    """Fix video tags to point to local cached files."""
    # Read thread JSON
    with open(thread_json_file) as f:
        thread_data = json.load(f)

    # Create image map: post_no -> local_image
    image_map = {p['no']: p['local_image'] for p in thread_data.get('posts', []) if 'local_image' in p}

    # Read HTML
    with open(html_file) as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Determine prefix based on file location
    # If in cache/imageboard/html/ -> ../shared_images/
    # If in cache/imageboard/threads/b/{id}/ -> ../../../shared_images/
    if 'html/' in str(html_file):
        prefix = "../"
    else:
        prefix = "../../../"

    # Fix video tags
    fixed_count = 0
    for post_no, local_filename in image_map.items():
        post_div = soup.find(id=f"pc{post_no}")
        if post_div:
            video = post_div.find('video', class_='expandedWebm')
            if video and video.has_attr('src'):
                old_src = video['src']
                video['src'] = f"{prefix}shared_images/{local_filename}"
                fixed_count += 1
                print(f"Fixed video for post {post_no}: {old_src} -> {prefix}shared_images/{local_filename}")

    # Write back
    with open(html_file, 'w') as f:
        f.write(soup.prettify())

    print(f"\nFixed {fixed_count} video links in {html_file}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix_thread_video_links.py <thread_id>")
        sys.exit(1)

    thread_id = sys.argv[1]
    html_file = Path(f"cache/imageboard/html/b_{thread_id}.html")
    thread_json_file = Path(f"cache/imageboard/threads/b/{thread_id}/thread.json")

    if not html_file.exists():
        print(f"HTML file not found: {html_file}")
        sys.exit(1)

    if not thread_json_file.exists():
        print(f"Thread JSON file not found: {thread_json_file}")
        sys.exit(1)

    fix_video_links(html_file, thread_json_file)