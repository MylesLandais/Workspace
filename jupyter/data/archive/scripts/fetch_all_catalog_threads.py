#!/usr/bin/env python3
"""Fetch all matching threads from catalog and queue them."""

import os
import json
import redis
import requests

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
KEYWORDS = ["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss", "actresses", "tiny", "cosplay"]

def fetch_and_queue_all():
    """Fetch catalog and queue all matching threads."""
    url = "https://a.4cdn.org/b/catalog.json"

    print("=" * 80)
    print(f"FETCHING ALL MATCHING THREADS FROM /b/")
    print("=" * 80)
    print(f"Keywords: {KEYWORDS}")
    print()

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        catalog = resp.json()
    except Exception as e:
        print(f"ERROR: {e}")
        return

    matched_threads = []

    for page in catalog:
        for thread in page.get("threads", []):
            sub = str(thread.get("sub", "")).lower()
            com = str(thread.get("com", "")).lower()
            text = f"{sub} {com}"

            if any(k.lower() in text for k in KEYWORDS):
                sub = thread.get("sub", "")
                if not sub:
                    com = thread.get("com", "")
                    preview = com[:100].replace('\n', ' ') if len(com) > 100 else com
                    sub = f"[{preview}]"

                matched_threads.append({
                    "board": "b",
                    "thread_id": thread["no"],
                    "subject": sub[:100],
                    "replies": thread.get("replies", 0),
                    "last_modified": thread.get("last_modified", 0)
                })

    print(f"Found {len(matched_threads)} matching threads in catalog")
    print()

    # Queue all threads
    r = redis.from_url(REDIS_URL)
    queued_count = 0

    for thread in matched_threads:
        job_data = json.dumps(thread)
        r.rpush('queue:monitors', job_data)
        queued_count += 1
        print(f"[{queued_count}/{len(matched_threads)}] Queued: [{thread['thread_id']}] {thread['subject'][:50]}")

    print()
    print("=" * 80)
    print(f"SUCCESS: Queued {queued_count} threads")
    print("=" * 80)

if __name__ == "__main__":
    fetch_and_queue_all()