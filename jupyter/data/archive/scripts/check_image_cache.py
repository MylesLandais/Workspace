#!/usr/bin/env python3
"""Check if an image exists in the cache."""

import hashlib
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def find_in_imageboard_cache(cache_dir: Path, sha256: str) -> Path | None:
    """Find image in imageboard cache (checks both symlinks and actual files)."""
    images_dir = cache_dir / "imageboard" / "images"
    
    # Check symlink in flat directory
    symlink_path = images_dir / sha256
    if symlink_path.exists():
        return symlink_path
    
    # Search for actual file with matching SHA256 in subdirectories
    for file_path in images_dir.rglob("*"):
        if file_path.is_file() and file_path.stat().st_size > 0:
            try:
                file_sha256 = compute_sha256(file_path)
                if file_sha256 == sha256:
                    return file_path
            except Exception:
                continue
    
    return None


def check_cache(image_path: Path, cache_dir: Path) -> bool:
    """Check if image exists in cache."""
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        return False
    
    print(f"Computing SHA256 for: {image_path}")
    sha256 = compute_sha256(image_path)
    print(f"SHA256: {sha256}")
    
    # Check in reddit cache
    reddit_path = cache_dir / "reddit" / "images" / sha256
    if reddit_path.exists():
        print(f"FOUND: Image exists in Reddit cache at {reddit_path}")
        return True
    
    # Check in imageboard cache
    imageboard_path = find_in_imageboard_cache(cache_dir, sha256)
    if imageboard_path:
        print(f"FOUND: Image exists in imageboard cache at {imageboard_path}")
        return True
    
    print("NOT FOUND: Image does not exist in cache")
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: check_image_cache.py <image_path> [cache_dir]")
        print("Example: docker compose exec jupyterlab python check_image_cache.py /home/jovyan/assets/image.jpg /home/jovyan/workspaces/cache")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    cache_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./cache")
    
    check_cache(image_path, cache_dir)


if __name__ == "__main__":
    main()
