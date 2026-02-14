#!/usr/bin/env python3
"""
Crawl Fapello profile for Ovilee May and store in Neo4j knowledge graph.

This script fetches all media from https://fapello.com/ovilee-may/ and stores:
- Creator node (Ovilee May)
- Handle node (ovilee-may on Fapello)
- Platform node (Fapello)
- Media nodes (all images/videos)
- Relationships between all nodes
"""

import sys
import re
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.fapello import FapelloAdapter
from feed.storage.neo4j_connection import get_connection


def store_fapello_profile(neo4j, profile_url: str, limit: int = None):
    """
    Crawl a Fapello profile and store Creator, Handle, Platform, and Media nodes in Neo4j.
    
    Args:
        neo4j: Neo4j connection
        profile_url: Fapello profile URL (e.g., https://fapello.com/ovilee-may/)
        limit: Maximum number of media items to fetch (None = all)
    """
    print(f"\n{'='*60}")
    print(f"Crawling Fapello profile: {profile_url}")
    print(f"{'='*60}\n")
    
    # Initialize Fapello adapter
    fapello = FapelloAdapter(delay_min=2.0, delay_max=5.0, mock=False)
    
    # Extract username from URL
    match = re.search(r'fapello\.com/([^/]+)/?', profile_url)
    if not match:
        print(f"Error: Could not extract username from URL: {profile_url}")
        return
    username = match.group(1)
    print(f"Username: {username}")
    
    # Fetch profile metadata
    print("\nFetching profile metadata...")
    metadata = fapello.fetch_source_metadata(profile_url)
    if not metadata:
        print(f"Warning: Could not fetch metadata for {profile_url}")
        creator_name = username.replace('-', ' ').title()
    else:
        print(f"  Name: {metadata.name}")
        print(f"  Description: {metadata.description}")
        print(f"  Subscribers/Likes: {metadata.subscribers}")
        
        # Extract creator name from description if available
        creator_name = username.replace('-', ' ').title()
        if metadata.description and 'Fapello profile:' in metadata.description:
            name_match = re.search(r'profile:\s*([^(]+)', metadata.description)
            if name_match:
                creator_name = name_match.group(1).strip()
    
    # Fetch media items
    print(f"\nFetching media items (limit: {limit if limit else 'all'})...")
    media_items = fapello.fetch_media(profile_url, limit=limit)
    print(f"Found {len(media_items)} media items")
    
    if not media_items:
        print("No media items found. Exiting.")
        return
    
    # Create Platform node for Fapello
    print("\nCreating/updating Platform node...")
    platform_query = """
    MERGE (p:Platform {slug: $slug})
    ON CREATE SET
        p.uuid = randomUUID(),
        p.name = $name,
        p.slug = $slug,
        p.icon_url = $icon_url,
        p.created_at = datetime(),
        p.updated_at = datetime()
    ON MATCH SET
        p.updated_at = datetime()
    RETURN p.uuid as uuid
    """
    neo4j.execute_write(
        platform_query,
        parameters={
            "slug": "fapello",
            "name": "Fapello",
            "icon_url": "https://fapello.com/assets/favicon/favicon-32x32.png"
        }
    )
    print("  Created/updated Platform node: Fapello")
    
    # Create Creator node
    print(f"\nCreating/updating Creator node: {creator_name}...")
    creator_query = """
    MERGE (c:Creator {slug: $slug})
    ON CREATE SET
        c.uuid = randomUUID(),
        c.name = $name,
        c.slug = $slug,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.name = $name,
        c.updated_at = datetime()
    RETURN c.uuid as uuid, c.slug as slug
    """
    creator_result = neo4j.execute_write(
        creator_query,
        parameters={
            "slug": username,
            "name": creator_name
        }
    )
    if creator_result:
        creator_uuid = creator_result[0]['uuid']
        print(f"  Created/updated Creator node: {creator_name} (slug: {username}, uuid: {creator_uuid})")
    
    # Create Handle node for Fapello profile
    print(f"\nCreating/updating Handle node: {username}...")
    handle_query = """
    MATCH (c:Creator {slug: $creator_slug})
    MERGE (h:Handle {profile_url: $profile_url})
    ON CREATE SET
        h.uuid = randomUUID(),
        h.username = $username,
        h.display_name = $display_name,
        h.profile_url = $profile_url,
        h.created_at = datetime(),
        h.updated_at = datetime()
    ON MATCH SET
        h.username = $username,
        h.display_name = $display_name,
        h.updated_at = datetime()
    WITH h, c
    MERGE (c)-[r:OWNS_HANDLE]->(h)
    ON CREATE SET
        r.status = 'Active',
        r.verified = false,
        r.confidence = 'High',
        r.discovered_at = datetime(),
        r.created_at = datetime()
    WITH h
    MATCH (p:Platform {slug: 'fapello'})
    MERGE (h)-[:ON_PLATFORM]->(p)
    RETURN h.uuid as uuid
    """
    handle_result = neo4j.execute_write(
        handle_query,
        parameters={
            "creator_slug": username,
            "username": username,
            "display_name": creator_name,
            "profile_url": profile_url.rstrip('/')
        }
    )
    if handle_result:
        handle_uuid = handle_result[0]['uuid']
        print(f"  Created/updated Handle node: {username} (uuid: {handle_uuid})")
    
    # Store all media items
    print(f"\nStoring {len(media_items)} media items...")
    stored_count = 0
    error_count = 0
    
    for i, media in enumerate(media_items, 1):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(media_items)} (stored: {stored_count}, errors: {error_count})")
        
        # Create Media node
        media_query = """
        MERGE (m:Media {source_url: $source_url})
        ON CREATE SET
            m.uuid = randomUUID(),
            m.title = $title,
            m.source_url = $source_url,
            m.publish_date = datetime({epochSeconds: $publish_epoch}),
            m.thumbnail_url = $thumbnail_url,
            m.media_type = $media_type,
            m.created_at = datetime(),
            m.updated_at = datetime()
        ON MATCH SET
            m.title = $title,
            m.thumbnail_url = $thumbnail_url,
            m.updated_at = datetime()
        WITH m
        WHERE m.media_type = 'Image'
        SET m:Image
        WITH m
        MATCH (h:Handle {profile_url: $profile_url})
        MERGE (h)-[r:PUBLISHED]->(m)
        ON CREATE SET
            r.published_at = datetime({epochSeconds: $publish_epoch}),
            r.created_at = datetime()
        WITH m
        MATCH (p:Platform {slug: 'fapello'})
        MERGE (m)-[:SOURCED_FROM]->(p)
        RETURN m.uuid as uuid
        """
        
        publish_epoch = int(media.publish_date.timestamp()) if media.publish_date else int(datetime.utcnow().timestamp())
        
        try:
            result = neo4j.execute_write(
                media_query,
                parameters={
                    "source_url": media.source_url,
                    "title": media.title or f"{username} - {i}",
                    "publish_epoch": publish_epoch,
                    "thumbnail_url": media.thumbnail_url,
                    "media_type": media.media_type.value,
                    "profile_url": profile_url.rstrip('/')
                }
            )
            if result:
                stored_count += 1
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Only print first 5 errors
                print(f"  Error storing media {i}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Import Complete!")
    print(f"{'='*60}")
    print(f"Successfully stored: {stored_count}/{len(media_items)} media items")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print(f"\nKnowledge graph structure:")
    print(f"  - Creator: {creator_name} (slug: {username})")
    print(f"  - Handle: {username} on Fapello")
    print(f"  - Platform: Fapello")
    print(f"  - Media: {stored_count} Image nodes")
    print(f"  - Relationships:")
    print(f"    * Creator -> OWNS_HANDLE -> Handle")
    print(f"    * Handle -> ON_PLATFORM -> Platform")
    print(f"    * Handle -> PUBLISHED -> Media")
    print(f"    * Media -> SOURCED_FROM -> Platform")
    print(f"{'='*60}\n")


def query_stored_data(neo4j, username: str):
    """Query and display the stored data."""
    query = """
    MATCH (c:Creator {slug: $username})-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform)
    OPTIONAL MATCH (h)-[:PUBLISHED]->(m:Media)
    RETURN 
        c.name as creator_name,
        c.slug as creator_slug,
        h.username as handle_username,
        p.name as platform_name,
        count(DISTINCT m) as media_count,
        collect(DISTINCT m.uuid)[0..5] as sample_media_uuids
    """
    result = neo4j.execute_read(query, parameters={"username": username})
    if result:
        for record in result:
            print(f"\nQuery Results:")
            print(f"  Creator: {record['creator_name']} (slug: {record['creator_slug']})")
            print(f"  Handle: {record['handle_username']} on {record['platform_name']}")
            print(f"  Media count: {record['media_count']}")
            if record['sample_media_uuids']:
                print(f"  Sample media UUIDs: {record['sample_media_uuids'][:3]}...")


if __name__ == "__main__":
    import sys
    
    # Get profile URL from command line argument or use default
    if len(sys.argv) > 1:
        profile_url = sys.argv[1]
        if not profile_url.startswith("http"):
            profile_url = f"https://fapello.com/{profile_url}/"
    else:
        # Default to ovilee-may
        profile_url = "https://fapello.com/ovilee-may/"
    
    # Extract username for query
    match = re.search(r'fapello\.com/([^/]+)/?', profile_url)
    if not match:
        print(f"Error: Invalid Fapello URL: {profile_url}")
        sys.exit(1)
    username = match.group(1)
    
    # Get limit from command line if provided
    limit = None
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid limit '{sys.argv[2]}', using None (fetch all)")
    
    # Connect to Neo4j
    print("Connecting to Neo4j...")
    neo4j = get_connection()
    print(f"Connected to: {neo4j.uri}\n")
    
    # Store the profile and all media
    # Set limit=None to fetch all, or specify a number (e.g., 100) for testing
    store_fapello_profile(neo4j, profile_url, limit=limit)
    
    # Query to verify
    query_stored_data(neo4j, username)

