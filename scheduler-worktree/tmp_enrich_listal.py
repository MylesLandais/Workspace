#!/usr/bin/env python3
"""Enrich Listal graph by crawling related images and lists."""

import json
import requests
import hashlib
from bs4 import BeautifulSoup
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import re
import time

FLARESOLVER_URL = "http://localhost:8191"
CACHE_DIR = Path("/home/warby/Workspace/jupyter/cache/listal/images")

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

    title = soup.find("title")
    if title:
        result["subject_name"] = title.get_text(strip=True).replace("Picture of ", "").split(" - Listal")[0].strip()

    img = soup.find("meta", property="og:image")
    if img:
        result["image_url"] = img.get("content")

    text = soup.get_text()
    views_match = re.search(r"(\d+)\s+Views", text)
    result["views"] = int(views_match.group(1)) if views_match else 0

    result["voters"] = []
    result["related_images"] = []
    result["curated_lists"] = []

    for link in soup.select('a[href*="/viewimage/"]'):
        href = link.get("href", "")
        match = re.search(r"/viewimage/(\d+)", href)
        if match:
            img_id = match.group(1)
            if img_id not in result["related_images"]:
                result["related_images"].append(img_id)

    for link in soup.select('a[href^="/list/"]'):
        href = link.get("href", "")
        name = link.get_text(strip=True)
        if href and name:
            result["curated_lists"].append({"url": f"https://www.listal.com{href}", "name": name})

    return result

def download_image(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.content
    sha256 = hashlib.sha256(data).hexdigest()
    cache_path = CACHE_DIR / f"{sha256}.jpg"
    if not cache_path.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(data)
    return cache_path, sha256

if __name__ == "__main__":
    from feed.storage.neo4j_connection import get_connection

    neo4j = get_connection()

    # Get all images that need enriching
    print("=== Finding images to enrich ===")
    r = neo4j.execute_read("""
        MATCH (li:ListalImage)
        WHERE li.views IS NULL AND li.image_id IN $ids
        RETURN li.image_id
    """, {"ids": ["11514493", "13864709", "14803899", "14900106", "14963335", 
                  "14984951", "15042731", "15142600", "19303906", "19775587",
                  "22240633", "23211436", "24773685", "24796562", "25214411",
                  "25241651", "26940699", "26957804"]})
    image_ids = [rec["li.image_id"] for rec in r]
    print(f"Found {len(image_ids)} images to crawl")

    # Also get the main image 16806755 which wasn't fully enriched
    main_image_id = "16806755"

    all_images = [main_image_id] + image_ids
    crawled = 0

    for img_id in all_images:
        url = f"https://www.listal.com/viewimage/{img_id}"
        print(f"\nCrawling {img_id}...")

        try:
            html = fetch_via_flaresolver(url)
            data = parse_image_page(html)
            print(f"  Subject: {data.get('subject_name')}")
            print(f"  Views: {data.get('views')}")
            print(f"  Related: {len(data.get('related_images', []))}")
            print(f"  Lists: {len(data.get('curated_lists', []))}")

            # Download image
            if data.get("image_url"):
                path, sha256 = download_image(data["image_url"])
                print(f"  Cached: {path.name} ({path.stat().st_size / 1024:.1f} KB)")

                # Update Neo4j
                neo4j.execute_write("""
                    MERGE (li:ListalImage {image_id: $image_id})
                    ON CREATE SET li.uuid = $uuid, li.normalized_url = $url, 
                        li.source_url = $url, li.discovered_at = datetime(), li.created_at = datetime()
                    SET li.subject_name = $name, li.views = $views, 
                        li.thumbnail_url = $thumb, li.image_path = $path, li.sha256 = $sha256,
                        li.cached_at = datetime(), li.updated_at = datetime()
                """, {
                    "image_id": img_id, "uuid": str(uuid4()), "url": url,
                    "name": data.get("subject_name"), "views": data.get("views"),
                    "thumb": data.get("image_url"), "path": str(path), "sha256": sha256
                })
                print(f"  Updated Neo4j")

            # Store voters
            for voter in data.get("voters", []):
                neo4j.execute_write("""
                    MERGE (lu:ListalUser {username: $username})
                    ON CREATE SET lu.discovered_at = datetime()
                    WITH lu MATCH (li:ListalImage {image_id: $image_id})
                    MERGE (lu)-[:VOTED_FOR]->(li)
                """, {"username": voter, "image_id": img_id})
            if data.get("voters"):
                print(f"  Stored {len(data['voters'])} voters")

            # Store similar images
            for sim_id in data.get("related_images", []):
                neo4j.execute_write("""
                    MATCH (li:ListalImage {image_id: $image_id})
                    MERGE (sim:ListalImage {image_id: $sim_id})
                    ON CREATE SET sim.discovered_at = datetime()
                    MERGE (li)-[:SIMILAR_TO]->(sim)
                """, {"image_id": img_id, "sim_id": sim_id})
            if data.get("related_images"):
                print(f"  Stored {len(data['related_images'])} similar images")

            # Store curated lists
            for lst in data.get("curated_lists", []):
                slug = re.sub(r"[^a-z0-9\s-]", "", lst["name"].lower())
                slug = re.sub(r"[\s-]+", "-", slug)
                neo4j.execute_write("""
                    MERGE (ll:ListalList {slug: $slug})
                    ON CREATE SET ll.name = $name, ll.url = $url, ll.discovered_at = datetime()
                    WITH ll MATCH (li:ListalImage {image_id: $image_id})
                    MERGE (li)-[:IN_LIST]->(ll)
                """, {"slug": slug, "name": lst["name"], "url": lst["url"], "image_id": img_id})
            if data.get("curated_lists"):
                print(f"  Stored {len(data['curated_lists'])} curated lists")

            crawled += 1
            time.sleep(1)  # Rate limit

        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n=== Done: crawled {crawled}/{len(all_images)} images ===")

    # Summary
    print("\n=== Graph Summary ===")
    r = neo4j.execute_read("""
        MATCH (li:ListalImage) 
        WHERE li.views IS NOT NULL
        RETURN count(li) as total, sum(li.views) as total_views
    """)
    print(f"Images with full data: {r[0]['total']}")
    print(f"Total views: {r[0]['total_views']}")

    r = neo4j.execute_read("MATCH (l:ListalList) RETURN count(l) as count")
    print(f"Curated lists: {r[0]['count']}")

    r = neo4j.execute_read("MATCH (u:ListalUser) RETURN count(u) as count")
    print(f"Users: {r[0]['count']}")
