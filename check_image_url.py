"""Check if a imageboard image URL has been cached or indexed."""

import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection


def extract_image_id(image_url: str) -> str:
    """Extract image ID from imageboard image URL."""
    # Pattern: https://i.4cdn.org/{board}/{tim}.{ext}
    pattern = r"i\.4cdn\.org/[^/]+/(\d+)\."
    match = re.search(pattern, image_url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract image ID from URL: {image_url}")


def check_neo4j(neo4j, image_url: str, image_id: str):
    """Check if image exists in Neo4j database."""
    print("=" * 70)
    print("CHECKING NEO4J DATABASE")
    print("=" * 70)
    
    # Try searching by exact image_url
    query1 = """
    MATCH (p:Post {image_url: $image_url})
    MATCH (p)-[:POSTED_IN]->(t:Thread)
    RETURN p, t, p.post_no as post_no, p.comment as comment,
           p.subject as subject, t.thread_id as thread_id,
           t.board as board, t.url as thread_url,
           p.image_hash as image_hash, p.image_path as image_path,
           p.created_at as created_at
    LIMIT 5
    """
    
    result1 = neo4j.execute_read(
        query1,
        parameters={"image_url": image_url}
    )
    
    if result1:
        print(f"FOUND in Neo4j (exact URL match): {len(result1)} result(s)")
        for i, record in enumerate(result1, 1):
            print(f"\n  Result {i}:")
            print(f"    Thread: /{record.get('board')}/{record.get('thread_id')}")
            print(f"    Post: #{record.get('post_no')}")
            print(f"    URL: {record.get('thread_url', 'N/A')}")
            print(f"    Image Hash: {record.get('image_hash', 'N/A')}")
            print(f"    Image Path: {record.get('image_path', 'N/A')}")
            print(f"    Created: {record.get('created_at', 'N/A')}")
            if record.get('subject'):
                print(f"    Subject: {record.get('subject')[:60]}...")
            if record.get('comment'):
                comment_preview = record.get('comment', '')[:100]
                print(f"    Comment: {comment_preview}...")
        return True
    
    # Try searching by image_id in URL pattern
    query2 = """
    MATCH (p:Post)
    WHERE p.image_url CONTAINS $image_id
    MATCH (p)-[:POSTED_IN]->(t:Thread)
    RETURN p, t, p.post_no as post_no, p.comment as comment,
           p.subject as subject, t.thread_id as thread_id,
           t.board as board, t.url as thread_url,
           p.image_url as image_url, p.image_hash as image_hash,
           p.image_path as image_path, p.created_at as created_at
    LIMIT 5
    """
    
    result2 = neo4j.execute_read(
        query2,
        parameters={"image_id": image_id}
    )
    
    if result2:
        print(f"FOUND in Neo4j (image ID match): {len(result2)} result(s)")
        for i, record in enumerate(result2, 1):
            print(f"\n  Result {i}:")
            print(f"    Image URL: {record.get('image_url', 'N/A')}")
            print(f"    Thread: /{record.get('board')}/{record.get('thread_id')}")
            print(f"    Post: #{record.get('post_no')}")
            print(f"    URL: {record.get('thread_url', 'N/A')}")
            print(f"    Image Hash: {record.get('image_hash', 'N/A')}")
            print(f"    Image Path: {record.get('image_path', 'N/A')}")
            print(f"    Created: {record.get('created_at', 'N/A')}")
        return True
    
    print("NOT FOUND in Neo4j database")
    return False


def check_cache_directory(image_url: str, image_id: str):
    """Check if image exists in cache directory."""
    print("\n" + "=" * 70)
    print("CHECKING CACHE DIRECTORY")
    print("=" * 70)
    
    # Check default cache location
    cache_dir = Path("./cache/imageboard/images")
    
    if not cache_dir.exists():
        print(f"Cache directory does not exist: {cache_dir}")
        return False
    
    print(f"Cache directory: {cache_dir}")
    
    # Images are stored by SHA256 hash, so we need to search by filename pattern
    # or check all files. Let's search for files that might match.
    # The image ID might be in the filename or we can check all image files.
    
    # Check if there are any .jpg files (most common)
    jpg_files = list(cache_dir.glob("*.jpg"))
    png_files = list(cache_dir.glob("*.png"))
    gif_files = list(cache_dir.glob("*.gif"))
    webm_files = list(cache_dir.glob("*.webm"))
    
    total_files = len(jpg_files) + len(png_files) + len(gif_files) + len(webm_files)
    print(f"Total cached images: {total_files}")
    print(f"  - JPG: {len(jpg_files)}")
    print(f"  - PNG: {len(png_files)}")
    print(f"  - GIF: {len(gif_files)}")
    print(f"  - WEBM: {len(webm_files)}")
    
    # Note: Images are stored by hash, not by image ID, so we can't directly
    # match the image ID to a filename. We'd need to check the database
    # to find the hash, then look for that file.
    
    print("\nNote: Images are cached by SHA256 hash, not image ID.")
    print("To find the cached file, check the image_hash from Neo4j results above.")
    
    return False


def main():
    """Main entry point."""
    image_url = "https://i.4cdn.org/b/1766507822496134.jpg"
    
    print("=" * 70)
    print("IMAGEBOARD IMAGE URL CHECKER")
    print("=" * 70)
    print(f"Image URL: {image_url}")
    print()
    
    # Extract image ID
    try:
        image_id = extract_image_id(image_url)
        print(f"Image ID: {image_id}")
        print()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Check Neo4j
    found_in_db = False
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
        print()
        found_in_db = check_neo4j(neo4j, image_url, image_id)
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        print("(Neo4j may not be configured or not running)")
        print()
    
    # Check cache directory
    check_cache_directory(image_url, image_id)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Image URL: {image_url}")
    print(f"Image ID: {image_id}")
    if found_in_db:
        print("Status: FOUND in database")
    else:
        print("Status: NOT FOUND in database")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())






