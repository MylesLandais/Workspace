#!/usr/bin/env python3
"""
Feed Manager for Universal Feed Reader.
Handles discovery, validation, and management of RSS/Atom feeds.
"""

import sys
import os
import json
import argparse
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional, List, Dict

# Third-party imports
try:
    import requests
    from bs4 import BeautifulSoup
    import feedparser
except ImportError as e:
    print(f"Error: Missing dependency {e.name}. Please ensure requests, beautifulsoup4, and feedparser are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

FEEDS_FILE = "feeds.json"

class FeedManager:
    def __init__(self, storage_file: str = FEEDS_FILE):
        self.storage_file = storage_file
        self.feeds = self._load_feeds()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def _load_feeds(self) -> List[Dict]:
        """Load feeds from JSON storage."""
        if not os.path.exists(self.storage_file):
            return []
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding {self.storage_file}. Starting with empty list.")
            return []

    def _save_feeds(self):
        """Save feeds to JSON storage."""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.feeds, f, indent=2)

    def discover_feed(self, url: str) -> Optional[str]:
        """
        Attempt to discover a valid RSS/Atom feed URL from a given website URL.
        """
        logger.info(f"Discovering feed for: {url}")
        
        # 1. Try the URL directly (in case it IS a feed)
        if self._validate_feed(url):
            return url

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

        # 2. Parse HTML for <link> tags
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for standard feed discovery tags
        feed_links = soup.find_all('link', rel=['alternate', 'feed'])
        
        candidates = []
        for link in feed_links:
            if link.get('type') in ['application/rss+xml', 'application/atom+xml', 'text/xml']:
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    candidates.append(full_url)

        # 3. Try common paths if no tags found
        if not candidates:
            common_suffixes = ['/feed', '/feed/', '/rss', '/rss/', '/atom.xml', '/feed.xml']
            # Remove trailing slash from base url for clean joining
            base_url = url.rstrip('/')
            for suffix in common_suffixes:
                candidates.append(base_url + suffix)

        # 4. Validate candidates
        for candidate in candidates:
            logger.info(f"Checking candidate: {candidate}")
            if self._validate_feed(candidate):
                logger.info(f"Found valid feed: {candidate}")
                return candidate

        logger.warning("No valid feed found.")
        return None

    def _validate_feed(self, url: str) -> bool:
        """Check if a URL points to a valid RSS/Atom feed."""
        try:
            # We use feedparser to parse. It can handle HTTP URLs directly.
            # But strictly, we might want to fetch first to handle errors gracefully.
            parsed = feedparser.parse(url)
            
            # bozo bit indicates parsing error, but often feeds are malformed but usable.
            # We check if it has entries or a title to confirm it's somewhat valid.
            if hasattr(parsed, 'feed') and (hasattr(parsed.feed, 'title') or len(parsed.entries) > 0):
                return True
            if parsed.version: # valid version detected
                return True
            
        except Exception as e:
            logger.debug(f"Validation failed for {url}: {e}")
        
        return False

    def add_feed(self, url: str) -> bool:
        """Add a new feed by URL (discovering if necessary)."""
        feed_url = self.discover_feed(url)
        if not feed_url:
            print(f"❌ Could not find a valid feed for {url}")
            return False

        # Check for duplicates
        if any(f['url'] == feed_url for f in self.feeds):
            print(f"⚠️  Feed already exists: {feed_url}")
            return True

        # Get Feed Info
        try:
            parsed = feedparser.parse(feed_url)
            title = parsed.feed.get('title', url)
            
            feed_data = {
                'url': feed_url,
                'title': title,
                'original_url': url,
                'added_at': os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip()
            }
            
            self.feeds.append(feed_data)
            self._save_feeds()
            print(f"✅ Added feed: {title} ({feed_url})")
            return True
        except Exception as e:
            logger.error(f"Error adding feed {feed_url}: {e}")
            return False

    def list_feeds(self):
        """List all subscribed feeds."""
        if not self.feeds:
            print("No feeds subscribed.")
            return

        print(f"\nSubscribed Feeds ({len(self.feeds)}):")
        print("-" * 60)
        for i, feed in enumerate(self.feeds, 1):
            print(f"{i}. {feed['title']}")
            print(f"   Source: {feed['original_url']}")
            print(f"   Feed:   {feed['url']}")
            print("-" * 60)

    def remove_feed(self, index: int) -> bool:
        """Remove a feed by index (1-based)."""
        if index < 1 or index > len(self.feeds):
            print("❌ Invalid feed index.")
            return False
        
        removed = self.feeds.pop(index - 1)
        self._save_feeds()
        print(f"🗑️  Removed feed: {removed['title']}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Feed Manager for Universal Feed Reader")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new feed')
    add_parser.add_argument('url', help='Website URL or Feed URL')

    # List command
    subparsers.add_parser('list', help='List subscribed feeds')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a feed')
    remove_parser.add_argument('index', type=int, help='Index of feed to remove (from list)')

    args = parser.parse_args()
    
    manager = FeedManager()

    if args.command == 'add':
        manager.add_feed(args.url)
    elif args.command == 'list':
        manager.list_feeds()
    elif args.command == 'remove':
        manager.remove_feed(args.index)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
