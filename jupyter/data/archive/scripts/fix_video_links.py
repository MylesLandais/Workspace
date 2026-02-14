#!/usr/bin/env python3
"""Fix video links in cached HTML files."""

import json
from bs4 import BeautifulSoup
from pathlib import Path

THREADS_DIR = Path("cache/imageboard/threads")
HTML_DIR = Path("cache/imageboard/html")

def fix_thread_html(thread_id):
    """Fix video tags in a specific thread's HTML file."""
    # Read thread JSON
    thread_json = THREADS_DIR / "b" / thread_id / "thread.json"
    if not thread_json.exists():
        print(f"Thread JSON not found: {thread_json}")
        return False
    
    with open(thread_json) as f:
        thread_data = json.load(f)
    
    # Read HTML file
    html_file = HTML_DIR / f"b_{thread_id}.html"
    if not html_file.exists():
        print(f"HTML file not found: {html_file}")
        return False
    
    with open(html_file) as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Build image map
    image_map = {p['no']: p['local_image'] for p in thread_data.get('posts', []) if 'local_image' in p}
    
    # Fix videos
    fixed_count = 0
    for post_no, local_filename in image_map.items():
        post_div = soup.find(id=f"pc{post_no}")
        if post_div:
            video = post_div.find('video', class_='expandedWebm')
            if video and video.has_attr('src'):
                old_src = video['src']
                video['src'] = f"../shared_images/{local_filename}"
                fixed_count += 1
                print(f"  Fixed video post {post_no}")
    
    if fixed_count > 0:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"Fixed {fixed_count} video(s) in {html_file}")
        return True
    else:
        print(f"No videos to fix in {html_file}")
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 fix_video_links.py <thread_id>")
        sys.exit(1)
    
    thread_id = sys.argv[1]
    fix_thread_html(thread_id)
