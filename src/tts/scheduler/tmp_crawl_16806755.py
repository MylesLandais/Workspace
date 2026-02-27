#!/usr/bin/env python3
"""Crawl Listal image 16806755 (Maddie Teeuws)."""

import json
import hashlib
import requests
from bs4 import BeautifulSoup
from uuid import uuid4
from datetime import datetime
from pathlib import Path

FLARESOLVER_URL = "http://localhost:8191"
IMAGE_ID = "16806755"
IMAGE_URL = f"https://www.listal.com/viewimage/{IMAGE_ID}"

def fetch_via_flaresolver(url):
    resp = requests.post(
        f"{FLARESOLVER_URL}/v1",
        json={"cmd": "request.get", "url": url, "maxTimeout": 60000},
        timeout=120
    )
    data = resp.json()
    if data.get("status") != "ok":
        raise Exception(f"FlareSolverr error: {data.get('message')}")
    return data["solution"]["response"]

def parse_image_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = {}

    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        title = title.replace('Picture of ', '').split(' - Listal')[0].strip()
        result['subject_name'] = title

    img = soup.find('meta', property='og:image')
    if img:
        result['image_url'] = img.get('content')

    text = soup.get_text()
    views_match = re.search(r'(\d+)\s+Views', text)
    result['views'] = int(views_match.group(1)) if views_match else 0

    result['voters'] = []
    voter_links = soup.select('a[href*=".listal.com"]')
    for link in voter_links[:15]:
        href = link.get('href', '')
        if href and href.startswith('/') and len(href) > 1:
            username = href.strip('/').split('.')[0]
            if username and username not in result['voters'] and len(username) < 30:
                result['voters'].append(username)

    result['related_images'] = []
    related_links = soup.select('a[href*="/viewimage/"]')
    for link in related_links[:20]:
        href = link.get('href', '')
        match = re.search(r'/viewimage/(\d+)', href)
        if match:
            img_id = match.group(1)
            if img_id not in result['related_images']:
                result['related_images'].append(img_id)

    result['curated_lists'] = []
    list_links = soup.select('a[href^="/list/"]')
    for link in list_links[:10]:
        href = link.get('href', '')
        name = link.get_text(strip=True)
        if href and name and len(name) < 100:
            result['curated_lists'].append({"url": f"https://www.listal.com{href}", "name": name})

    date_match = re.search(r'(\d+)\s+(years?|months?|days?)\s+ago', text)
    result['added_ago'] = date_match.group(0) if date_match else "unknown"

    return result

def download_image(url, cache_dir):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.content
    sha256 = hashlib.sha256(data).hexdigest()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{sha256}.jpg"
    with open(cache_path, 'wb') as f:
        f.write(data)
    return cache_path, sha256

if __name__ == "__main__":
    import re
    from feed.storage.neo4j_connection import get_connection

    print(f"=== Crawling Listal {IMAGE_ID} ===")

    print("Fetching page...")
    html = fetch_via_flaresolver(IMAGE_URL)

    print("Parsing...")
    data = parse_image_page(html)
    print(f"  Subject: {data['subject_name']}")
    print(f"  Views: {data['views']}")
    print(f"  Voters: {len(data['voters'])}")
    print(f"  Related images: {len(data['related_images'])}")
    print(f"  Curated lists: {len(data['curated_lists'])}")

    print("Downloading image...")
    cache_dir = Path("/home/warby/Workspace/jupyter/cache/listal/images")
    image_path, sha256 = download_image(data['image_url'], cache_dir)
    print(f"  Cached: {image_path} ({image_path.stat().st_size / 1024:.1f} KB)")

    print("Storing to Neo4j...")
    neo4j = get_connection()
    subject_name = data['subject_name']
    slug = re.sub(r'[^a-z0-9-]', '', subject_name.lower().replace(' ', '-'))

    # Store image
    neo4j.execute_write("""
        MERGE (li:ListalImage {image_id: $image_id})
        ON CREATE SET li.uuid = $uuid, li.normalized_url = $url, li.source_url = $url,
            li.thumbnail_url = $thumb, li.views = $views, li.vote_count = $votes,
            li.subject_name = $name, li.image_path = $path, li.sha256 = $sha256,
            li.cached_at = datetime(), li.discovered_at = datetime(), li.created_at = datetime()
        ON MATCH SET li.views = $views, li.updated_at = datetime()
    """, {
        "image_id": IMAGE_ID, "uuid": str(uuid4()), "url": IMAGE_URL,
        "thumb": data['image_url'], "views": data['views'], "votes": len(data['voters']),
        "name": subject_name, "path": str(image_path), "sha256": sha256
    })
    print(f"  Stored ListalImage: {IMAGE_ID}")

    # Store voters
    for voter in data['voters']:
        neo4j.execute_write("""
            MERGE (lu:ListalUser {username: $username})
            ON CREATE SET lu.discovered_at = datetime()
            WITH lu MATCH (li:ListalImage {image_id: $image_id})
            MERGE (lu)-[:VOTED_FOR]->(li)
        """, {"username": voter, "image_id": IMAGE_ID})
    print(f"  Stored {len(data['voters'])} voters")

    # Store related images
    for rid in data['related_images']:
        neo4j.execute_write("""
            MATCH (li:ListalImage {image_id: $image_id})
            MERGE (lir:ListalImage {image_id: $rid})
            ON CREATE SET lir.discovered_at = datetime()
            MERGE (li)-[:SIMILAR_TO]->(lir)
        """, {"image_id": IMAGE_ID, "rid": rid})
    print(f"  Stored {len(data['related_images'])} related images")

    # Store curated lists
    for lst in data['curated_lists']:
        slug_list = re.sub(r'[^a-z0-9\s-]', '', lst['name'].lower())
        slug_list = re.sub(r'[\s-]+', '-', slug_list)
        neo4j.execute_write("""
            MERGE (ll:ListalList {slug: $slug})
            ON CREATE SET ll.name = $name, ll.url = $url, ll.discovered_at = datetime()
            WITH ll MATCH (li:ListalImage {image_id: $image_id})
            MERGE (li)-[:IN_LIST]->(ll)
        """, {"slug": slug_list, "name": lst['name'], "url": lst['url'], "image_id": IMAGE_ID})
    print(f"  Stored {len(data['curated_lists'])} curated lists")

    # Link to Creator/ListalProfile
    neo4j.execute_write("""
        MERGE (c:Creator {slug: $slug})
        ON CREATE SET c.uuid = $uuid, c.name = $name, c.created_at = datetime()
        WITH c
        MERGE (lp:ListalProfile {slug: $slug})
        ON CREATE SET lp.name = $name, lp.url = $url, lp.discovered_at = datetime()
        MERGE (c)-[:LISTAL_PROFILE]->(lp)
        MERGE (lp)-[:SUBJECT_OF]->(c)
    """, {"slug": slug, "uuid": str(uuid4()), "name": subject_name, "url": f"https://www.listal.com/{slug}"})

    # Link image to profile
    neo4j.execute_write("""
        MATCH (lp:ListalProfile {slug: $slug})
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (lp)-[:HAS_IMAGE]->(li)
    """, {"slug": slug, "image_id": IMAGE_ID})

    print(f"\n=== Done ===")
    print(f"Image: {IMAGE_ID}")
    print(f"Subject: {subject_name}")
    print(f"Cache: {image_path}")
    print(f"SHA256: {sha256}")
