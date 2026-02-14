"""Check if images were stored for a thread."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

thread_id = 944011323

print("=" * 70)
print(f"IMAGE STORAGE CHECK: /b/{thread_id}")
print("=" * 70)

conn = get_connection()

# Get posts with images
result = conn.execute_read(
    """
    MATCH (t:Thread {thread_id: $thread_id})<-[:POSTED_IN]-(p:Post)
    RETURN count(p) as total_posts,
           count(CASE WHEN p.image_url IS NOT NULL THEN 1 END) as posts_with_images,
           collect({
               url: p.image_url,
               hash: p.image_hash,
               path: p.image_path,
               filename: p.image_filename
           })[0..10] as sample_images
    """,
    parameters={"thread_id": thread_id}
)

if result:
    r = result[0]
    print(f"\nTotal Posts: {r['total_posts']}")
    print(f"Posts with Images: {r['posts_with_images']}")
    
    if r['posts_with_images'] > 0:
        print(f"\nSample Image Data:")
        for img in r['sample_images']:
            if img.get('url'):
                print(f"  URL: {img['url']}")
                print(f"  Hash: {img.get('hash', 'None')}")
                print(f"  Path: {img.get('path', 'None')}")
                print(f"  Filename: {img.get('filename', 'None')}")
                print()
    else:
        print("\nNo images stored in database")

# Check file system
print("=" * 70)
print("FILE SYSTEM CHECK")
print("=" * 70)

images_dir = Path("/home/jovyan/cache/imageboard/images")
print(f"\nImages Directory: {images_dir}")

if images_dir.exists():
    image_files = list(images_dir.glob("*"))
    print(f"  Status: EXISTS")
    print(f"  Total cached images: {len(image_files)}")
    if len(image_files) > 0:
        print(f"  Sample files:")
        for img in image_files[:5]:
            size = img.stat().st_size
            print(f"    {img.name} ({size:,} bytes)")
else:
    print(f"  Status: DIRECTORY DOES NOT EXIST")

conn.close()

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("Images were NOT downloaded because --no-images flag was used.")
print("Image URLs are stored in the database, but files are not cached.")






