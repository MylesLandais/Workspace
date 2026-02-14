#!/usr/bin/env python3
"""Fetch Listal image page and parse metadata."""

import json
import sys
import requests
from bs4 import BeautifulSoup

FLARESOLVER_URL = "http://host.docker.internal:8191"
IMAGE_URL = "https://www.listal.com/viewimage/26229169"

def fetch_via_flaresolver(url):
    """Fetch URL using FlareSolverr."""
    resp = requests.post(
        f"{FLARESOLVER_URL}/v1",
        json={
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000
        },
        timeout=120
    )
    data = resp.json()
    if data.get("status") != "ok":
        raise Exception(f"FlareSolverr error: {data.get('message')}")
    return data["solution"]["response"]

def parse_image_page(html):
    """Parse Listal image page HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    result = {}

    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        title = re.sub(r'\s*[-|]\s*Listal.*$', '', title, flags=re.IGNORECASE)
        result['subject_name'] = title.replace('Picture of ', '').strip()

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
            result['curated_lists'].append({
                "url": f"https://www.listal.com{href}",
                "name": name
            })

    date_match = re.search(r'(\d+)\s+(years?|months?|days?)\s+ago', text)
    result['added_ago'] = date_match.group(0) if date_match else "unknown"

    result['profile_url'] = f"https://www.listal.com/{result.get('subject_name', '').lower().replace(' ', '-')}"

    return result

if __name__ == "__main__":
    import re

    print("Fetching via FlareSolverr...")
    html = fetch_via_flaresolver(IMAGE_URL)
    print(f"Got {len(html)} bytes")

    print("\nParsing page...")
    data = parse_image_page(html)

    print("\n=== Parsed Metadata ===")
    print(json.dumps(data, indent=2))

    print("\n=== Store to Neo4j ===")
    from feed.storage.neo4j_connection import get_connection
    from uuid import uuid4
    from datetime import datetime

    neo4j = get_connection()
    print(f"Connected: {neo4j.uri}")

    image_id = "26229169"
    subject_name = data.get('subject_name', 'Maddie Teeuws')

    # Store ListalImage
    query = """
    MERGE (li:ListalImage {image_id: $image_id})
    ON CREATE SET
        li.uuid = $uuid,
        li.normalized_url = $normalized_url,
        li.source_url = $source_url,
        li.thumbnail_url = $thumbnail_url,
        li.views = $views,
        li.vote_count = $vote_count,
        li.subject_name = $subject_name,
        li.discovered_at = datetime(),
        li.created_at = datetime(),
        li.updated_at = datetime()
    ON MATCH SET
        li.views = $views,
        li.updated_at = datetime()
    RETURN li
    """

    neo4j.execute_write(query, {
        "image_id": image_id,
        "uuid": str(uuid4()),
        "normalized_url": IMAGE_URL,
        "source_url": IMAGE_URL,
        "thumbnail_url": data.get('image_url'),
        "views": data.get('views', 0),
        "vote_count": len(data.get('voters', [])),
        "subject_name": subject_name,
    })
    print(f"Stored ListalImage: {image_id}")

    # Store voters
    for voter in data.get('voters', []):
        voter_q = """
        MERGE (lu:ListalUser {username: $username})
        ON CREATE SET lu.discovered_at = datetime(), lu.created_at = datetime()
        WITH lu
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (lu)-[:VOTED_FOR]->(li)
        """
        neo4j.execute_write(voter_q, {"username": voter, "image_id": image_id})
    print(f"Stored {len(data.get('voters', []))} voters")

    # Store related images
    for related_id in data.get('related_images', []):
        related_q = """
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (lir:ListalImage {image_id: $related_id})
        ON CREATE SET lir.discovered_at = datetime()
        MERGE (li)-[:SIMILAR_TO]->(lir)
        """
        neo4j.execute_write(related_q, {"image_id": image_id, "related_id": related_id})
    print(f"Stored {len(data.get('related_images', []))} related images")

    # Store curated lists
    for lst in data.get('curated_lists', []):
        slug = re.sub(r'[^a-z0-9\s-]', '', lst['name'].lower())
        slug = re.sub(r'[\s-]+', '-', slug)
        list_q = """
        MERGE (ll:ListalList {slug: $slug})
        ON CREATE SET ll.name = $name, ll.url = $url, ll.discovered_at = datetime(), ll.created_at = datetime()
        WITH ll
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (li)-[:IN_LIST]->(ll)
        """
        neo4j.execute_write(list_q, {"slug": slug, "name": lst['name'], "url": lst['url'], "image_id": image_id})
    print(f"Stored {len(data.get('curated_lists', []))} curated lists")

    # Link to Creator if exists
    creator_q = """
    MATCH (c:Creator)
    WHERE c.name CONTAINS $name OR c.slug CONTAINS $slug
    MERGE (lp:ListalProfile {slug: $slug})
    ON CREATE SET lp.name = $name, lp.url = $url, lp.discovered_at = datetime()
    MERGE (c)-[:LISTAL_PROFILE]->(lp)
    MERGE (lp)-[:SUBJECT_OF]->(c)
    RETURN c.name, c.slug
    """
    name_lower = subject_name.lower()
    slug_lower = re.sub(r'[^a-z0-9-]', '', name_lower.replace(' ', '-'))
    result = neo4j.execute_write(creator_q, {
        "name": subject_name,
        "slug": slug_lower,
        "url": data['profile_url']
    })
    if result:
        print(f"Linked to Creator: {result[0].get('c.name', 'unknown')}")
    else:
        print("No matching Creator found")

    print("\nDone!")
