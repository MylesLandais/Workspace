#!/usr/bin/env python3
"""Imageboard monitor worker - processes queued thread monitors with de-duplication and moderation."""
import os
import sys
import time
import json
import requests
import redis
import hashlib
import re
from bs4 import BeautifulSoup
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
CACHE_DIR = os.environ.get('CACHE_DIR', '/home/warby/Workspace/jupyter/cache/imageboard')
IMAGES_DIR = os.path.join(CACHE_DIR, 'shared_images')
THREADS_DIR = os.path.join(CACHE_DIR, 'threads')
HTML_DIR = os.path.join(CACHE_DIR, 'html')

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(THREADS_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

r = redis.from_url(REDIS_URL)

# OTEL Metrics (optional - fails gracefully if not installed)
try:
    import otel_monitor
    jobs_processed_total = otel_monitor.jobs_processed_total
    jobs_success_total = otel_monitor.jobs_success_total
    jobs_failed_total = otel_monitor.jobs_failed_total
    queue_depth = otel_monitor.queue_depth
    job_processing_duration_seconds = otel_monitor.job_processing_duration_seconds
    thread_posts_collected = otel_monitor.thread_posts_collected
    thread_images_downloaded = otel_monitor.thread_images_downloaded
    thread_duplicates_found = otel_monitor.thread_duplicates_found
    thread_moderated_posts = otel_monitor.thread_moderated_posts
    thread_last_fetch_timestamp = otel_monitor.thread_last_fetch_timestamp
    OTEL_ENABLED = True
except (ImportError, AttributeError):
    OTEL_ENABLED = False
    jobs_processed_total = None
    jobs_success_total = None
    jobs_failed_total = None
    queue_depth = None
    job_processing_duration_seconds = None
    thread_posts_collected = None
    thread_images_downloaded = None
    thread_duplicates_found = None
    thread_moderated_posts = None
    thread_last_fetch_timestamp = None

def fetch_thread(board, thread_id):
    """Fetch thread posts from 4cdn API."""
    url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            print(f"Thread {thread_id} archived or deleted.")
            return None
    except Exception as e:
        print(f"Error fetching thread {thread_id}: {e}")
    return None

def fetch_html(board, thread_id):
    """Fetch thread HTML for offline viewing."""
    url = f"https://boards.4chan.org/{board}/thread/{thread_id}"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"Error fetching HTML for {thread_id}: {e}")
    return None

def rewrite_html_for_offline(html_text, thread_data, board, thread_id, depth=2):
    """Rewrite HTML to use local images and fix styles."""
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # 1. Remove base tag if present (it breaks local relative paths for images)
    base_tag = soup.find('base')
    if base_tag:
        base_tag.decompose()
 
    # 2. Fix all relative links/scripts to be absolute to 4chan
    for tag in soup.find_all(['link', 'script', 'a', 'img', 'form']):
        for attr in ['href', 'src', 'action']:
            if tag.has_attr(attr):
                val = tag[attr]
                if val.startswith('//'):
                    tag[attr] = 'https:' + val
                elif val.startswith('/') and not val.startswith('//'):
                    tag[attr] = 'https://boards.4chan.org' + val
                elif not val.startswith('http') and not val.startswith('#') and not val.startswith('javascript') and not val.startswith('../'):
                    tag[attr] = f"https://boards.4chan.org/{board}/" + val
    
    # 3. Map of post_no to local_image
    image_map = {p['no']: p['local_image'] for p in thread_data.get('posts', []) if 'local_image' in p}
    
    # 4. Find posts and update image src/href
    # html/ (depth 1) -> ../shared_images/
    # threads/board/id/ (depth 3) -> ../../../shared_images/
    prefix = "../" * depth
    
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
                # If src is already a CDN URL, don't change it
                if not old_src.startswith('https://i.4cdn.org/'):
                    # Try to use local image if available
                    video['src'] = f"{prefix}shared_images/{local_filename}"
                    print(f"Updated video src for post {post_no}: {old_src[:50]} -> {video['src']}")
                else:
                    video['src'] = f"{prefix}shared_images/{local_filename}"
    
    return soup.prettify()

def get_file_sha256(file_path):
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_and_dedup_image(post, board):
    """Download an image/video and use SHA256 de-duplication with retry logic."""
    if 'tim' not in post:
        return None, False
    
    filename = f"{post['tim']}{post.get('ext', '.jpg')}"
    url = f"https://i.4cdn.org/{board}/{filename}"
    
    # Temporary download path
    temp_path = os.path.join(CACHE_DIR, f"temp_{filename}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=60, stream=True)
            if resp.status_code == 200:
                with open(temp_path, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                
                # Compute hash
                sha256 = get_file_sha256(temp_path)
                final_filename = f"{sha256}{post.get('ext', '.jpg')}"
                final_path = os.path.join(IMAGES_DIR, final_filename)
                
                if os.path.exists(final_path):
                    # # Duplicate found, remove temp file
                    os.remove(temp_path)
                    return final_filename, True # filename, is_duplicate
                else:
                    # New image, move to final path
                    os.rename(temp_path, final_path)
                    return final_filename, False
            elif resp.status_code == 429:
                # Rate limited, wait and retry
                wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                print(f"Rate limited (HTTP 429), waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"  HTTP {resp.status_code}, download failed")
                break
        except Exception as e:
            print(f"  Error: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                break
    
    # If all retries failed, return CDN URL so HTML can still work
    print(f"  Download failed after {max_retries} retries, using CDN URL: {url}")
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return url, False  # Return CDN URL instead of local path

def moderate_post(post):
    """Identify if a post is low-quality/shitpost."""
    com = str(post.get('com', '')).lower()
    
    # 1. Hex pattern (bot noise)
    if re.search(r'[0-9a-f]{16,}', com):
        return True, "bot:hex_pattern"
    
    # 2. Repetitive noise
    if "nut after nut" in com:
        return True, "low_quality:repetitive"
    
    # 3. Known bot triggers
    if any(kw in com for kw in ["logfag", "shiteater"]):
        return True, "bot:keyword"
        
    return False, None

def follow_threads(posts, board):
    """Identify links to new/next threads and queue them."""
    for post in posts:
        com = str(post.get('com', '')).lower()
        # Look for "new thread" or "next thread" followed by a link or number
        # Also support looser patterns like "New" with a link nearby
        # Regex 1: "new/next thread" -> link
        match1 = re.search(r'(?:new|next|previous)\s*thread.*?(?:>>|&gt;&gt;)(\d{7,})', com, re.IGNORECASE | re.DOTALL)
        
        # Regex 2: Link -> "new/next thread"
        match2 = re.search(r'(?:>>|&gt;&gt;)(\d{7,}).*?(?:new|next|previous)\s*thread', com, re.IGNORECASE | re.DOTALL)
        
        # Regex 3: Just "New" or "Next" with a link (looser)
        match3 = re.search(r'(?:^|\s)(?:new|next)(?:\s|$|!|\.).*?(?:>>|&gt;&gt;)(\d{7,})', com, re.IGNORECASE | re.DOTALL)
        
        new_thread_id = None
        if match1:
            new_thread_id = match1.group(1)
        elif match2:
            new_thread_id = match2.group(1)
        elif match3:
            new_thread_id = match3.group(1)
        
        if new_thread_id:
            print(f"Found link to new thread: {new_thread_id}")
            job_data = json.dumps({
                "board": board,
                "thread_id": int(new_thread_id),
                "subject": "Follow-up Thread"
            })
            r.rpush('queue:monitors', job_data)

def process_monitor_job(job_data):
    """Process a monitoring job."""
    board = job_data['board']
    thread_id = job_data['thread_id']
    subject = job_data.get('subject', '')
    
    # Use body preview if subject is empty or "[body]"
    if not subject or subject.startswith('[') and subject.endswith(']'):
        if subject.startswith('[') and subject.endswith(']'):
            # Extract body from brackets format
            truncated_subject = subject[1:-1][:50]
        else:
            truncated_subject = ""
    
    print(f"\n[{board}/{thread_id}] Monitoring: {subject[:40]}")
    
    if OTEL_ENABLED and jobs_processed_total:
        jobs_processed_total.inc(1)
    
    try:
        if OTEL_ENABLED and job_processing_duration_seconds:
            with job_processing_duration_seconds.time():
                thread_data = fetch_thread(board, thread_id)
                if not thread_data:
                    return False
                
                posts = thread_data.get('posts', [])
                thread_dir = os.path.join(THREADS_DIR, board, str(thread_id))
                os.makedirs(thread_dir, exist_ok=True)
                
                # Process posts
                moderated_count = 0
                image_count = 0
                duplicate_count = 0
                
                for post in posts:
                    # Moderation
                    is_bad, reason = moderate_post(post)
                    if is_bad:
                        post['moderated'] = True
                        post['moderation_reason'] = reason
                        moderated_count += 1
                    
                    # Images/videos (check for tim field which includes all media)
                    if 'tim' in post:
                        img_file, is_dup = download_and_dedup_image(post, board)
                        if img_file:
                            # img_file can be local filename or CDN URL (if download failed)
                            # Store either way so HTML can use it
                            post['local_image'] = img_file
                            image_count += 1
                            if is_dup:
                                duplicate_count += 1
                
                # Thread following
                follow_threads(posts, board)
                
                # Save data for offline exploration
                data_path = os.path.join(thread_dir, 'thread.json')
                with open(data_path, 'w') as f:
                    json.dump(thread_data, f, indent=2)
                
                # Save HTML for offline viewing
                html_text = fetch_html(board, thread_id)
                if html_text:
                    # Save version for HTML_DIR (depth 1: html/b_{thread_id}.html)
                    html_main = rewrite_html_for_offline(html_text, thread_data, board, thread_id, depth=1)
                    html_path = os.path.join(HTML_DIR, f"{board}_{thread_id}.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_main)
                        
                    # Save version for thread dir (depth 3: threads/board/id/index.html)
                    html_thread = rewrite_html_for_offline(html_text, thread_data, board, thread_id, depth=3)
                    with open(os.path.join(thread_dir, 'index.html'), 'w', encoding='utf-8') as f:
                        f.write(html_thread)
                
                print(f"  Posts: {len(posts)}, Moderated: {moderated_count}, Images: {image_count}, Dups: {duplicate_count}")
        else:
            thread_data = fetch_thread(board, thread_id)
            if not thread_data:
                return False
                
            posts = thread_data.get('posts', [])
            thread_dir = os.path.join(THREADS_DIR, board, str(thread_id))
            os.makedirs(thread_dir, exist_ok=True)
            
            # Process posts
            moderated_count = 0
            image_count = 0
            duplicate_count = 0
            
            for post in posts:
                # Moderation
                is_bad, reason = moderate_post(post)
                if is_bad:
                    post['moderated'] = True
                    post['moderation_reason'] = reason
                    moderated_count += 1
                    
                    # Images
                if 'tim' in post:
                    img_file, is_dup = download_and_dedup_image(post, board)
                    if img_file:
                        # img_file can be local filename or CDN URL (if download failed)
                        # Store either way so HTML can use it
                        post['local_image'] = img_file
                        image_count += 1
                        if is_dup:
                            duplicate_count += 1
                
                # Thread following
                follow_threads(posts, board)
                
                # Save data for offline exploration
                data_path = os.path.join(thread_dir, 'thread.json')
                with open(data_path, 'w') as f:
                    json.dump(thread_data, f, indent=2)
                
                # Save HTML for offline viewing
                html_text = fetch_html(board, thread_id)
                if html_text:
                    # Save version for HTML_DIR (depth 1: html/b_{thread_id}.html)
                    html_main = rewrite_html_for_offline(html_text, thread_data, board, thread_id, depth=1)
                    html_path = os.path.join(HTML_DIR, f"{board}_{thread_id}.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_main)
                        
                    # Save version for thread dir (depth 3: threads/board/id/index.html)
                    html_thread = rewrite_html_for_offline(html_text, thread_data, board, thread_id, depth=3)
                    with open(os.path.join(thread_dir, 'index.html'), 'w', encoding='utf-8') as f:
                        f.write(html_thread)
                
                print(f"  Posts: {len(posts)}, Moderated: {moderated_count}, Images: {image_count}, Dups: {duplicate_count}")
        
        # Record metrics
        if OTEL_ENABLED:
            if jobs_success_total:
                jobs_success_total.inc(1)
            if thread_posts_collected:
                thread_posts_collected.labels(board=board, thread_id=str(thread_id), subject=truncated_subject).inc(len(posts))
            if thread_images_downloaded:
                thread_images_downloaded.labels(board=board, thread_id=str(thread_id), subject=truncated_subject).inc(image_count)
            if thread_duplicates_found:
                thread_duplicates_found.labels(board=board, thread_id=str(thread_id), subject=truncated_subject).inc(duplicate_count)
            if thread_moderated_posts:
                thread_moderated_posts.labels(board=board, thread_id=str(thread_id), subject=truncated_subject).inc(moderated_count)
            if thread_last_fetch_timestamp:
                thread_last_fetch_timestamp.labels(board=board, thread_id=str(thread_id), subject=truncated_subject).set(time.time())
        
        return True
        
    except Exception as e:
        print(f"Error processing job: {e}")
        if OTEL_ENABLED and jobs_failed_total:
            jobs_failed_total.inc(1)
        return False

def worker():
    """Main worker loop."""
    print("Imageboard Monitor Worker (Enhanced) started")
    print(f"Redis: {REDIS_URL}")
    print(f"Cache: {CACHE_DIR}")
    if OTEL_ENABLED:
        print("OTEL metrics: ENABLED")
    else:
        print("OTEL metrics: DISABLED")
    
    while True:
        try:
            # Update queue depth metric
            if OTEL_ENABLED and queue_depth:
                queue_depth.set(r.llen('queue:monitors'))
            
            job = r.blpop('queue:monitors', timeout=5)
            if job and len(job) >= 2:
                job_raw = job[1]
                try:
                    data = json.loads(job_raw.decode('utf-8'))
                    process_monitor_job(data)
                except Exception as e:
                    print(f"Error processing job: {e}")
                    if OTEL_ENABLED and jobs_failed_total:
                        jobs_failed_total.inc(1)
        except KeyboardInterrupt:
            print("\nWorker stopped")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    worker()
