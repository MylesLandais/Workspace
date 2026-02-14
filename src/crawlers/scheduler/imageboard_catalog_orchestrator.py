#!/usr/bin/env python3
"""Imageboard catalog orchestrator - polls catalog and queues threads for monitoring."""
import os
import sys
import time
import json
import redis
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
BOARD = os.environ.get('IMAGEBOARD_BOARD', 'b')
KEYWORDS = ["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss", "actresses", "tiny", "cosplay"]
SKIP_BOARDS = []  # Empty - we want to monitor /ss/ threads
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', 1800)) # 30 minutes default

# OTEL Metrics (optional - fails gracefully if not installed)
try:
    import otel_monitor
    catalog_polls_total = otel_monitor.catalog_polls_total
    catalog_polls_success = otel_monitor.catalog_polls_success
    catalog_polls_failed = otel_monitor.catalog_polls_failed
    threads_discovered_total = otel_monitor.threads_discovered_total
    threads_queued_total = otel_monitor.threads_queued_total
    catalog_fetch_duration_seconds = otel_monitor.catalog_fetch_duration_seconds
    OTEL_ENABLED = True
except (ImportError, AttributeError):
    OTEL_ENABLED = False
    catalog_polls_total = None
    catalog_polls_success = None
    catalog_polls_failed = None
    threads_discovered_total = None
    threads_queued_total = None
    catalog_fetch_duration_seconds = None

def poll_catalog():
    """Fetch catalog and find matching threads."""
    url = f"https://a.4cdn.org/{BOARD}/catalog.json"
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Polling /{BOARD}/ catalog...")
    
    start_time = time.time()
    
    try:
        if OTEL_ENABLED and catalog_polls_total:
            catalog_polls_total.inc(1)
        
        if OTEL_ENABLED and catalog_fetch_duration_seconds:
            with catalog_fetch_duration_seconds.time():
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                catalog = resp.json()
        else:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            catalog = resp.json()
        
        if OTEL_ENABLED and catalog_polls_success:
            catalog_polls_success.inc(1)
            
    except Exception as e:
        print(f"Error fetching catalog: {e}")
        if OTEL_ENABLED and catalog_polls_failed:
            catalog_polls_failed.inc(1)
        return []

    matched_threads = []
    for page in catalog:
        for thread in page.get("threads", []):
            # Skip threads from SKIP_BOARDS
            if BOARD in SKIP_BOARDS:
                logger.warning(f"Skipping board {BOARD} - in skip list")
                continue
            
            sub = str(thread.get("sub", "")).lower()
            com = str(thread.get("com", "")).lower()
            text = f"{sub} {com}"
            
            if any(k.lower() in text for k in KEYWORDS):
                # Use subject if available, otherwise use body preview
                sub = thread.get("sub", "")
                if not sub:
                    com = thread.get("com", "")
                    # Get first 100 chars of body for preview
                    preview = com[:100].replace('\n', ' ') if len(com) > 100 else com
                    sub = f"[{preview}]"
                
                matched_threads.append({
                    "board": BOARD,
                    "thread_id": thread["no"],
                    "subject": sub[:100],
                    "replies": thread.get("replies", 0),
                    "last_modified": thread.get("last_modified", 0)
                })
    
    if OTEL_ENABLED:
        fetch_time = time.time() - start_time
        if threads_discovered_total:
            threads_discovered_total.inc(len(matched_threads))
        print(f"Catalog fetch completed in {fetch_time:.2f}s")
    
    return matched_threads

def queue_threads(threads):
    """Push threads to Redis queue."""
    if not threads:
        return
    
    r = redis.from_url(REDIS_URL)
    queued_count = 0
    
    for thread in threads:
        job_data = json.dumps(thread)
        # Use a set to avoid duplicate active monitors if possible, 
        # but for now just push to queue. The worker should handle dedup.
        r.rpush('queue:monitors', job_data)
        queued_count += 1
        
    print(f"Queued {queued_count} threads for monitoring.")
    
    if OTEL_ENABLED and threads_queued_total:
        threads_queued_total.inc(queued_count)

def main():
    print(f"Imageboard Catalog Orchestrator started for /{BOARD}/")
    print(f"Keywords: {KEYWORDS}")
    
    while True:
        threads = poll_catalog()
        print(f"Found {len(threads)} matching threads.")
        queue_threads(threads)
        
        print(f"Sleeping for {POLL_INTERVAL} seconds...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
