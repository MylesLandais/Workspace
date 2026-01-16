#!/usr/bin/env python3
"""Test image similarity and caching for deduplicating images."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.image_dedup.deduplicator import ImageDeduplicator
from src.image_dedup.models import IngestRequest


def test_image_similarity(image_path: Path, cache_dir: Path) -> dict:
    """Test if an image exists in cache using image deduplication."""
    if not image_path.exists():
        return {
            "found": False,
            "error": f"Image not found: {image_path}"
        }
    
    try:
        deduplicator = ImageDeduplicator(
            storage_path=str(cache_dir / "storage"),
            enable_clip=False,
        )
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        request = IngestRequest(
            image_bytes=image_bytes,
            post_id=None,
            metadata={"source_path": str(image_path)}
        )
        
        response = deduplicator.ingest_image(request)
        
        return {
            "found": response.is_duplicate,
            "is_repost": response.is_repost,
            "confidence": response.confidence,
            "method": response.matched_method,
            "image_id": response.image_id,
            "cluster_id": response.cluster_id,
            "sha256": response.hashes.sha256,
        }
        
    except Exception as e:
        return {
            "found": False,
            "error": str(e)
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test image similarity and caching")
    parser.add_argument("image_path", type=str, help="Path to image to test")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Cache directory (default: cache)")
    
    args = parser.parse_args()
    
    image_path = Path(args.image_path)
    cache_dir = Path(args.cache_dir)
    
    print("=" * 80)
    print("IMAGE SIMILARITY AND CACHING TEST")
    print("=" * 80)
    print(f"Testing: {image_path}")
    print(f"Cache dir: {cache_dir}")
    print("=" * 80)
    print()
    
    result = test_image_similarity(image_path, cache_dir)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return 1
    
    if result["found"]:
        print(f"✓ Image FOUND in cache!")
        print(f"  - Method: {result['method']}")
        print(f"  - Confidence: {result['confidence']}")
        print(f"  - SHA256: {result['sha256']}")
        print(f"  - Image ID: {result['image_id']}")
        print(f"  - Cluster ID: {result['cluster_id']}")
        print(f"  - Is Repost: {result['is_repost']}")
    else:
        print("✗ Image NOT FOUND in cache")
        print(f"  - SHA256: {result['sha256']}")
        print(f"  - Image ID: {result['image_id']}")
        print(f"  - Cluster ID: {result['cluster_id']}")
    
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
