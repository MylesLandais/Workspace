#!/usr/bin/env python3
import requests
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

# Keywords including cosplay
keywords = ["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss", "actresses", "tiny", "cosplay"]
keywords_lower = [k.lower() for k in keywords]

print(f"Searching /b/ catalog for threads matching: {keywords}")
print()

# Fetch catalog
resp = requests.get("https://a.4cdn.org/b/catalog.json", timeout=30)
catalog = resp.json()

# Find matching threads
matched_threads = []
for page in catalog:
    for thread in page.get("threads", []):
        sub = str(thread.get("sub", "")).lower()
        com = str(thread.get("com", "")).lower()
        text = f"{sub} {com}"
        if any(k.lower() in text for k in keywords):
            matched_threads.append(thread)

print(f"Found {len(matched_threads)} threads matching keywords:")
print()
for t in matched_threads[:10]:
    print(f"  - {t.get('no')}: {t.get('sub', 'No subject')[:60]}...")
