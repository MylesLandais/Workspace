#!/usr/bin/env python3
"""Parse Listal response and store to Neo4j."""

import json
import re
from uuid import uuid4
from datetime import datetime

IMAGE_ID = "26229169"

with open('/tmp/listal_response.json') as f:
    data = json.load(f)

html = data.get('solution', {}).get('response', '')

from bs4 import BeautifulSoup
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

print("=== Parsed Metadata ===")
print(json.dumps(result, indent=2))

print("\n=== Store to Neo4j ===")
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
print(f"Connected: {neo4j.uri}")

image_id = IMAGE_ID
subject_name = result.get('subject_name', 'Maddie Teeuws')

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
    "normalized_url": f"https://www.listal.com/viewimage/{image_id}",
    "source_url": f"https://www.listal.com/viewimage/{image_id}",
    "thumbnail_url": result.get('image_url'),
    "views": result.get('views', 0),
    "vote_count": len(result.get('voters', [])),
    "subject_name": subject_name,
})
print(f"Stored ListalImage: {image_id}")

for voter in result.get('voters', []):
    voter_q = """
    MERGE (lu:ListalUser {username: $username})
    ON CREATE SET lu.discovered_at = datetime(), lu.created_at = datetime()
    WITH lu
    MATCH (li:ListalImage {image_id: $image_id})
    MERGE (lu)-[:VOTED_FOR]->(li)
    """
    neo4j.execute_write(voter_q, {"username": voter, "image_id": image_id})
print(f"Stored {len(result.get('voters', []))} voters")

for related_id in result.get('related_images', []):
    related_q = """
    MATCH (li:ListalImage {image_id: $image_id})
    MERGE (lir:ListalImage {image_id: $related_id})
    ON CREATE SET lir.discovered_at = datetime()
    MERGE (li)-[:SIMILAR_TO]->(lir)
    """
    neo4j.execute_write(related_q, {"image_id": image_id, "related_id": related_id})
print(f"Stored {len(result.get('related_images', []))} related images")

for lst in result.get('curated_lists', []):
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
print(f"Stored {len(result.get('curated_lists', []))} curated lists")

name_lower = subject_name.lower()
slug_lower = re.sub(r'[^a-z0-9-]', '', name_lower.replace(' ', '-'))

creator_q = """
MATCH (c:Creator)
WHERE c.name CONTAINS $name OR c.slug CONTAINS $slug
MERGE (lp:ListalProfile {slug: $slug})
ON CREATE SET lp.name = $name, lp.url = $url, lp.discovered_at = datetime()
MERGE (c)-[:LISTAL_PROFILE]->(lp)
MERGE (lp)-[:SUBJECT_OF]->(c)
RETURN c.name, c.slug
"""
result_neo = neo4j.execute_write(creator_q, {
    "name": subject_name,
    "slug": slug_lower,
    "url": f"https://www.listal.com/{slug_lower}"
})
if result_neo:
    print(f"Linked to Creator: {result_neo[0].get('c.name', 'unknown')}")
else:
    print("No matching Creator found - creating profile anyway")
    profile_q = """
    MERGE (lp:ListalProfile {slug: $slug})
    ON CREATE SET lp.name = $name, lp.url = $url, lp.discovered_at = datetime(), lp.created_at = datetime()
    RETURN lp
    """
    neo4j.execute_write(profile_q, {"slug": slug_lower, "name": subject_name, "url": f"https://www.listal.com/{slug_lower}"})
    print(f"Created ListalProfile: {slug_lower}")

print("\nDone!")
