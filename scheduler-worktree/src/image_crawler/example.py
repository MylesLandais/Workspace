"""Example usage of the image crawler."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from image_crawler import MasterCrawler
from image_crawler.platforms import RedditCrawler


def main():
    """Example crawler usage."""
    print("Initializing image crawler...")

    crawler = MasterCrawler(
        num_workers=2,
        face_similarity_threshold=0.65,
    )

    print("Adding Reddit crawler...")
    reddit_crawler = RedditCrawler(
        subreddit="BrookeMonk",
        check_interval=1800,
        mock=False,
    )
    crawler.add_platform_crawler(reddit_crawler)

    print("Starting crawler...")
    print("Press Ctrl+C to stop")

    try:
        crawler.run(max_urls=100, max_duration=300)
    except KeyboardInterrupt:
        print("\nStopping crawler...")

    stats = crawler.get_stats()
    print(f"\nCrawler stats: {stats}")


if __name__ == "__main__":
    main()








