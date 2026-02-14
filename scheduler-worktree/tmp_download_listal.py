#!/usr/bin/env python3
"""Download Listal images to cache."""

import hashlib
import requests
from pathlib import Path
from datetime import datetime

LISTAL_IMAGE_URL = "https://ilarge.lisimg.com/image/26229169/740full-maddie-teeuws.jpg"
CACHE_DIR = Path("/home/jovyan/workspaces/cache/listal/images")

def compute_sha256(data):
    return hashlib.sha256(data).hexdigest()

def download_and_cache(url, cache_dir):
    """Download image and save to cache by SHA256."""
    print(f"Downloading: {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    
    data = resp.content
    sha256 = compute_sha256(data)
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{sha256}.jpg"
    
    with open(cache_path, 'wb') as f:
        f.write(data)
    
    print(f"Cached: {cache_path}")
    return cache_path, sha256

if __name__ == "__main__":
    path, sha256 = download_and_cache(LISTAL_IMAGE_URL, CACHE_DIR)
    print(f"\nSaved: {path}")
    print(f"SHA256: {sha256}")
    print(f"Size: {path.stat().st_size / 1024:.1f} KB")
    
    # Update Neo4j with cache path
    from feed.storage.neo4j_connection import get_connection
    neo4j = get_connection()
    
    query = """
    MATCH (li:ListalImage {image_id: "26229169"})
    SET li.image_path = $path,
        li.sha256 = $sha256,
        li.cached_at = datetime()
    """
    neo4j.execute_write(query, {"path": str(path), "sha256": sha256})
    print("Updated Neo4j with cache path")
