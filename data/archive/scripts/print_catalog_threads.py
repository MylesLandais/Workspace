#!/usr/bin/env python3
"""Print threads touched by catalog poll."""

import requests
import json

KEYWORDS = ["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss", "actresses", "tiny", "cosplay"]

def main():
    url = "https://a.4cdn.org/b/catalog.json"

    print("=" * 80)
    print(f"CATALOG POLL - /b/ - Threads matching keywords: {KEYWORDS}")
    print("=" * 80)

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
                matched_threads.append({
                    "thread_id": thread["no"],
                    "subject": thread.get("sub", "[No subject]")[:60],
                    "replies": thread.get("replies", 0),
                    "images": thread.get("images", 0),
                    "last_modified": thread.get("last_modified", 0)
                })

    # Sort by last modified
    matched_threads.sort(key=lambda x: x["last_modified"], reverse=True)

    # Print all threads
    for i, t in enumerate(matched_threads, 1):
        print(f"{i}. [{t['thread_id']}] {t['subject']}")
        print(f"   Replies: {t['replies']} | Images: {t['images']}")
        print()

    print("=" * 80)
    print(f"Total threads: {len(matched_threads)}")
    print("=" * 80)

if __name__ == "__main__":
    main()