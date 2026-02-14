#!/usr/bin/env python3
"""Find duplicate images in assets that exist in cache."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_image_cache import compute_sha256, find_in_imageboard_cache


def find_duplicates(assets_dir: Path, cache_dir: Path) -> list[tuple[Path, Path]]:
    """Find all duplicates and return list of (asset_path, cache_path)."""
    if not assets_dir.exists():
        print(f"ERROR: Assets directory not found: {assets_dir}")
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.webm', '.mp4'}
    duplicates = []
    
    print(f"Scanning {assets_dir} for duplicates...")
    print(f"Images to check: {len(list(assets_dir.iterdir()))}")
    print()
    
    for i, image_path in enumerate(sorted(assets_dir.iterdir()), 1):
        if not image_path.is_file() or image_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            if i % 10 == 0:
                print(f"Progress: {i} files checked... ({len(duplicates)} duplicates found)")
            
            sha256 = compute_sha256(image_path)
            cached_path = find_in_imageboard_cache(cache_dir, sha256)
            
            if cached_path:
                duplicates.append((image_path, cached_path))
                
        except Exception as e:
            print(f"ERROR processing {image_path.name}: {e}")
    
    print()
    return duplicates


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Find duplicate images in assets")
    parser.add_argument("--assets-dir", type=str, default="/home/jovyan/assets", help="Assets directory")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Cache directory")
    parser.add_argument("--cleanup", action="store_true", help="Remove duplicate files from assets")
    
    args = parser.parse_args()
    
    assets_dir = Path(args.assets_dir)
    cache_dir = Path(args.cache_dir)
    
    print("=" * 80)
    print("DUPLICATE IMAGE FINDER")
    print("=" * 80)
    print(f"Assets dir: {assets_dir}")
    print(f"Cache dir: {cache_dir}")
    print("=" * 80)
    print()
    
    duplicates = find_duplicates(assets_dir, cache_dir)
    
    print("=" * 80)
    print(f"FOUND {len(duplicates)} DUPLICATES")
    print("=" * 80)
    print()
    
    if duplicates:
        print("Duplicates (asset -> cache):")
        print("-" * 80)
        for asset_path, cache_path in duplicates:
            print(f"{asset_path.name}")
            print(f"  -> {cache_path}")
            print()
        
        if args.cleanup:
            print("=" * 80)
            print("CLEANUP MODE: Removing duplicates from assets...")
            print("=" * 80)
            print()
            
            removed = 0
            for asset_path, cache_path in duplicates:
                try:
                    asset_path.unlink()
                    print(f"✓ Removed: {asset_path.name}")
                    removed += 1
                except Exception as e:
                    print(f"✗ Failed to remove {asset_path.name}: {e}")
            
            print()
            print(f"Removed {removed} duplicate files from assets")
    else:
        print("No duplicates found!")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
