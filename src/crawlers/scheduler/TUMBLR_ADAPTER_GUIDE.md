# Tumblr Adapter Usage Guide

## Overview

The TumblrAdapter allows you to parse Tumblr blog RSS feeds and scrape full post content with rich context including images, tags, and metadata.

## Installation

Ensure dependencies are installed (already in requirements.txt):
```bash
beautifulsoup4>=4.12.0
feedparser>=6.0.10
requests>=2.31.0
```

## Basic Usage

### Import the Adapter

```python
from src.feed.platforms.tumblr import TumblrAdapter

# Initialize adapter
adapter = TumblrAdapter(
    delay_min=2.0,  # Minimum delay between requests
    delay_max=5.0,  # Maximum delay between requests
)
```

### Fetch Posts

```python
# Using full URL
posts, next_token = adapter.fetch_posts(
    source="https://blackswandive.tumblr.com",
    limit=20,
    scrape_content=True  # Scrape full HTML content
)

# Using blog name only
posts, next_token = adapter.fetch_posts(
    source="blackswandive",
    limit=20
)
```

### Access Post Metadata

```python
for post in posts:
    print(f"Post ID: {post.id}")
    print(f"Title: {post.title}")
    print(f"URL: {post.url}")
    print(f"Created: {post.created_utc}")
    print(f"Author: {post.author}")
    print(f"Content preview: {post.selftext[:100]}...")

    # Get rich metadata (images, tags)
    metadata = adapter.get_post_metadata(post.id)
    if metadata:
        print(f"Images: {len(metadata['images'])}")
        for img_url in metadata['images']:
            print(f"  - {img_url}")
        print(f"Tags: {metadata['tags']}")
```

### Entity Filtering

Filter posts by entity name (useful for tracking specific people, brands, or keywords):

```python
posts, _ = adapter.fetch_posts(
    source="blackswandive",
    entity_filter="philadelphia",  # Only posts mentioning "philadelphia"
    limit=50
)
```

### Fetch Blog Metadata

```python
from src.feed.models.subreddit import Subreddit

metadata = adapter.fetch_source_metadata("blackswandive")
if metadata:
    print(f"Blog: {metadata.name}")
    print(f"Description: {metadata.description}")
    print(f"Created: {metadata.created_utc}")
```

## Data Structure

### Post Fields

- `id`: Unique post identifier (numeric or slug)
- `title`: Post title
- `created_utc`: Publication timestamp
- `url`: Full post URL
- `selftext`: Full post content (HTML parsed to text)
- `author`: Blog name or author
- `subreddit`: Blog name (reused field)
- `permalink`: Full post URL

### Extended Metadata (via get_post_metadata)

- `images`: List of image URLs extracted from post
- `tags`: List of tags associated with post
- `entity_matched`: Entity filter string if match occurred

## Integration with Feed Engine

```python
from src.feed.di.container import DIContainer
from src.feed.platforms.tumblr import TumblrAdapter

# Register Tumblr adapter
container = DIContainer()
container.register(
    'tumblr_adapter',
    lambda: TumblrAdapter(),
    singleton=True
)

# Use in post service
tumblr = container.get('tumblr_adapter')
posts, _ = tumblr.fetch_posts("blackswandive", limit=10)
```

## Notes

1. **Rate Limiting**: The adapter automatically delays between requests (2-5 seconds by default) to be respectful.

2. **RSS Format**: Tumblr blogs automatically provide RSS feeds at `https://blogname.tumblr.com/rss`.

3. **Content Scraping**: When `scrape_content=True`, the adapter makes additional HTTP requests to fetch full post HTML and extract additional metadata not available in the RSS feed.

4. **Mock Mode**: Set `mock=True` during testing to avoid network requests and return fake data.

## Examples

### Crawl Multiple Blogs

```python
blogs = [
    "blackswandive",
    "nasa",
    "moma"
]

for blog in blogs:
    posts, _ = adapter.fetch_posts(blog, limit=5)
    print(f"{blog}: {len(posts)} posts")
```

### Build Semantic Layer

```python
from src.feed.models.creator import Creator

# Extract entity relationships from posts
for post in posts:
    metadata = adapter.get_post_metadata(post.id)

    # Extract mentions, tags, and other semantic data
    creator = Creator(
        name=post.author,
        platform="tumblr",
        source=post.subreddit
    )
    # Store to Neo4j or other graph database
```

## Supported URL Formats

- `https://blogname.tumblr.com`
- `http://blogname.tumblr.com`
- `blogname.tumblr.com`
- `blogname`

All normalize to the blog name internally.
