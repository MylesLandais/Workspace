#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.model_image_cache import get_model_image_cache

def test_cache():
    print("Testing ModelImageCache...")
    
    cache = get_model_image_cache()
    
    print(f"Bucket: {cache.bucket_name}")
    print(f"Cache TTL: {cache.cache_ttl} hours")
    print(f"Local fallback: {cache.use_local_fallback}")
    print()
    
    # Get stats
    stats = cache.get_stats()
    print("Cache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Test with sample image URL
    test_url = "https://i.redd.it/example.jpg"
    print(f"Testing cache with URL: {test_url}")
    
    is_cached, location = cache.is_cached(test_url)
    print(f"  Is cached: {is_cached}")
    if location:
        print(f"  Location: {location}")

if __name__ == "__main__":
    test_cache()
