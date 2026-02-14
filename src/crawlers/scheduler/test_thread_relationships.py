#!/usr/bin/env python3
"""Test script for thread relationship extraction."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.utils.reddit_url_extractor import extract_reddit_urls, parse_reddit_url


def test_url_extraction():
    """Test URL extraction from various text formats."""
    
    test_cases = [
        {
            "name": "Full new Reddit URL",
            "text": "Check out this thread: https://www.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/",
            "expected_count": 1,
        },
        {
            "name": "Old Reddit URL",
            "text": "See https://old.reddit.com/r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/",
            "expected_count": 1,
        },
        {
            "name": "Relative permalink",
            "text": "Discussion here: /r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/",
            "expected_count": 1,
        },
        {
            "name": "Multiple URLs",
            "text": """
            Original: https://www.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/
            Discussion: /r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/
            """,
            "expected_count": 2,
        },
        {
            "name": "URL in markdown link",
            "text": "See [this thread](https://www.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/)",
            "expected_count": 1,
        },
        {
            "name": "URL with query params",
            "text": "https://www.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/?context=3",
            "expected_count": 1,
        },
    ]
    
    print("Testing URL Extraction")
    print("=" * 80)
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Text: {test_case['text'][:80]}...")
        
        urls = extract_reddit_urls(test_case['text'])
        
        print(f"Found {len(urls)} URL(s)")
        for url_info in urls:
            print(f"  - Post ID: {url_info.get('post_id')}")
            print(f"    Subreddit: {url_info.get('subreddit')}")
            print(f"    Permalink: {url_info.get('permalink')}")
        
        if len(urls) != test_case['expected_count']:
            print(f"  FAILED: Expected {test_case['expected_count']}, got {len(urls)}")
            all_passed = False
        else:
            print(f"  PASSED")
    
    print("\n" + "=" * 80)
    print("Testing URL Parsing")
    print("=" * 80)
    
    parse_tests = [
        {
            "url": "https://www.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/",
            "expected_post_id": "1ptxm3x",
            "expected_subreddit": "LocalLLaMA",
        },
        {
            "url": "/r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/",
            "expected_post_id": "1pu1nx1",
            "expected_subreddit": "SillyTavernAI",
        },
        {
            "url": "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/",
            "expected_post_id": "1ptxm3x",
            "expected_subreddit": "LocalLLaMA",
        },
    ]
    
    for test in parse_tests:
        print(f"\nParsing: {test['url']}")
        parsed = parse_reddit_url(test['url'])
        
        if parsed:
            print(f"  Post ID: {parsed.get('post_id')} (expected: {test['expected_post_id']})")
            print(f"  Subreddit: {parsed.get('subreddit')} (expected: {test['expected_subreddit']})")
            
            if parsed.get('post_id') == test['expected_post_id'] and parsed.get('subreddit') == test['expected_subreddit']:
                print(f"  PASSED")
            else:
                print(f"  FAILED")
                all_passed = False
        else:
            print(f"  FAILED: Could not parse URL")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("All tests PASSED")
    else:
        print("Some tests FAILED")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = test_url_extraction()
    sys.exit(0 if success else 1)







