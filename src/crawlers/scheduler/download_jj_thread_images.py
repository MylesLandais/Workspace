"""Download all images from JJ-related threads."""

import sys
import requests
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

def download_image(image_url: str, output_dir: Path) -> tuple[Path, str] | None:
    """Download an image and return (path, sha256_hash)."""
    try:
        response = requests.get(image_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; imageboard-archiver/1.0)"
        })
        response.raise_for_status()
        
        image_bytes = response.content
        
        # Compute hash
        import hashlib
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()
        
        # Determine extension
        ext = ".jpg"
        if ".png" in image_url.lower():
            ext = ".png"
        elif ".gif" in image_url.lower():
            ext = ".gif"
        elif ".webm" in image_url.lower():
            ext = ".webm"
        
        # Save
        filename = f"{sha256_hash}{ext}"
        filepath = output_dir / filename
        
        if not filepath.exists():
            filepath.write_bytes(image_bytes)
            return filepath, sha256_hash
        else:
            return filepath, sha256_hash
            
    except Exception as e:
        print(f"  Error downloading {image_url}: {e}")
        return None

def main():
    print("=" * 70)
    print("DOWNLOADING JJ THREAD IMAGES")
    print("=" * 70)
    
    # Setup output directory
    output_dir = Path("/home/jovyan/workspaces/cache/imageboard/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()
    
    # Connect to Neo4j
    conn = get_connection()
    
    # Find all JJ-related threads
    result = conn.execute_read(
        """
        MATCH (t:Thread)
        WHERE toLower(t.title) CONTAINS "jj"
        RETURN t.board as board,
               t.thread_id as thread_id,
               t.title as title,
               t.url as url
        ORDER BY t.thread_id DESC
        """
    )
    
    if not result:
        print("No JJ-related threads found.")
        return
    
    print(f"Found {len(result)} JJ-related thread(s):\n")
    for record in result:
        print(f"  /{record['board']}/{record['thread_id']}: {record['title']}")
    print()
    
    # Get all images from these threads
    all_images = []
    for record in result:
        thread_id = record['thread_id']
        board = record['board']
        
        images_result = conn.execute_read(
            """
            MATCH (t:Thread {board: $board, thread_id: $thread_id})<-[:POSTED_IN]-(p:Post)
            WHERE p.image_url IS NOT NULL
            RETURN p.image_url as url,
                   p.image_filename as filename,
                   p.image_hash as existing_hash
            """,
            parameters={"board": board, "thread_id": thread_id}
        )
        
        for img_record in images_result:
            all_images.append({
                "url": img_record["url"],
                "filename": img_record.get("filename"),
                "thread_id": thread_id,
                "existing_hash": img_record.get("existing_hash"),
            })
    
    print(f"Found {len(all_images)} image(s) to download:\n")
    
    downloaded = 0
    skipped = 0
    errors = 0
    
    for i, img in enumerate(all_images, 1):
        url = img["url"]
        print(f"[{i}/{len(all_images)}] {url}")
        
        # Check if already downloaded
        if img["existing_hash"]:
            existing_file = output_dir / f"{img['existing_hash']}.jpg"
            if existing_file.exists():
                print(f"  -> Already exists: {existing_file.name}")
                skipped += 1
                continue
        
        # Download
        result = download_image(url, output_dir)
        if result:
            filepath, hash_value = result
            print(f"  -> Downloaded: {filepath.name} ({filepath.stat().st_size:,} bytes)")
            
            # Update database with hash and path
            conn.execute_write(
                """
                MATCH (p:Post {image_url: $url})
                SET p.image_hash = $hash,
                    p.image_path = $path
                """,
                parameters={
                    "url": url,
                    "hash": hash_value,
                    "path": str(filepath)
                }
            )
            downloaded += 1
        else:
            errors += 1
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total images: {len(all_images)}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Errors: {errors}")
    print(f"Output directory: {output_dir}")
    print()
    
    # List downloaded files
    image_files = list(output_dir.glob("*"))
    print(f"Total images in cache: {len(image_files)}")
    if len(image_files) > 0:
        total_size = sum(f.stat().st_size for f in image_files)
        print(f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    
    conn.close()

if __name__ == "__main__":
    main()






