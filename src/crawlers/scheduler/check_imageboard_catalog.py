#!/usr/bin/env python3
"""Imageboard catalog checker using 4cdn API."""
import requests, json

# Fetch catalog from 4cdn (no Cloudflare)
resp = requests.get("https://a.4cdn.org/b/catalog.json", timeout=30)
data = resp.json()

# Get all threads from page 1
page1 = data[0]
threads = page1["threads"]

keywords = ["feet", "irl", "girl", "celeb", "jj", "shota", "insta", "tiktok", "vsco", "cel", "panties", "gooning", "goon", "zoomers", "ecdw", "cosplay"]
matched = []

for t in threads:
    sub = (t.get("sub", "") or "").lower()
    com = (t.get("com", "") or "").lower()
    text = sub + " " + com

    if any(k in text for k in keywords):
        matched.append(t)

print(f"\n{'='*60}")
print("IMAGEBOARD CATALOG CHECK - /b/ Board (4cdn API)")
print(f"{'='*60}")
print(f"Total threads on page 1: {len(threads)}")
print(f"Matched keywords: {keywords}")
print(f"Matched threads: {len(matched)}")

# Check monitored threads
monitored = [944305066, 944330306, 944334107, 944334460, 944335160, 944339094,
             944341070, 944343857, 944345092, 944346714, 944347077, 944347174,
             944347178, 944348635, 944348736, 944350251]

already_monitoring = [t for t in matched if t.get("no") in monitored]
new_threads = [t for t in matched if t.get("no") not in monitored]

print(f"\nAlready monitoring: {len(already_monitoring)}")
print(f"NEW threads to monitor: {len(new_threads)}")

if new_threads:
    print(f"\n{'='*60}")
    print("NEW THREADS:")
    print(f"{'='*60}")
    for t in new_threads:
        no = t.get("no", "?")
        sub = (t.get("sub", "") or "No subject")[:50]
        replies = t.get("replies", 0)
        print(f"  [{no}] {sub}")
        print(f"      Replies: {replies} | URL: https://boards.4chan.org/b/thread/{no}")

# High activity threads
high_activity = [t for t in matched if t.get("replies", 0) > 100]
if high_activity:
    print(f"\n{'='*60}")
    print("HIGH ACTIVITY THREADS (>100 replies):")
    print(f"{'='*60}")
    for t in sorted(high_activity, key=lambda x: x.get("replies", 0), reverse=True)[:5]:
        no = t.get("no", "?")
        sub = (t.get("sub", "") or "No subject")[:50]
        replies = t.get("replies", 0)
        print(f"  [{no}] {sub} ({replies} replies)")
