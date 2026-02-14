#!/usr/bin/env python3
import json, hashlib, requests, re
from bs4 import BeautifulSoup
from uuid import uuid4
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path("/home/jovyan/workspaces/cache/listal/images")

def parse_image_page(html):
    soup = BeautifulSoup(html, "html.parser")
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

from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()

image_ids = [
    "11514493", "13864709", "14803899", "14900106", "14963335", "14984951",
    "15042731", "15142600", "19303906", "19775587", "22240633", "23211436",
    "24773685", "24796562", "25214411", "25241651", "26940699", "26957804",
    "16806755"
]

processed = 0
for img_id in image_ids:
    print(f"\nProcessing {img_id}...")
    try:
        with open(f"/tmp/listal_{img_id}.json") as f:
            data_json = json.load(f)
        html = data_json["solution"]["response"]
        data = parse_image_page(html)
        subject = data.get("subject_name", "Unknown")
        views = data.get("views", 0)
        related_count = len(data.get("related_images", []))
        lists_count = len(data.get("curated_lists", []))
        print(f"  Subject: {subject}, Views: {views}")
        print(f"  Related: {related_count}, Lists: {lists_count}")
        if data.get("image_url"):
            path, sha256 = download_image(data["image_url"])
            print(f"  Cached: {path.name} ({path.stat().st_size / 1024:.1f} KB)")
            neo4j.execute_write("""
                MERGE (li:ListalImage {image_id: $image_id})
                ON CREATE SET li.uuid = $uuid, li.normalized_url = $url, li.source_url = $url,
                    li.discovered_at = datetime(), li.created_at = datetime()
                SET li.subject_name = $name, li.views = $views, li.thumbnail_url = $thumb,
                    li.image_path = $path, li.sha256 = $sha256, li.cached_at = datetime(),
                    li.updated_at = datetime()
            """, {"image_id": img_id, "uuid": str(uuid4()), 
                  "url": f"https://www.listal.com/viewimage/{img_id}",
                  "name": subject, "views": views, "thumb": data.get("image_url"),
                  "path": str(path), "sha256": sha256})
            print(f"  Updated Neo4j")
        for voter in data.get("voters", []):
            neo4j.execute_write("""
                MERGE (lu:ListalUser {username: $username})
                ON CREATE SET lu.discovered_at = datetime()
                WITH lu MATCH (li:ListalImage {image_id: $image_id})
                MERGE (lu)-[:VOTED_FOR]->(li)
            """, {"username": voter, "image_id": img_id})
        for sim_id in data.get("related_images", []):
            neo4j.execute_write("""
                MATCH (li:ListalImage {image_id: $image_id})
                MERGE (sim:ListalImage {image_id: $sim_id})
                ON CREATE SET sim.discovered_at = datetime()
                MERGE (li)-[:SIMILAR_TO]->(sim)
            """, {"image_id": img_id, "sim_id": sim_id})
        for lst in data.get("curated_lists", []):
            slug = re.sub(r"[^a-z0-9\s-]", "", lst["name"].lower())
            slug = re.sub(r"[\s-]+", "-", slug)
            neo4j.execute_write("""
                MERGE (ll:ListalList {slug: $slug})
                ON CREATE SET ll.name = $name, ll.url = $url, ll.discovered_at = datetime()
                WITH ll MATCH (li:ListalImage {image_id: $image_id})
                MERGE (li)-[:IN_LIST]->(ll)
            """, {"slug": slug, "name": lst["name"], "url": lst["url"], "image_id": img_id})
        processed += 1
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n=== Done: {processed}/{len(image_ids)} ===")

# Summary
print("\n=== Graph Summary ===")
r = neo4j.execute_read("MATCH (li:ListalImage) WHERE li.views IS NOT NULL RETURN count(li) as total, sum(li.views) as total_views")
print(f"Images with data: {r[0]['total']}, Total views: {r[0]['total_views']}")
r = neo4j.execute_read("MATCH (l:ListalList) RETURN count(l) as count")
print(f"Curated lists: {r[0]['count']}")
r = neo4j.execute_read("MATCH (l:ListalList)-[:IN_LIST]->(i) RETURN count(distinct l) as lists_with, count(i) as links")
print(f"Lists with images: {r[0]['lists_with']}, Total links: {r[0]['links']}")
r = neo4j.execute_read("MATCH (li:ListalImage)-[:SIMILAR_TO]->(s) RETURN count(distinct li) as sources, count(s) as targets")
print(f"Similar image links: {r[0]['sources']} sources -> {r[0]['targets']} targets")

print("\n=== Top Images by Views ===")
r = neo4j.execute_read("MATCH (li:ListalImage) WHERE li.views IS NOT NULL RETURN li.image_id, li.subject_name, li.views ORDER BY li.views DESC LIMIT 10")
for rec in r:
    print(f"  {rec['li.image_id']}: {rec['li.subject_name']} ({rec['li.views']} views)")

print("\n=== Top Lists by Image Count ===")
r = neo4j.execute_read("MATCH (l:ListalList)-[:IN_LIST]->(i:ListalImage) WITH l, count(i) as cnt RETURN l.name, cnt ORDER BY cnt DESC LIMIT 5")
for rec in r:
    print(f"  {rec['l.name']}: {rec['cnt']} images")
