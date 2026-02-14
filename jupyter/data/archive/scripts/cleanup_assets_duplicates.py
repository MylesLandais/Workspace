#!/usr/bin/env python3
"""
Periodic duplicate image cleanup from assets folder.

This script finds and removes duplicate images from the assets folder
that already exist in the cache. This is safe to run periodically
as it only removes duplicates from assets, not from the cache.
"""

import sys
import hashlib
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_cache_hashes(cache_dir: Path) -> set[str]:
    """Get all SHA256 hashes from cache symlinks."""
    images_dir = cache_dir / "imageboard" / "images"
    hashes = set()
    
    if not images_dir.exists():
        return hashes
    
    for item in images_dir.iterdir():
        if item.is_symlink() or item.is_file():
            try:
                sha256 = item.stem
                if len(sha256) == 64:  # SHA256 hex string length
                    hashes.add(sha256)
            except Exception:
                pass
    
    return hashes


def find_and_remove_duplicates(
    assets_dir: Path,
    cache_dir: Path,
    dry_run: bool = True
) -> dict:
    """
    Find and optionally remove duplicate images from assets.
    
    Args:
        assets_dir: Path to assets directory
        cache_dir: Path to cache directory
        dry_run: If True, only report what would be removed
    
    Returns:
        Dictionary with statistics
    """
    if not assets_dir.exists():
        return {
            "status": "error",
            "error": f"Assets directory not found: {assets_dir}",
            "duplicates_found": 0,
            "duplicates_removed": 0,
            "space_freed": 0
        }
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.webm', '.mp4'}
    cache_hashes = get_cache_hashes(cache_dir)
    duplicates = []
    total_size_freed = 0
    
    for image_path in sorted(assets_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            sha256 = compute_sha256(image_path)
            
            if sha256 in cache_hashes:
                file_size = image_path.stat().st_size
                duplicates.append((image_path, sha256, file_size))
                total_size_freed += file_size
                
        except Exception as e:
            print(f"ERROR processing {image_path.name}: {e}")
    
    if dry_run:
        print(f"[DRY RUN] Would remove {len(duplicates)} duplicate(s)")
        for dup in duplicates:
            print(f"  - {dup[0].name} ({dup[2]:,} bytes)")
    else:
        print(f"Removing {len(duplicates)} duplicate(s)...")
        for dup in duplicates:
            try:
                dup[0].unlink()
                print(f"  ✓ Removed: {dup[0].name} ({dup[2]:,} bytes)")
            except Exception as e:
                print(f"  ✗ Failed to remove {dup[0].name}: {e}")
    
    return {
        "status": "success",
        "duplicates_found": len(duplicates),
        "duplicates_removed": 0 if dry_run else len(duplicates),
        "space_freed": total_size_freed,
        "dry_run": dry_run
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Periodic duplicate image cleanup from assets folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default, safe)
  python cleanup_assets_duplicates.py --assets-dir /home/jovyan/assets --cache-dir /home/jovyan/workspaces/cache
  
  # Actually remove duplicates
  python cleanup_assets_duplicates.py --assets-dir /home/jovyan/assets --cache-dir /home/jovyan/workspaces/cache --cleanup
  
  # Run as cron job (add cleanup flag in crontab)
  0 2 * * * cd /home/jovyan/workspaces && python cleanup_assets_duplicates.py --cleanup >> /var/log/assets_cleanup.log 2>&1
        """
    )
    parser.add_argument("--assets-dir", type=str, default="/home/jovyan/assets",
                       help="Assets directory (default: /home/jovyan/assets)")
    parser.add_argument("--cache-dir", type=str, default="cache",
                       help="Cache directory (default: cache)")
    parser.add_argument("--cleanup", action="store_true",
                       help="Actually remove duplicates (default: dry run)")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress output (for cron jobs)")
    
    args = parser.parse_args()
    
    assets_dir = Path(args.assets_dir)
    cache_dir = Path(args.cache_dir)
    
    if not args.quiet:
        print("=" * 80)
        print("ASSETS DUPLICATE CLEANUP")
        print("=" * 80)
        print(f"Assets dir: {assets_dir}")
        print(f"Cache dir: {cache_dir}")
        print(f"Mode: {'DRY RUN (no changes)' if not args.cleanup else 'CLEANUP (removing files)'}")
        print("=" * 80)
        print()
    
    result = find_and_remove_duplicates(assets_dir, cache_dir, dry_run=not args.cleanup)
    
    if result["status"] == "error":
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    
    if not args.quiet:
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Duplicates found: {result['duplicates_found']}")
        if args.cleanup:
            print(f"Duplicates removed: {result['duplicates_removed']}")
        if result['space_freed'] > 0:
            size_mb = result['space_freed'] / (1024 * 1024)
            print(f"Space freed: {size_mb:.2f} MB ({result['space_freed']:,} bytes)")
        print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
