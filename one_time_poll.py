#!/usr/bin/env python3
"""
One-time imageboard poll for daily collection.
Fatches catalog, matches keywords, collects data.
"""

import requests
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Keywords with cosplay
keywords = ["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss", "actresses", "tiny", "cosplay"]

print("=" * 70)
print("ONE-TIME IMAGEBOARD POLL")
print("=" * 70)
print(f"Board: /b/")
print(f"Keywords: {keywords}")
print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print()

# Fetch catalog
print("Fetching /b/ catalog...")
resp = requests.get("https://a.4cdn.org/b/catalog.json", timeout=30)
catalog = resp.json()
print(f"Found {len(catalog)} pages in catalog")
print()

# Find matching threads
matched_threads = []
for page in catalog:
    for thread in page.get("threads", []):
        sub = str(thread.get("sub", "")).lower()
        com = str(thread.get("com", "")).lower()
        text = f"{sub} {com}"
        if any(k.lower() in text for k in keywords):
            matched_threads.append(thread)

print(f"Found {len(matched_threads)} threads matching keywords")
print()

# Save results
output = {
    "timestamp": datetime.utcnow().isoformat(),
    "board": "b",
    "keywords": keywords,
    "threads_found": len(matched_threads),
    "threads": []
}

for t in matched_threads:
    output["threads"].append({
        "thread_id": t.get("no"),
        "subject": t.get("sub", "No subject"),
        "replies": t.get("replies", 0),
        "images": t.get("images", 0),
        "last_modified": t.get("last_modified", 0)
    })

# Save to file
output_file = Path(__file__).parent / "cache" / "imageboard" / f"poll_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Saved results to: {output_file}")
print()

# Show top threads
print("Top matching threads:")
print()
for i, t in enumerate(output["threads"][:10], 1):
    subject = t['subject'][:60]
    print(f"  {i}. [{t['thread_id']}] {subject}... ({t['images']} images)")

print()
print("=" * 70)
print(f"DONE: Collected {len(output['threads'])} matching threads")
print("=" * 70)
