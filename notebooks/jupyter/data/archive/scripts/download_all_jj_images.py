"""Download all images from JJ thread by parsing HTML directly."""

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
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    
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
            
            # Get filename from link text or nearby elements
            filename = link.get_text().strip()
            
            images.append({
                'url': image_url,
                'filename': filename,
            })
    
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
    print("DOWNLOADING ALL JJ THREAD IMAGES")
    print("=" * 70)
    
    # Setup
    output_dir = Path("/home/jovyan/workspaces/cache/imageboard/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    html_dir = Path("/home/jovyan/workspaces/cache/imageboard/html")
    
    print(f"Output directory: {output_dir}")
    print()
    
    # Find JJ thread HTML files
    jj_html_files = list(html_dir.glob("b_944011323.html"))
    
    if not jj_html_files:
        print("No JJ thread HTML files found.")
        return
    
    all_images = []
    for html_file in jj_html_files:
        print(f"Parsing: {html_file.name}")
        images = extract_images_from_html(html_file)
        print(f"  Found {len(images)} image(s)")
        all_images.extend(images)
        print()
    
    if not all_images:
        print("No images found in HTML.")
        return
    
    print(f"Total images to download: {len(all_images)}\n")
    print("=" * 70)
    
    downloaded = 0
    skipped = 0
    errors = 0
    
    for i, img in enumerate(all_images, 1):
        url = img['url']
        print(f"[{i}/{len(all_images)}] {url}")
        
        # Check if already exists by hash
        result = download_image(url, output_dir)
        if result:
            filepath, hash_value = result
            size = filepath.stat().st_size
            if size > 0:
                print(f"  -> Saved: {filepath.name} ({size:,} bytes)")
                downloaded += 1
            else:
                print(f"  -> Already exists: {filepath.name}")
                skipped += 1
        else:
            errors += 1
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total images: {len(all_images)}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print()
    
    # List files
    image_files = sorted(output_dir.glob("*"), key=lambda x: x.stat().st_size, reverse=True)
    print(f"Total images in cache: {len(image_files)}")
    if image_files:
        total_size = sum(f.stat().st_size for f in image_files)
        print(f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        print(f"\nLargest files:")
        for f in image_files[:5]:
            size = f.stat().st_size
            print(f"  {f.name}: {size:,} bytes ({size / 1024:.1f} KB)")
    
    print(f"\nFiles accessible at: /home/warby/Workspace/jupyter/cache/imageboard/images/")

if __name__ == "__main__":
    main()






