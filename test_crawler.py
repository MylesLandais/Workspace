#!/usr/bin/env python3
"""Test script for the modular Reddit crawler."""

import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from feed.crawler.reddit_crawler import RedditCrawler, CrawlerConfig


# Test subreddits (small list for quick testing)
TEST_SUBREDDITS = [
    "TaylorSwift",
    "TaylorSwiftPictures",
    "TaylorSwiftCandids",
]


def test_crawler_dry_run():
    """Test crawler in dry-run mode (no database writes)."""
    print("=" * 80)
    print("TEST: Dry-run mode (no database writes)")
    print("=" * 80)
    
    config = CrawlerConfig(
        subreddits=TEST_SUBREDDITS,
        request_delay_min=1.0,
        request_delay_max=2.0,
        subreddit_delay_min=2.0,
        subreddit_delay_max=3.0,
        cycle_delay_min=1.0,
        cycle_delay_max=2.0,
        step_delay_min=0.5,
        step_delay_max=1.0,
        max_pages=1,
        limit_per_page=10,
        max_cycles=1,
        dry_run=True,
        mock=False,
    )
    
    crawler = RedditCrawler(config)
    crawler.run()
    
    print("\nTest completed successfully!")


def test_crawler_mock():
    """Test crawler with mock data."""
    print("=" * 80)
    print("TEST: Mock mode (using mock data)")
    print("=" * 80)
    
    config = CrawlerConfig(
        subreddits=TEST_SUBREDDITS,
        request_delay_min=0.1,
        request_delay_max=0.2,
        subreddit_delay_min=0.1,
        subreddit_delay_max=0.2,
        cycle_delay_min=0.1,
        cycle_delay_max=0.2,
        step_delay_min=0.1,
        step_delay_max=0.2,
        max_pages=1,
        limit_per_page=5,
        max_cycles=1,
        dry_run=True,
        mock=True,
    )
    
    crawler = RedditCrawler(config)
    crawler.run()
    
    print("\nTest completed successfully!")


def test_crawler_production():
    """Test crawler in production mode (with database)."""
    print("=" * 80)
    print("TEST: Production mode (with database writes)")
    print("=" * 80)
    
    config = CrawlerConfig(
        subreddits=TEST_SUBREDDITS,
        request_delay_min=2.0,
        request_delay_max=5.0,
        subreddit_delay_min=5.0,
        subreddit_delay_max=10.0,
        cycle_delay_min=10.0,
        cycle_delay_max=20.0,
        step_delay_min=1.0,
        step_delay_max=2.0,
        max_pages=1,
        limit_per_page=10,
        max_cycles=1,
        dry_run=False,
        mock=False,
    )
    
    crawler = RedditCrawler(config)
    crawler.run()
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Reddit crawler")
    parser.add_argument(
        "--mode",
        choices=["dry-run", "mock", "production"],
        default="dry-run",
        help="Test mode (default: dry-run)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "dry-run":
            test_crawler_dry_run()
        elif args.mode == "mock":
            test_crawler_mock()
        elif args.mode == "production":
            test_crawler_production()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

