"""Download all missing images from all monitored threads."""

import sys
import re
import requests
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

def extract_images_from_html(html_path: Path) -> list[dict]:
    """Extract all image URLs from imageboard thread HTML."""
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
    except Exception as e:
        print(f"  Error reading HTML: {e}")
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    images = []
    
    # Find all file links
    file_links = soup.find_all('a', class_='fileThumb')
    for link in file_links:
        href = link.get('href', '')
        if href:
            # Convert to full URL
            if href.startswith('//'):
                image_url = 'https:' + href
            elif href.startswith('/'):
                image_url = f'https://i.4cdn.org{href}'
            else:
                image_url = href
            
            images.append({'url': image_url})
    
    return images

def download_image(image_url: str, output_dir: Path) -> tuple[Path, str] | None:
    """Download an image and return (path, sha256_hash)."""
    try:
        response = requests.get(image_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; imageboard-archiver/1.0)"
        })
        response.raise_for_status()
        
        image_bytes = response.content
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()
        
        # Determine extension
        ext = ".jpg"
        if ".png" in image_url.lower():
            ext = ".png"
        elif ".gif" in image_url.lower():
            ext = ".gif"
        elif ".webm" in image_url.lower():
            ext = ".webm"
        
        filename = f"{sha256_hash}{ext}"
        filepath = output_dir / filename
        
        if not filepath.exists():
            filepath.write_bytes(image_bytes)
        
        return filepath, sha256_hash
            
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("=" * 70)
    print("DOWNLOADING ALL MISSING THREAD IMAGES")
    print("=" * 70)
    
    # Setup
    output_dir = Path("/home/jovyan/workspace/cache/imageboard/images")
    html_dir = Path("/home/jovyan/workspace/cache/imageboard/html")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    print()
    
    # Get all threads from database
    conn = get_connection()
    threads_result = conn.execute_read(
        """
        MATCH (t:Thread)
        RETURN t.board as board,
               t.thread_id as thread_id,
               t.title as title
        ORDER BY t.thread_id DESC
        """
    )
    
    print(f"Processing {len(threads_result)} thread(s):\n")
    
    total_downloaded = 0
    total_skipped = 0
    total_errors = 0
    
    for thread in threads_result:
        thread_id = thread['thread_id']
        board = thread['board']
        title = thread.get('title', 'N/A')
        
        print(f"Thread /{board}/{thread_id}: {title}")
        
        # Find HTML file
        html_file = html_dir / f"{board}_{thread_id}.html"
        if not html_file.exists():
            print(f"  -> HTML file not found: {html_file}")
            print()
            continue
        
        # Extract images from HTML
        images = extract_images_from_html(html_file)
        print(f"  -> Found {len(images)} image(s) in HTML")
        
        if not images:
            print()
            continue
        
        # Download each image
        downloaded = 0
        skipped = 0
        errors = 0
        
        for i, img in enumerate(images, 1):
            url = img['url']
            
            # Check if already in database with hash
            check_result = conn.execute_read(
                """
                MATCH (p:Post {image_url: $url})
                RETURN p.image_hash as hash
                LIMIT 1
                """,
                parameters={"url": url}
            )
            
            existing_hash = check_result[0]['hash'] if check_result and check_result[0].get('hash') else None
            
            if existing_hash:
                # Check if file exists
                existing_file = output_dir / f"{existing_hash}.jpg"
                if not existing_file.exists():
                    # Try other extensions
                    for ext in ['.png', '.gif', '.webm']:
                        existing_file = output_dir / f"{existing_hash}{ext}"
                        if existing_file.exists():
                            break
                
                if existing_file.exists():
                    print(f"  [{i}/{len(images)}] {url}")
                    print(f"    -> Already downloaded: {existing_file.name}")
                    skipped += 1
                    continue
            
            # Download
            print(f"  [{i}/{len(images)}] {url}")
            result = download_image(url, output_dir)
            if result:
                filepath, hash_value = result
                size = filepath.stat().st_size
                print(f"    -> Downloaded: {filepath.name} ({size:,} bytes)")
                
                # Update database
                try:
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
                except Exception as e:
                    print(f"    -> Warning: Could not update database: {e}")
                
                downloaded += 1
            else:
                errors += 1
        
        print(f"  -> Downloaded: {downloaded}, Skipped: {skipped}, Errors: {errors}")
        print()
        
        total_downloaded += downloaded
        total_skipped += skipped
        total_errors += errors
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total downloaded: {total_downloaded}")
    print(f"Total skipped: {total_skipped}")
    print(f"Total errors: {total_errors}")
    print()
    
    # Final stats
    image_files = list(output_dir.glob("*"))
    total_size = sum(f.stat().st_size for f in image_files if f.is_file())
    print(f"Total images in cache: {len(image_files)}")
    print(f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    print(f"Host path: /home/warby/Workspace/jupyter/cache/imageboard/images/")
    
    conn.close()

if __name__ == "__main__":
    main()






