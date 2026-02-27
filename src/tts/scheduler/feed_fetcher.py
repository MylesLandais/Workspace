#!/usr/bin/env python3
"""
Feed Fetcher for Universal Feed Reader.
Downloads articles from subscribed feeds and saves them as local HTML files.
"""

import os
import sys
import json
import re
import logging
from datetime import datetime
from pathlib import Path
import unicodedata

# Third-party imports
try:
    import feedparser
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Missing dependency. Please ensure feedparser and beautifulsoup4 are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

FEEDS_FILE = "feeds.json"
DOWNLOAD_DIR = "reader_library"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max_width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        article {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ margin-top: 0; color: #1a1a1a; }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }}
        img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; border-radius: 4px; }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 0;
            padding-left: 20px;
            color: #555;
        }}
        .nav {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../../index.html">← Back to Dashboard</a>
    </div>
    <article>
        <header>
            <h1>{title}</h1>
            <div class="meta">
                <strong>Source:</strong> {feed_title}<br>
                <strong>Date:</strong> {date}<br>
                <strong>Author:</strong> {author}
            </div>
        </header>
        <div class="content">
            {content}
        </div>
    </article>
</body>
</html>
"""

def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

class FeedFetcher:
    def __init__(self, feeds_file: str = FEEDS_FILE, download_dir: str = DOWNLOAD_DIR):
        self.feeds_file = feeds_file
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

    def load_feeds(self):
        if not os.path.exists(self.feeds_file):
            logger.error(f"Feeds file {self.feeds_file} not found.")
            return []
        with open(self.feeds_file, 'r') as f:
            return json.load(f)

    def fetch_all(self):
        feeds = self.load_feeds()
        if not feeds:
            print("No feeds to fetch.")
            return

        print(f"🚀 Starting fetch for {len(feeds)} feeds...")
        
        total_new = 0
        
        for feed_cfg in feeds:
            try:
                new_count = self.fetch_feed(feed_cfg)
                total_new += new_count
            except Exception as e:
                logger.error(f"Failed to process feed {feed_cfg.get('title')}: {e}")

        print("\n" + "="*50)
        print(f"✨ Update Complete. {total_new} new articles downloaded.")
        print("="*50)

    def fetch_feed(self, feed_cfg):
        url = feed_cfg['url']
        feed_title = feed_cfg['title']
        
        logger.info(f"Fetching: {feed_title}")
        
        # Parse feed
        d = feedparser.parse(url)
        
        if d.bozo:
            logger.warning(f"  ⚠️  Feed parsing issue for {feed_title}: {d.bozo_exception}")

        # Create directory for this feed
        feed_slug = slugify(feed_title)
        feed_dir = self.download_dir / feed_slug
        feed_dir.mkdir(exist_ok=True)

        new_count = 0

        for entry in d.entries:
            # Get Title
            title = entry.get('title', 'Untitled')
            
            # Get Date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.now()
            
            date_str = published.strftime('%Y-%m-%d')
            display_date = published.strftime('%B %d, %Y')
            
            # Generate Filename
            slug = slugify(title)
            filename = f"{date_str}-{slug}.html"
            filepath = feed_dir / filename
            
            # Skip if exists
            if filepath.exists():
                continue
            
            # Get Content
            content = ""
            if 'content' in entry:
                # Atom/RSS content module
                for c in entry.content:
                    content += c.value
            elif 'summary_detail' in entry:
                content = entry.summary_detail.value
            elif 'summary' in entry:
                content = entry.summary
            elif 'description' in entry:
                content = entry.description
            
            # Get Author
            author = entry.get('author', feed_title)
            
            # Save HTML
            html_content = HTML_TEMPLATE.format(
                title=title,
                feed_title=feed_title,
                date=display_date,
                author=author,
                content=content
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            new_count += 1
            logger.info(f"  📥 Downloaded: {title}")

        return new_count

if __name__ == "__main__":
    fetcher = FeedFetcher()
    fetcher.fetch_all()
