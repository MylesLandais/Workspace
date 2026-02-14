"""Find imageboard thread for an image and identify person using OSINT."""

import sys
import re
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection


def extract_image_id(image_url: str) -> Optional[str]:
    """Extract image ID from imageboard image URL."""
    # Pattern: https://i.4cdn.org/{board}/{tim}.{ext}
    pattern = r"i\.4cdn\.org/[^/]+/(\d+)\."
    match = re.search(pattern, image_url)
    if match:
        return match.group(1)
    return None


def search_neo4j_for_image(neo4j, image_url: str, image_id: str) -> Optional[Dict[str, Any]]:
    """Search Neo4j for posts containing this image."""
    # Try searching by image_url
    query = """
    MATCH (p:Post {image_url: $image_url})
    MATCH (p)-[:POSTED_IN]->(t:Thread)
    RETURN p, t, p.post_no as post_no, p.comment as comment,
           p.subject as subject, t.thread_id as thread_id,
           t.board as board, t.url as thread_url
    LIMIT 1
    """
    
    result = neo4j.execute_read(
        query,
        parameters={"image_url": image_url}
    )
    
    if result:
        record = result[0]
        return {
            "post": dict(record["p"]),
            "thread": dict(record["t"]),
            "post_no": record.get("post_no"),
            "comment": record.get("comment"),
            "subject": record.get("subject"),
            "thread_id": record.get("thread_id"),
            "board": record.get("board"),
            "thread_url": record.get("thread_url"),
        }
    
    # Try searching by image_id in URL pattern
    query2 = """
    MATCH (p:Post)
    WHERE p.image_url CONTAINS $image_id
    MATCH (p)-[:POSTED_IN]->(t:Thread)
    RETURN p, t, p.post_no as post_no, p.comment as comment,
           p.subject as subject, t.thread_id as thread_id,
           t.board as board, t.url as thread_url
    LIMIT 1
    """
    
    result2 = neo4j.execute_read(
        query2,
        parameters={"image_id": image_id}
    )
    
    if result2:
        record = result2[0]
        return {
            "post": dict(record["p"]),
            "thread": dict(record["t"]),
            "post_no": record.get("post_no"),
            "comment": record.get("comment"),
            "subject": record.get("subject"),
            "thread_id": record.get("thread_id"),
            "board": record.get("board"),
            "thread_url": record.get("thread_url"),
        }
    
    return None


def search_imageboard_api(image_id: str, board: str = "b") -> Optional[Dict[str, Any]]:
    """
    Search imageboard API for threads containing this image.
    Note: Imageboard API doesn't directly support image search, but we can check recent threads.
    """
    try:
        # Get catalog
        catalog_url = f"https://a.4cdn.org/{board}/catalog.json"
        response = requests.get(catalog_url, timeout=10)
        response.raise_for_status()
        catalog = response.json()
        
        # Search through threads
        for page in catalog:
            for thread in page.get("threads", []):
                thread_id = thread.get("no")
                if not thread_id:
                    continue
                
                # Fetch thread
                thread_url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"
                try:
                    thread_response = requests.get(thread_url, timeout=10)
                    thread_response.raise_for_status()
                    thread_data = thread_response.json()
                    
                    # Check posts for image
                    for post in thread_data.get("posts", []):
                        if post.get("tim") == int(image_id):
                            return {
                                "thread_id": thread_id,
                                "board": board,
                                "post_no": post.get("no"),
                                "subject": thread.get("sub", ""),
                                "comment": post.get("com", ""),
                                "thread_url": f"https://boards.4chan.org/{board}/thread/{thread_id}",
                            }
                except Exception:
                    continue
    except Exception as e:
        print(f"Error searching imageboard API: {e}")
    
    return None


def identify_person_in_image(image_url: str, image_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Identify person in image using face recognition and OSINT.
    This is a placeholder - would integrate with face recognition APIs.
    """
    # Download image if not cached
    if not image_path:
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_path = Path("/tmp") / f"image_{extract_image_id(image_url)}.jpg"
            image_path.write_bytes(response.content)
        except Exception as e:
            return {"error": f"Failed to download image: {e}"}
    
    # TODO: Integrate with face recognition service
    # Options:
    # 1. Google Vision API - Celebrity Detection
    # 2. AWS Rekognition - Celebrity Recognition
    # 3. Face++ API
    # 4. PimEyes (reverse image search)
    # 5. Yandex Reverse Image Search
    
    result = {
        "image_path": str(image_path),
        "image_url": image_url,
        "identified": False,
        "person": None,
        "confidence": None,
        "method": "placeholder",
    }
    
    # Placeholder for actual face recognition
    print("Note: Face recognition integration needed")
    print("Suggested APIs:")
    print("  - Google Cloud Vision API (Celebrity Detection)")
    print("  - AWS Rekognition (Celebrity Recognition)")
    print("  - PimEyes (Reverse Image Search)")
    print("  - Yandex Reverse Image Search")
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find imageboard thread for an image and identify person"
    )
    parser.add_argument(
        "image_url",
        help="imageboard image URL (e.g., https://i.4cdn.org/b/1766562467722962.jpg)"
    )
    parser.add_argument(
        "--identify",
        action="store_true",
        help="Attempt to identify person in image"
    )
    parser.add_argument(
        "--board",
        default="b",
        help="Board to search (default: b)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("IMAGEBOARD IMAGE THREAD FINDER")
    print("=" * 70)
    print(f"Image URL: {args.image_url}")
    print()
    
    # Extract image ID
    image_id = extract_image_id(args.image_url)
    if not image_id:
        print("Error: Could not extract image ID from URL")
        return 1
    
    print(f"Image ID: {image_id}")
    print()
    
    # Search Neo4j
    neo4j_result = None
    print("Searching Neo4j graph...")
    try:
        neo4j = get_connection()
        neo4j_result = search_neo4j_for_image(neo4j, args.image_url, image_id)
        
        if neo4j_result:
            print("Found in Neo4j!")
            print(f"  Thread: /{neo4j_result['board']}/{neo4j_result['thread_id']}")
            print(f"  Post: #{neo4j_result['post_no']}")
            print(f"  URL: {neo4j_result.get('thread_url', 'N/A')}")
            if neo4j_result.get('subject'):
                print(f"  Subject: {neo4j_result['subject']}")
            if neo4j_result.get('comment'):
                comment_preview = neo4j_result['comment'][:100]
                print(f"  Comment: {comment_preview}...")
            print()
        else:
            print("Not found in Neo4j graph")
            print()
    except Exception as e:
        print(f"Error searching Neo4j: {e}")
        print("(Neo4j may not be configured or thread not yet crawled)")
        print()
    
    # Search imageboard API
    api_result = None
    print("Searching imageboard API...")
    print("(This may take a while - checking recent threads...)")
    api_result = search_imageboard_api(image_id, args.board)
    
    if api_result:
        print("Found in imageboard API!")
        print(f"  Thread: /{api_result['board']}/{api_result['thread_id']}")
        print(f"  Post: #{api_result['post_no']}")
        print(f"  URL: {api_result['thread_url']}")
        if api_result.get('subject'):
            print(f"  Subject: {api_result['subject']}")
        print()
    else:
        print("Not found in recent threads (may be archived)")
        print()
    
    # Identify person if requested
    if args.identify:
        print("=" * 70)
        print("PERSON IDENTIFICATION (OSINT)")
        print("=" * 70)
        ident_result = identify_person_in_image(args.image_url)
        
        if ident_result.get("error"):
            print(f"Error: {ident_result['error']}")
        else:
            print(f"Image cached: {ident_result['image_path']}")
            if ident_result.get("identified"):
                print(f"Identified: {ident_result['person']}")
                print(f"Confidence: {ident_result['confidence']}")
                print(f"Method: {ident_result['method']}")
            else:
                print("Person identification not yet implemented")
                print("See suggestions above for API integration")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Image ID: {image_id}")
    found_thread = False
    if neo4j_result:
        print(f"Thread found (Neo4j): /{neo4j_result.get('board', 'N/A')}/{neo4j_result.get('thread_id', 'N/A')}")
        found_thread = True
    if api_result:
        print(f"Thread found (API): /{api_result.get('board', 'N/A')}/{api_result.get('thread_id', 'N/A')}")
        found_thread = True
    if not found_thread:
        print("Thread not found - may need to crawl more threads")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

