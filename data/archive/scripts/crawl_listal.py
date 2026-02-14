#!/usr/bin/env python3
"""
Listal crawler integration with web index queue.
Discovers and queues Listal profiles/images for crawling.
"""

import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent / "src"))

import requests
from bs4 import BeautifulSoup

from feed.platforms.listal import ListalAdapter
from feed.storage.neo4j_connection import get_connection


def add_listal_url_to_queue(
    neo4j,
    url: str,
    entity_name: Optional[str] = None,
    priority: float = 1.0,
    crawl_interval_days: float = 1.0,
) -> bool:
    """
    Add a Listal URL to the web index queue.

    Args:
        neo4j: Neo4j connection
        url: Listal URL (profile or image)
        entity_name: Optional entity name for linking to Creator
        priority: Crawl priority (higher = more important)
        crawl_interval_days: How often to re-crawl

    Returns:
        True if URL was added, False if already exists
    """
    from uuid import uuid4
    from urllib.parse import urlparse

    normalized_url = _normalize_listal_url(url)
    domain = "www.listal.com"

    query = """
    MATCH (w:WebPage {normalized_url: $normalized_url})
    RETURN w.normalized_url as url
    LIMIT 1
    """
    existing = neo4j.execute_read(query, parameters={"normalized_url": normalized_url})

    if existing:
        return False

    create_query = """
    MERGE (w:WebPage {normalized_url: $normalized_url})
    ON CREATE SET
        w.original_url = $original_url,
        w.domain = $domain,
        w.source_type = 'listal',
        w.entity_name = $entity_name,
        w.next_crawl_at = datetime(),
        w.crawl_interval_days = $crawl_interval_days,
        w.change_count = 0,
        w.no_change_count = 0,
        w.robots_allowed = true,
        w.created_at = datetime(),
        w.updated_at = datetime()
    ON MATCH SET
        w.updated_at = datetime()
    RETURN w
    """

    neo4j.execute_write(
        create_query,
        parameters={
            "normalized_url": normalized_url,
            "original_url": url,
            "domain": domain,
            "entity_name": entity_name,
            "crawl_interval_days": crawl_interval_days,
        },
    )

    print(f"Queued: {normalized_url}")
    return True


def _normalize_listal_url(url: str) -> str:
    """Normalize Listal URL to canonical form."""
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"

    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def discover_profile_images(
    neo4j,
    profile_url: str,
    entity_name: Optional[str] = None,
    max_images: int = 50,
) -> List[str]:
    """
    Discover images from a Listal profile and queue them.

    Args:
        neo4j: Neo4j connection
        profile_url: Listal profile URL
        entity_name: Entity name for linking
        max_images: Maximum images to queue

    Returns:
        List of queued image URLs
    """
    adapter = ListalAdapter(mock=True)
    images = adapter._fetch_profile_images(profile_url, limit=max_images)

    queued = []
    for img in images:
        added = add_listal_url_to_queue(
            neo4j,
            img.source_url,
            entity_name=entity_name,
            priority=0.8,
            crawl_interval_days=7.0,
        )
        if added:
            queued.append(img.source_url)

    return queued


def discover_related_images(
    neo4j,
    image_url: str,
    entity_name: Optional[str] = None,
) -> List[str]:
    """
    Parse an image page and discover related images from "People also voted for".

    Args:
        neo4j: Neo4j connection
        image_url: Listal image URL
        entity_name: Entity name for linking

    Returns:
        List of discovered related image URLs
    """
    adapter = ListalAdapter(mock=True)

    response = requests.get(image_url, headers=adapter.headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')

    related_urls = []
    related_links = soup.select('a[href*="/viewimage/"]')

    for link in related_links:
        href = link.get('href', '')
        if href and '/viewimage/' in href:
            if not href.startswith('http'):
                href = f"https://www.listal.com{href}"
            if href not in related_urls:
                related_urls.append(href)

    queued = []
    for url in related_urls[:20]:
        added = add_listal_url_to_queue(
            neo4j,
            url,
            entity_name=entity_name,
            priority=0.5,
            crawl_interval_days=14.0,
        )
        if added:
            queued.append(url)

    return queued


def store_listal_image(
    neo4j,
    image_url: str,
    image_data: Dict[str, Any],
    creator_slug: Optional[str] = None,
) -> None:
    """
    Store parsed Listal image data in Neo4j.

    Args:
        neo4j: Neo4j connection
        image_url: Normalized image URL
        image_data: Parsed image metadata from parse_image_page()
        creator_slug: Optional Creator slug to link to
    """
    from uuid import uuid4

    image_id = image_data.get("image_id", "unknown")
    subject_name = image_data.get("subject_name", "Unknown")

    query = """
    MERGE (li:ListalImage {image_id: $image_id})
    ON CREATE SET
        li.uuid = $uuid,
        li.normalized_url = $normalized_url,
        li.source_url = $source_url,
        li.thumbnail_url = $thumbnail_url,
        li.views = $views,
        li.vote_count = $vote_count,
        li.added_date = $added_date,
        li.added_by = $added_by,
        li.subject_name = $subject_name,
        li.discovered_at = datetime(),
        li.created_at = datetime(),
        li.updated_at = datetime()
    ON MATCH SET
        li.views = $views,
        li.vote_count = $vote_count,
        li.updated_at = datetime()
    RETURN li
    """

    neo4j.execute_write(
        query,
        parameters={
            "image_id": image_id,
            "uuid": str(uuid4()),
            "normalized_url": image_url,
            "source_url": image_url,
            "thumbnail_url": image_data.get("thumbnail_url"),
            "views": image_data.get("views", 0),
            "vote_count": image_data.get("vote_count", 0),
            "added_date": image_data.get("added_date", datetime.utcnow()),
            "added_by": image_data.get("added_by"),
            "subject_name": subject_name,
        },
    )

    for voter in image_data.get("voters", []):
        voter_query = """
        MERGE (lu:ListalUser {username: $username})
        ON CREATE SET
            lu.discovered_at = datetime(),
            lu.created_at = datetime()
        WITH lu
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (lu)-[:VOTED_FOR]->(li)
        ON CREATE SET lu.updated_at = datetime()
        """
        neo4j.execute_write(
            voter_query,
            parameters={"username": voter, "image_id": image_id},
        )

    for related_id in image_data.get("related_image_ids", []):
        related_query = """
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (lir:ListalImage {image_id: $related_id})
        ON CREATE SET lir.discovered_at = datetime()
        MERGE (li)-[:SIMILAR_TO]->(lir)
        """
        neo4j.execute_write(
            related_query,
            parameters={"image_id": image_id, "related_id": related_id},
        )

    for lst in image_data.get("curator_lists", []):
        list_url = lst.get("list_url", "")
        list_name = lst.get("list_name", "Unknown")
        list_slug = _slugify(list_name)

        list_query = """
        MERGE (ll:ListalList {slug: $slug})
        ON CREATE SET
            ll.name = $name,
            ll.url = $url,
            ll.curator = $curator,
            ll.discovered_at = datetime(),
            ll.created_at = datetime()
        WITH ll
        MATCH (li:ListalImage {image_id: $image_id})
        MERGE (li)-[:IN_LIST]->(ll)
        """
        neo4j.execute_write(
            list_query,
            parameters={
                "slug": list_slug,
                "name": list_name,
                "url": list_url,
                "curator": image_data.get("added_by"),
                "image_id": image_id,
            },
        )

    if creator_slug:
        profile_query = """
        MATCH (c:Creator {slug: $creator_slug})
        MERGE (lp:ListalProfile {slug: $slug})
        ON CREATE SET
            lp.name = $name,
            lp.url = $profile_url,
            lp.discovered_at = datetime(),
            lp.created_at = datetime()
        WITH c, lp
        MERGE (c)-[:LISTAL_PROFILE]->(lp)
        MERGE (lp)-[:SUBJECT_OF]->(c)
        """
        slug = _slugify(subject_name)
        neo4j.execute_write(
            profile_query,
            parameters={
                "creator_slug": creator_slug,
                "slug": slug,
                "name": subject_name,
                "profile_url": f"https://www.listal.com/{slug}",
            },
        )


def _slugify(text: str) -> str:
    """Create URL-safe slug from text."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')


def crawl_listal_image(neo4j, image_url: str, creator_slug: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Crawl a Listal image and store results.

    Args:
        neo4j: Neo4j connection
        image_url: Listal image URL
        creator_slug: Optional Creator to link to

    Returns:
        Parsed image data or None
    """
    adapter = ListalAdapter()

    try:
        response = requests.get(image_url, headers=adapter.headers, timeout=15)
        response.raise_for_status()

        image_data = adapter.parse_image_page(response.text)

        store_listal_image(neo4j, image_url, image_data, creator_slug=creator_slug)

        update_query = """
        MATCH (w:WebPage {normalized_url: $url})
        SET w.last_crawled_at = datetime(),
            w.http_status = 200,
            w.updated_at = datetime()
        """
        neo4j.execute_write(update_query, parameters={"url": image_url})

        return image_data

    except Exception as e:
        print(f"Error crawling Listal image {image_url}: {e}")

        update_query = """
        MATCH (w:WebPage {normalized_url: $url})
        SET w.last_crawled_at = datetime(),
            w.http_status = 500,
            w.updated_at = datetime()
        """
        neo4j.execute_write(update_query, parameters={"url": image_url})

        return None


if __name__ == "__main__":
    import argparse
    import requests
    from bs4 import BeautifulSoup

    parser = argparse.ArgumentParser(description="Listal crawler integration")
    parser.add_argument("command", choices=["queue", "crawl", "discover"])
    parser.add_argument("--url", help="URL to process")
    parser.add_argument("--entity", help="Entity name for linking")
    parser.add_argument("--creator", help="Creator slug to link to")

    args = parser.parse_args()

    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")

    if args.command == "queue":
        if args.url:
            add_listal_url_to_queue(neo4j, args.url, entity_name=args.entity)
        else:
            print("Error: --url required")

    elif args.command == "crawl":
        if args.url:
            crawl_listal_image(neo4j, args.url, creator_slug=args.creator)
        else:
            print("Error: --url required")

    elif args.command == "discover":
        if args.url:
            discover_profile_images(neo4j, args.url, entity_name=args.entity)
        else:
            print("Error: --url required")
