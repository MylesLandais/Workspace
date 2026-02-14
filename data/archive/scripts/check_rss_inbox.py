#!/usr/bin/env python3
"""
RSS Feed Checker & Spider for femdom-pov.me
Handles Cloudflare-protected feeds using browser automation and scrapes full page content.
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from playwright.sync_api import sync_playwright, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with: pip install playwright && playwright install chromium")

import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from src.feed.storage.neo4j_connection import get_connection


class CreepyCrawlySpider:
    """
    Spider for crawling full page content from Cloudflare-protected sites.
    Named 'Creepy Crawly' as requested.
    """

    def __init__(self, delay_min: float = 2.0, delay_max: float = 5.0):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.browser: Optional[Browser] = None
        self.context = None
        self.page = None

    def _delay(self):
        """Random delay to appear more human."""
        import random
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def start(self):
        """Start the browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed")

        self.playwright = sync_playwright().start()
        # Use chromium with stealth settings - try headless first
        try:
            # Try to use system chromium first
            self.browser = self.playwright.chromium.launch(
                channel='chrome',
                headless=True,  # Use headless for Docker environment
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
        except:
            # Fall back to bundled chromium
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        self.page = self.context.new_page()
        print("🕷️ Creepy Crawly spider started")

    def stop(self):
        """Stop the browser."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🕷️ Creepy Crawly spider stopped")

    def crawl_page(self, url: str) -> dict:
        """
        Crawl a single page and extract content, images, and metadata.

        Args:
            url: URL to crawl

        Returns:
            Dictionary with 'content', 'images', 'author', 'published_date'
        """
        try:
            self._delay()

            # Navigate to page
            self.page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait for content to load
            time.sleep(2)

            # Get page content
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
                tag.decompose()

            # Try to find main content
            content_selectors = [
                'article',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.post',
                '#content',
                '.post-body',
                '[itemprop="articleBody"]',
            ]

            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                content = soup.find('body')

            # Extract text content
            text_content = content.get_text(separator='\n', strip=True) if content else ''

            # Extract images
            images = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convert to absolute URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        parsed = url.split('/')
                        base_url = '/'.join(parsed[:3])
                        src = base_url + src
                    elif not src.startswith('http'):
                        src = urljoin(url, src)
                    images.append(src)

            # Try to extract author
            author = None
            author_selectors = [
                '.author',
                '.post-author',
                '[rel="author"]',
                '.byline',
                '[itemprop="author"]',
            ]
            for selector in author_selectors:
                elem = soup.select_one(selector)
                if elem:
                    author = elem.get_text(strip=True)
                    break

            # Try to extract published date
            published_date = None
            date_selectors = [
                'time[datetime]',
                '.published',
                '.post-date',
                '[itemprop="datePublished"]',
            ]
            for selector in date_selectors:
                elem = soup.select_one(selector)
                if elem:
                    datetime_attr = elem.get('datetime')
                    if datetime_attr:
                        try:
                            published_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        except:
                            pass

            return {
                'content': text_content,
                'images': images,
                'author': author,
                'published_date': published_date,
                'url': url,
            }

        except Exception as e:
            print(f"  ⚠️  Error crawling {url}: {e}")
            return {
                'content': '',
                'images': [],
                'author': None,
                'published_date': None,
                'url': url,
            }

    def crawl_multiple(self, urls: List[str]) -> List[dict]:
        """
        Crawl multiple pages.

        Args:
            urls: List of URLs to crawl

        Returns:
            List of page data dictionaries
        """
        results = []
        for i, url in enumerate(urls, 1):
            print(f"  🕷️  Crawling {i}/{len(urls)}: {url}")
            result = self.crawl_page(url)
            results.append(result)
        return results


class RSSInboxChecker:
    """
    Check RSS inbox for new posts using Creepy Crawly spider.
    """

    def __init__(self, spider: CreepyCrawlySpider):
        self.spider = spider

    def fetch_feed_via_browser(self, feed_url: str) -> list:
        """
        Fetch RSS feed through browser to bypass Cloudflare.

        Args:
            feed_url: RSS feed URL

        Returns:
            List of feed entries
        """
        try:
            self.spider.page.goto(feed_url, wait_until='networkidle', timeout=30000)
            time.sleep(3)

            # Get the XML content - might be HTML-escaped
            html_content = self.spider.page.content()

            # Extract the actual XML from the pre tag if present
            import html
            if '<pre' in html_content:
                # Content is in a pre tag, extract it
                soup = BeautifulSoup(html_content, 'html.parser')
                pre_tag = soup.find('pre')
                if pre_tag:
                    xml_content = html.unescape(pre_tag.get_text())
                else:
                    xml_content = html_content
            else:
                xml_content = html_content

            # Parse with feedparser
            feed = feedparser.parse(xml_content)

            if feed.bozo and feed.bozo_exception:
                print(f"  ⚠️  Feed parsing warning: {feed.bozo_exception}")

            return feed.entries
        except Exception as e:
            print(f"  ❌ Error fetching feed via browser: {e}")
            return []

    def check_new_posts(
        self,
        feed_url: str,
        since: Optional[datetime] = None,
        scrape_content: bool = True,
    ) -> dict:
        """
        Check RSS feed for new posts.

        Args:
            feed_url: RSS feed URL
            since: Only return posts after this datetime
            scrape_content: Whether to scrape full page content

        Returns:
            Dictionary with stats and posts
        """
        print(f"\n📬 Checking RSS inbox: {feed_url}")
        print("=" * 70)

        # Fetch feed entries
        entries = self.fetch_feed_via_browser(feed_url)

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

            # Scrape full content if requested
            scraped = None
            if scrape_content and post_url:
                scraped = self.spider.crawl_page(post_url)

            post = {
                'title': title,
                'url': post_url,
                'published': published_date,
                'description': description,
                'is_new': is_new,
                'scraped': scraped,
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
                    if post['scraped'] and post['scraped']['images']:
                        print(f"     Images found: {len(post['scraped']['images'])}")

        return {
            'total': len(posts),
            'new': new_count,
            'posts': posts,
        }

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

                post_data = post['scraped'] if post['scraped'] else post
                content = post_data.get('content') or post.get('description', '')
                author = post_data.get('author')

                # Create post node
                query = """
                MERGE (p:Post {url: $url})
                SET p.title = $title,
                    p.selftext = $content,
                    p.created_utc = $created_utc,
                    p.author = $author,
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
                    'content': content,
                    'created_utc': post['published'] or datetime.utcnow(),
                    'author': author,
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
        description="Check RSS inbox with Creepy Crawly spider"
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
        "--dry-run",
        action="store_true",
        help="Don't scrape full content, just list posts"
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

    # Initialize spider
    spider = CreepyCrawlySpider()

    try:
        spider.start()

        # Initialize inbox checker
        checker = RSSInboxChecker(spider)

        # Check for new posts
        result = checker.check_new_posts(
            feed_url=args.feed_url,
            since=since_date,
            scrape_content=not args.dry_run,
        )

        # Save to database if requested
        if args.save:
            checker.save_to_database(result['posts'])

        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Summary: {result['new']} new posts out of {result['total']} total")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        spider.stop()


if __name__ == "__main__":
    sys.exit(main())
