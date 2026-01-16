"""Check where a thread was saved."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

thread_id = 944011323

print("=" * 70)
print(f"THREAD STORAGE LOCATION: /b/{thread_id}")
print("=" * 70)

conn = get_connection()

# Get thread info from Neo4j
result = conn.execute_read(
    """
    MATCH (t:Thread {thread_id: $thread_id})
    RETURN t.board as board,
           t.thread_id as thread_id,
           t.title as title,
           t.url as url,
           t.html_path as html_path,
           t.post_count as post_count,
           t.created_at as created_at
    LIMIT 1
    """,
    parameters={"thread_id": thread_id}
)

if result:
    r = result[0]
    print("\nNeo4j Database (KG_Slop):")
    print(f"  Board: /{r['board']}/")
    print(f"  Thread ID: {r['thread_id']}")
    print(f"  Title: {r['title']}")
    print(f"  URL: {r['url']}")
    print(f"  HTML Path: {r['html_path']}")
    print(f"  Post Count: {r['post_count']}")
    print(f"  Created: {r.get('created_at', 'N/A')}")
else:
    print("\nThread not found in Neo4j")

# Get post count
result2 = conn.execute_read(
    """
    MATCH (t:Thread {thread_id: $thread_id})<-[:POSTED_IN]-(p:Post)
    RETURN count(p) as post_count,
           collect(p.id)[0..5] as sample_ids
    """,
    parameters={"thread_id": thread_id}
)

if result2:
    r2 = result2[0]
    print(f"\nPosts in Database: {r2['post_count']}")
    if r2['sample_ids']:
        print(f"  Sample Post IDs: {r2['sample_ids']}")

# Check file system
print("\n" + "=" * 70)
print("FILE SYSTEM LOCATIONS")
print("=" * 70)

cache_dir = Path("/home/jovyan/workspace/cache/imageboard")
html_file = cache_dir / "html" / f"b_{thread_id}.html"

print(f"\nCache Directory: {cache_dir}")
print(f"  HTML File: {html_file}")

if html_file.exists():
    size = html_file.stat().st_size
    print(f"  Status: EXISTS ({size:,} bytes)")
else:
    print(f"  Status: NOT FOUND")

# Check for images
images_dir = cache_dir / "images"
if images_dir.exists():
    image_files = list(images_dir.glob("*"))
    print(f"\nImages Directory: {images_dir}")
    print(f"  Total cached images: {len(image_files)}")
    if len(image_files) > 0:
        print(f"  Sample: {image_files[0].name}")

conn.close()

print("\n" + "=" * 70)






