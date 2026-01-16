#!/usr/bin/env python3
"""Fast duplicate finder using cache symlinks."""

import sys
import hashlib
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):  # Larger chunks
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_cache_hashes(cache_dir: Path) -> set[str]:
    """Get all SHA256 hashes from cache symlinks."""
    images_dir = cache_dir / "imageboard" / "images"
    hashes = set()
    
    print(f"Reading cache symlinks from {images_dir}...")
    if images_dir.exists():
        for item in images_dir.iterdir():
            if item.is_symlink() or item.is_file():
                try:
                    # Symlink name or filename is the SHA256 (with optional extension)
                    sha256 = item.stem
                    if len(sha256) == 64:  # SHA256 hex string length
                        hashes.add(sha256)
                except Exception:
                    pass
    
    print(f"Found {len(hashes)} hashes in cache")
    return hashes


def find_duplicates(assets_dir: Path, cache_hashes: set[str]) -> list[Path]:
    """Find duplicate images by comparing SHA256."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.webm', '.mp4'}
    duplicates = []
    
    print(f"\nScanning {assets_dir} for duplicates...")
    
    for i, image_path in enumerate(sorted(assets_dir.iterdir()), 1):
        if not image_path.is_file() or image_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            if i % 50 == 0:
                print(f"Progress: {i} files checked... ({len(duplicates)} duplicates found)")
            
            sha256 = compute_sha256(image_path)
            
            if sha256 in cache_hashes:
                duplicates.append(image_path)
                
        except Exception as e:
            print(f"ERROR processing {image_path.name}: {e}")
    
    print()
    return duplicates


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast duplicate finder")
    parser.add_argument("--assets-dir", type=str, default="/home/jovyan/assets", help="Assets directory")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Cache directory")
    parser.add_argument("--cleanup", action="store_true", help="Remove duplicate files from assets")
    
    args = parser.parse_args()
    
    assets_dir = Path(args.assets_dir)
    cache_dir = Path(args.cache_dir)
    
    print("=" * 80)
    print("FAST DUPLICATE IMAGE FINDER")
    print("=" * 80)
    print(f"Assets dir: {assets_dir}")
    print(f"Cache dir: {cache_dir}")
    print("=" * 80)
    print()
    
    cache_hashes = get_cache_hashes(cache_dir)
    duplicates = find_duplicates(assets_dir, cache_hashes)
    
    print("=" * 80)
    print(f"FOUND {len(duplicates)} DUPLICATES")
    print("=" * 80)
    print()
    
    if duplicates:
        print("Duplicate files:")
        print("-" * 80)
        for dup in duplicates:
            sha256 = compute_sha256(dup)
            cache_path = cache_dir / "imageboard" / "images" / f"{sha256}.jpg"
            if not cache_path.exists():
                cache_path = cache_dir / "imageboard" / "images" / f"{sha256}.png"
            print(f"{dup.name}")
            print(f"  SHA256: {sha256}")
            print(f"  Cache: {cache_path}")
            print()
        
        if args.cleanup:
            print("=" * 80)
            print("CLEANUP MODE: Removing duplicates from assets...")
            print("=" * 80)
            print()
            
            removed = 0
            for dup in duplicates:
                try:
                    dup.unlink()
                    print(f"✓ Removed: {dup.name}")
                    removed += 1
                except Exception as e:
                    print(f"✗ Failed to remove {dup.name}: {e}")
            
            print()
            print(f"Removed {removed} duplicate files from assets")
    else:
        print("No duplicates found!")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
