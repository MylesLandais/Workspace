#!/usr/bin/env python3
"""Check if an image exists in the database or cache."""

import sys
import hashlib
from pathlib import Path
from urllib.parse import urlparse

# Add src to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from feed.storage.neo4j_connection import get_connection
from feed.utils.image_hash import hash_image_url, download_and_hash_image


def check_image_by_url(image_url: str):
    """
    Check if an image exists in the database by URL or hash.
    
    Args:
        image_url: Image URL to check
    """
    print("=" * 80)
    print(f"Checking image: {image_url}")
    print("=" * 80)
    print()
    
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    print()
    
    # Check by URL first
    print("1. Checking by URL...")
    query_by_url = """
    MATCH (p:Post)
    WHERE p.url = $url
    RETURN p.id as post_id,
           p.title as title,
           p.url as url,
           p.image_hash as image_hash,
           p.image_dhash as image_dhash,
           p.created_utc as created,
           p.subreddit as subreddit
    LIMIT 10
    """
    
    results = neo4j.execute_read(query_by_url, parameters={"url": image_url})
    
    if results:
        print(f"   Found {len(results)} post(s) with this URL:")
        for i, record in enumerate(results, 1):
            print(f"\n   Post {i}:")
            print(f"     ID: {record.get('post_id')}")
            print(f"     Title: {record.get('title', 'N/A')[:60]}")
            print(f"     Subreddit: r/{record.get('subreddit', 'N/A')}")
            print(f"     Created: {record.get('created', 'N/A')}")
            print(f"     Image Hash: {record.get('image_hash', 'N/A')}")
            if record.get('image_dhash'):
                print(f"     Image dHash: {record.get('image_dhash')}")
        return True
    else:
        print("   No posts found with this URL")
    
    # Compute hash and check by hash
    print("\n2. Computing image hash...")
    try:
        image_hash, image_dhash = hash_image_url(image_url, timeout=10)
        if image_hash:
            print(f"   SHA-256: {image_hash}")
            if image_dhash:
                print(f"   dHash: {image_dhash}")
            
            # Check by SHA-256 hash
            print("\n3. Checking by SHA-256 hash...")
            query_by_hash = """
            MATCH (p:Post)
            WHERE p.image_hash = $hash
            RETURN p.id as post_id,
                   p.title as title,
                   p.url as url,
                   p.image_hash as image_hash,
                   p.image_dhash as image_dhash,
                   p.created_utc as created,
                   p.subreddit as subreddit
            LIMIT 10
            """
            
            results = neo4j.execute_read(
                query_by_hash,
                parameters={"hash": image_hash}
            )
            
            if results:
                print(f"   Found {len(results)} post(s) with this hash:")
                for i, record in enumerate(results, 1):
                    print(f"\n   Post {i}:")
                    print(f"     ID: {record.get('post_id')}")
                    print(f"     Title: {record.get('title', 'N/A')[:60]}")
                    print(f"     URL: {record.get('url', 'N/A')[:80]}")
                    print(f"     Subreddit: r/{record.get('subreddit', 'N/A')}")
                    print(f"     Created: {record.get('created', 'N/A')}")
                return True
            else:
                print("   No posts found with this hash")
            
            # Check by dHash if available
            if image_dhash:
                print("\n4. Checking by dHash...")
                query_by_dhash = """
                MATCH (p:Post)
                WHERE p.image_dhash = $dhash
                RETURN p.id as post_id,
                       p.title as title,
                       p.url as url,
                       p.image_hash as image_hash,
                       p.image_dhash as image_dhash,
                       p.created_utc as created,
                       p.subreddit as subreddit
                LIMIT 10
                """
                
                results = neo4j.execute_read(
                    query_by_dhash,
                    parameters={"dhash": image_dhash}
                )
                
                if results:
                    print(f"   Found {len(results)} post(s) with this dHash:")
                    for i, record in enumerate(results, 1):
                        print(f"\n   Post {i}:")
                        print(f"     ID: {record.get('post_id')}")
                        print(f"     Title: {record.get('title', 'N/A')[:60]}")
                        print(f"     URL: {record.get('url', 'N/A')[:80]}")
                        print(f"     Subreddit: r/{record.get('subreddit', 'N/A')}")
                        print(f"     Created: {record.get('created', 'N/A')}")
                    return True
                else:
                    print("   No posts found with this dHash")
        else:
            print("   Could not compute hash (image may be inaccessible)")
            
    except Exception as e:
        print(f"   Error computing hash: {e}")
    
    # Check Image nodes if they exist
    print("\n5. Checking Image nodes...")
    query_image_nodes = """
    MATCH (img:Image)
    WHERE img.url = $url
    RETURN img.url as url,
           img.hash as hash,
           count { (p:Post)-[:HAS_IMAGE]->(img) } as post_count
    LIMIT 10
    """
    
    results = neo4j.execute_read(
        query_image_nodes,
        parameters={"url": image_url}
    )
    
    if results:
        print(f"   Found {len(results)} Image node(s):")
        for i, record in enumerate(results, 1):
            print(f"\n   Image {i}:")
            print(f"     URL: {record.get('url', 'N/A')[:80]}")
            print(f"     Hash: {record.get('hash', 'N/A')}")
            print(f"     Linked to {record.get('post_count', 0)} post(s)")
        return True
    else:
        print("   No Image nodes found with this URL")
    
    print("\n" + "=" * 80)
    print("SUMMARY: Image not found in database")
    print("=" * 80)
    return False


def check_image_by_hash(image_hash: str):
    """
    Check if an image exists in the database by hash.
    
    Args:
        image_hash: SHA-256 hash of the image
    """
    print("=" * 80)
    print(f"Checking image by hash: {image_hash}")
    print("=" * 80)
    print()
    
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    print()
    
    query = """
    MATCH (p:Post)
    WHERE p.image_hash = $hash
    RETURN p.id as post_id,
           p.title as title,
           p.url as url,
           p.image_hash as image_hash,
           p.image_dhash as image_dhash,
           p.created_utc as created,
           p.subreddit as subreddit
    LIMIT 20
    """
    
    results = neo4j.execute_read(query, parameters={"hash": image_hash})
    
    if results:
        print(f"Found {len(results)} post(s) with this hash:")
        for i, record in enumerate(results, 1):
            print(f"\nPost {i}:")
            print(f"  ID: {record.get('post_id')}")
            print(f"  Title: {record.get('title', 'N/A')[:60]}")
            print(f"  URL: {record.get('url', 'N/A')[:80]}")
            print(f"  Subreddit: r/{record.get('subreddit', 'N/A')}")
            print(f"  Created: {record.get('created', 'N/A')}")
            if record.get('image_dhash'):
                print(f"  dHash: {record.get('image_dhash')}")
        return True
    else:
        print("No posts found with this hash")
        return False


def check_image_statistics():
    """Show statistics about images in the database."""
    print("=" * 80)
    print("Image Database Statistics")
    print("=" * 80)
    print()
    
    neo4j = get_connection()
    
    queries = {
        "Total posts with images": """
        MATCH (p:Post)
        WHERE p.image_hash IS NOT NULL
        RETURN count(p) as count
        """,
        "Unique image hashes": """
        MATCH (p:Post)
        WHERE p.image_hash IS NOT NULL
        RETURN count(DISTINCT p.image_hash) as count
        """,
        "Posts with dHash": """
        MATCH (p:Post)
        WHERE p.image_dhash IS NOT NULL
        RETURN count(p) as count
        """,
        "Image nodes count": """
        MATCH (img:Image)
        RETURN count(img) as count
        """,
        "Posts linked to Image nodes": """
        MATCH (p:Post)-[:HAS_IMAGE]->(img:Image)
        RETURN count(DISTINCT p) as count
        """,
    }
    
    for label, query in queries.items():
        try:
            result = neo4j.execute_read(query)
            if result:
                count = result[0].get('count', 0)
                print(f"{label}: {count:,}")
        except Exception as e:
            print(f"{label}: Error - {e}")
    
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check if an image exists in the database")
    parser.add_argument(
        "image_url",
        nargs="?",
        help="Image URL to check"
    )
    parser.add_argument(
        "--hash",
        help="Check by SHA-256 hash instead of URL"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show image database statistics"
    )
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            check_image_statistics()
        elif args.hash:
            check_image_by_hash(args.hash)
        elif args.image_url:
            check_image_by_url(args.image_url)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




