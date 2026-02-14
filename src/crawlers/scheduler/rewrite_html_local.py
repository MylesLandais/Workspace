"""Rewrite imageboard HTML to use local cached images."""

import sys
import os
import re
import hashlib
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional
from urllib.parse import urlparse


def compute_sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def compute_image_hash_from_url(image_url: str) -> Optional[str]:
    """Download image and compute its hash."""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return compute_sha256_hash(response.content)
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")
        return None


def find_cached_image_by_hash(cache_dir: Path, image_hash: str) -> Optional[Path]:
    """Find cached image by hash in any thread directory."""
    # Search in flat directory
    flat_path = cache_dir / image_hash
    if flat_path.exists():
        return flat_path
    
    # Search in board/thread structure
    for board_dir in cache_dir.iterdir():
        if not board_dir.is_dir():
            continue
        for thread_dir in board_dir.iterdir():
            if not thread_dir.is_dir():
                continue
            for image_file in thread_dir.iterdir():
                if image_file.name.startswith(image_hash):
                    return image_file
    
    return None


def extract_image_urls_from_html(html_path: Path) -> list:
    """Extract all 4chan image URLs from HTML."""
    content = html_path.read_text(encoding='utf-8')
    
    # Pattern for 4chan images
    patterns = [
        r'https://i\.4cdn\.org/[^/]+/[0-9]+\.[a-z]+',
        r'//i\.4cdn\.org/[^/]+/[0-9]+\.[a-z]+',
    ]
    
    urls = set()
    for pattern in patterns:
        urls.update(re.findall(pattern, content))
    
    return sorted(urls)


def rewrite_html_with_local_images(
    html_path: Path,
    cache_dir: Path,
    output_path: Path = None,
    download_missing: bool = False
) -> Tuple[Path, Dict[str, str]]:
    """
    Rewrite HTML to use local cached images.
    
    Args:
        html_path: Path to original HTML file
        cache_dir: Directory containing cached images
        output_path: Path to write rewritten HTML (default: same dir with '_local' suffix)
        download_missing: If True, download missing images
    
    Returns:
        Tuple of (output_path, url_to_local_path_mapping)
    """
    if output_path is None:
        output_path = html_path.parent / f"{html_path.stem}_local{html_path.suffix}"
    
    content = html_path.read_text(encoding='utf-8')
    
    # Extract image URLs
    image_urls = extract_image_urls_from_html(html_path)
    print(f"Found {len(image_urls)} image URLs")
    
    # Build mapping of URLs to local paths
    url_to_local: Dict[str, str] = {}
    missing_count = 0
    
    for url in image_urls:
        # Ensure full URL
        if url.startswith('//'):
            url = 'https:' + url
        
        # Get file extension
        ext = Path(urlparse(url).path).suffix or '.jpg'
        
        # Compute hash by downloading
        print(f"\nProcessing: {Path(url).name}")
        image_hash = compute_image_hash_from_url(url)
        
        if not image_hash:
            print(f"  Skipping {url}")
            continue
        
        # Find cached image
        cached_path = find_cached_image_by_hash(cache_dir, image_hash + ext)
        if cached_path:
            # Convert to relative path from HTML location
            try:
                rel_path = cached_path.relative_to(html_path.parent)
                url_to_local[url] = str(rel_path)
                print(f"  ✓ Found local: {rel_path}")
            except ValueError:
                # Image is not under HTML parent, use absolute
                url_to_local[url] = str(cached_path)
                print(f"  ✓ Found (absolute): {cached_path}")
        else:
            missing_count += 1
            print(f"  ✗ Missing")
            if download_missing:
                print(f"     Would download to: {cache_dir / (image_hash + ext)}")
    
    # Rewrite HTML
    rewritten = content
    for url, local_path in url_to_local.items():
        # Replace both http:// and // versions
        rewritten = rewritten.replace(url, local_path)
        rewritten = rewritten.replace(url.replace('https://', '//'), local_path)
    
    # Write rewritten HTML
    output_path.write_text(rewritten, encoding='utf-8')
    
    print(f"\n" + "=" * 70)
    print(f"Rewritten HTML: {output_path}")
    print(f"Images found locally: {len(url_to_local)}")
    print(f"Images missing: {missing_count}")
    print("=" * 70)
    
    return output_path, url_to_local


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rewrite imageboard HTML to use local cached images"
    )
    parser.add_argument(
        "html_file",
        type=Path,
        help="Path to cached HTML file"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache/imageboard/images"),
        help="Directory containing cached images"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for rewritten HTML (default: <input>_local.html)"
    )
    parser.add_argument(
        "--download-missing",
        action="store_true",
        help="Download missing images to cache"
    )
    
    args = parser.parse_args()
    
    if not args.html_file.exists():
        print(f"Error: HTML file not found: {args.html_file}")
        return 1
    
    rewrite_html_with_local_images(
        args.html_file,
        args.cache_dir,
        args.output,
        args.download_missing
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
