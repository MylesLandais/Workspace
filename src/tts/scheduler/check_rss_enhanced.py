#!/usr/bin/env python3
"""
RSS Feed Checker - Alternative approach for Cloudflare-protected feeds
Uses requests with enhanced headers and cookie handling.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import requests
import feedparser
from bs4 import BeautifulSoup

from src.feed.storage.neo4j_connection import get_connection


class EnhancedRSSChecker:
    """
    Enhanced RSS checker with better headers and session management.
    May work with some Cloudflare-protected feeds.
    """

    def __init__(self):
        self.session = requests.Session()
        # Use realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

    def check_feed(self, feed_url: str, since: Optional[datetime] = None) -> dict:
        """
        Check RSS feed for new posts.

        Args:
            feed_url: RSS feed URL
            since: Only return posts after this datetime

        Returns:
            Dictionary with stats and posts
        """
        print(f"\n📬 Checking RSS inbox: {feed_url}")
        print("=" * 70)

        try:
            # First, try to visit the main site to get cookies
            print("  🔄 Attempting to access main site...")
            main_url = feed_url.replace('/feed/', '/')
            try:
                main_response = self.session.get(main_url, timeout=15)
                print(f"     Main site: {main_response.status_code}")
            except:
                print("     Could not access main site, trying feed directly...")

            # Now try to fetch the feed
            print("  🔄 Fetching RSS feed...")
            response = self.session.get(feed_url, timeout=15)
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.content)

            if feed.bozo and feed.bozo_exception:
                print(f"  ⚠️  Feed parsing warning: {feed.bozo_exception}")

            entries = feed.entries

            if not entries:
                print("  ❌ No entries found in feed")
                return {'total': 0, 'new': 0, 'posts': []}

            # Process entries
            posts = []
            new_count = 0

            for entry in entries:
                post_url = entry.get('link', '')
                title = entry.get('title', '')
                description = entry.get('description', '')
                published_parsed = entry.get('published_parsed')

                # Parse published date
                published_date = None
                if published_parsed:
                    try:
                        published_date = datetime(*published_parsed[:6])
                    except:
                        pass

                # Check if new
                is_new = True
                if since and published_date:
                    is_new = published_date > since

                if is_new:
                    new_count += 1

                post = {
                    'title': title,
                    'url': post_url,
                    'published': published_date,
                    'description': description,
                    'is_new': is_new,
                }
                posts.append(post)

            # Display results
            print(f"  ✅ Total posts in feed: {len(posts)}")
            print(f"  🆕 New posts (since {since}): {new_count}")
            print("=" * 70)

            # List new posts
            if new_count > 0:
                print("\n📰 New Posts:")
                for i, post in enumerate(posts, 1):
                    if post['is_new']:
                        print(f"\n  {i}. {post['title']}")
                        print(f"     URL: {post['url']}")
                        if post['published']:
                            print(f"     Published: {post['published'].strftime('%Y-%m-%d %H:%M:%S')}")

            return {
                'total': len(posts),
                'new': new_count,
                'posts': posts,
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"  ❌ Error: 403 Forbidden - site protected by Cloudflare")
                print(f"  💡 Alternative: Use BlogAdapter with mock mode for testing")
                print(f"  💡 Alternative: Set up browser automation with Playwright (requires system libraries)")
            else:
                print(f"  ❌ HTTP Error: {e}")
            return {'total': 0, 'new': 0, 'posts': []}
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {'total': 0, 'new': 0, 'posts': []}

    def save_to_database(self, posts: list, subreddit: str = "femdom-pov") -> int:
        """
        Save posts to Neo4j database.

        Args:
            posts: List of post dictionaries
            subreddit: Subreddit/feed name

        Returns:
            Number of posts saved
        """
        try:
            neo4j = get_connection()
            saved_count = 0

            for post in posts:
                if not post['is_new']:
                    continue

                # Create post node
                query = """
                MERGE (p:Post {url: $url})
                SET p.title = $title,
                    p.selftext = $content,
                    p.created_utc = $created_utc,
                    p.score = 0,
                    p.num_comments = 0,
                    p.upvote_ratio = 0.0,
                    p.over_18 = false
                WITH p
                MERGE (s:Subreddit {name: $subreddit})
                MERGE (p)-[:POSTED_IN]->(s)
                """

                neo4j.execute_write(query, parameters={
                    'url': post['url'],
                    'title': post['title'],
                    'content': post.get('description', ''),
                    'created_utc': post['published'] or datetime.utcnow(),
                    'subreddit': subreddit,
                })

                saved_count += 1

            print(f"\n💾 Saved {saved_count} posts to database")
            return saved_count

        except Exception as e:
            print(f"  ❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="Check RSS inbox with enhanced headers"
    )
    parser.add_argument(
        "--feed-url",
        default="https://femdom-pov.me/feed/",
        help="RSS feed URL to check"
    )
    parser.add_argument(
        "--since",
        help="Only show posts after this date (YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save new posts to database"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use BlogAdapter mock mode (for testing)"
    )

    args = parser.parse_args()

    # Parse since date
    since_date = None
    if args.since:
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Invalid date format: {args.since}. Use YYYY-MM-DD HH:MM:SS")
            return 1

    if args.mock:
        # Use mock mode
        print("\n🧪 Using mock mode (BlogAdapter)")
        from src.feed.platforms.blog import BlogAdapter

        adapter = BlogAdapter(mock=True)
        posts, _ = adapter.fetch_posts(args.feed_url, limit=10)

        print(f"\n📊 Mock Results:")
        print(f"  Total posts: {len(posts)}")

        for i, post in enumerate(posts, 1):
            print(f"\n  {i}. {post.title}")
            print(f"     URL: {post.url}")
            print(f"     Created: {post.created_utc}")

        return 0

    # Initialize checker
    checker = EnhancedRSSChecker()

    # Check for new posts
    result = checker.check_feed(
        feed_url=args.feed_url,
        since=since_date,
    )

    # Save to database if requested
    if args.save and result['new'] > 0:
        checker.save_to_database(result['posts'])

    # Summary
    print("\n" + "=" * 70)
    print(f"📊 Summary: {result['new']} new posts out of {result['total']} total")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
