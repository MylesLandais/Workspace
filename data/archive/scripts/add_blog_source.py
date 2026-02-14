#!/usr/bin/env python3
"""
Feed Discovery Tool.

Auto-discovers RSS/Atom feeds from a given URL and verifies them 
using the internal BlogAdapter.
"""

import sys
import argparse
import requests
from urllib.parse import urljoin, urlparse
from typing import Optional, List
from pathlib import Path
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.blog import BlogAdapter


class FeedDiscoverer:
    """Discovers and verifies RSS/Atom feeds from web pages."""

    COMMON_FEED_PATHS = [
        '/rss', 
        '/feed', 
        '/atom.xml', 
        '/rss.xml', 
        '/blog/rss', 
        '/blog/feed',
        '/index.xml'
    ]

    def __init__(self):
        """Initialize the discoverer with standard headers."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FeedBot/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

    def discover(self, url: str) -> Optional[str]:
        """
        Discover RSS/Atom feed from a URL.

        Args:
            url: The website URL to scan.

        Returns:
            The discovered feed URL or None.
        """
        print(f"\n🔍 Discovering feed for: {url}")
        print("=" * 70)
        
        try:
            # 1. Check HTML head tags
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            feed_links = soup.find_all('link', rel='alternate')
            
            candidates = []
            for link in feed_links:
                type_attr = link.get('type', '').lower()
                if any(t in type_attr for t in ['rss', 'atom', 'xml']):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        candidates.append(full_url)
            
            if candidates:
                print(f"✅ Found {len(candidates)} feed candidate(s) in HTML head:")
                for c in candidates:
                    print(f"  - {c}")
                return candidates[0] 
                
            # 2. Check common paths
            print("⚠️  No feed links found in HTML head. Checking common paths...")
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            
            for path in self.COMMON_FEED_PATHS:
                candidate = urljoin(base, path)
                try:
                    r = requests.head(candidate, headers=self.headers, timeout=5)
                    content_type = r.headers.get('Content-Type', '').lower()
                    if r.status_code == 200 and ('xml' in content_type or 'rss' in content_type):
                        print(f"✅ Found feed at common path: {candidate}")
                        return candidate
                except requests.RequestException:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"❌ Error during discovery: {e}")
            return None

    def verify(self, feed_url: str) -> bool:
        """
        Verify the feed using the internal BlogAdapter.

        Args:
            feed_url: The feed URL to verify.

        Returns:
            True if valid posts are found, False otherwise.
        """
        print(f"\n🧪 Verifying feed: {feed_url}")
        print("=" * 70)
        
        adapter = BlogAdapter(mock=False)
        
        try:
            posts, _ = adapter.fetch_posts(feed_url, limit=5)
            
            if not posts:
                print("❌ Fetched 0 posts. Feed might be empty or invalid.")
                return False
                
            print(f"✅ Successfully fetched {len(posts)} posts:")
            for i, post in enumerate(posts, 1):
                print(f"  {i}. {post.title}")
                print(f"     Date: {post.created_utc}")
                print(f"     URL: {post.url}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error verifying feed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Add a new blog source to the poller")
    parser.add_argument("url", help="URL of the blog/site to add")
    
    args = parser.parse_args()
    
    discoverer = FeedDiscoverer()
    
    # 1. Discover Feed
    feed_url = discoverer.discover(args.url)
    
    if feed_url:
        print(f"\n🎉 DISCOVERY SUCCESS: Found feed at {feed_url}")
        
        # 2. Verify Feed
        if discoverer.verify(feed_url):
            print("\n" + "=" * 70)
            print(f"✅ VALIDATION PASSED")
            print(f"To add this domain to the poller, use this feed URL:")
            print(f"  {feed_url}")
            print("=" * 70)
        else:
            print(f"\n❌ VALIDATION FAILED: Feed found at {feed_url} but could not be parsed.")
    else:
        print("\n" + "=" * 70)
        print("❌ DISCOVERY FAILED: No RSS/Atom feed found.")
        print("=" * 70)
        print("You MUST generate an internal provider to monitor this page.")
        print("See src/feed/platforms/blog.py for reference.")


if __name__ == "__main__":
    main()
