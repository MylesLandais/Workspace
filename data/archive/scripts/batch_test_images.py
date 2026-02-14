#!/usr/bin/env python3
"""Batch test image similarity and caching for multiple images."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_image_cache import compute_sha256, find_in_imageboard_cache


def batch_test_assets(assets_dir: Path, cache_dir: Path) -> None:
    """Test all images in assets directory."""
    if not assets_dir.exists():
        print(f"ERROR: Assets directory not found: {assets_dir}")
        return
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.webm', '.mp4'}
    
    found_count = 0
    not_found_count = 0
    error_count = 0
    
    print("=" * 80)
    print("BATCH IMAGE SIMILARITY AND CACHING TEST")
    print("=" * 80)
    print(f"Assets dir: {assets_dir}")
    print(f"Cache dir: {cache_dir}")
    print("=" * 80)
    print()
    
    for image_path in sorted(assets_dir.iterdir()):
        if image_path.is_file() and image_path.suffix.lower() in image_extensions:
            try:
                sha256 = compute_sha256(image_path)
                cached_path = find_in_imageboard_cache(cache_dir, sha256)
                
                if cached_path:
                    print(f"✓ FOUND: {image_path.name}")
                    print(f"  SHA256: {sha256}")
                    print(f"  Cached: {cached_path}")
                    print()
                    found_count += 1
                else:
                    print(f"✗ NOT FOUND: {image_path.name}")
                    print(f"  SHA256: {sha256}")
                    print()
                    not_found_count += 1
                    
            except Exception as e:
                print(f"✗ ERROR: {image_path.name}")
                print(f"  Error: {e}")
                print()
                error_count += 1
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Found in cache: {found_count}")
    print(f"Not found: {not_found_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {found_count + not_found_count + error_count}")
    print("=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch test image similarity and caching")
    parser.add_argument("--assets-dir", type=str, default="/home/jovyan/assets", help="Assets directory (default: /home/jovyan/assets)")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Cache directory (default: cache)")
    
    args = parser.parse_args()
    
    assets_dir = Path(args.assets_dir)
    cache_dir = Path(args.cache_dir)
    
    batch_test_assets(assets_dir, cache_dir)


if __name__ == "__main__":
    main()
