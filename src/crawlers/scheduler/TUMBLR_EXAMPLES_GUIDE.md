# Tumblr Feed Examples Guide

## Available Examples

### 1. Basic Test: `test_tumblr_adapter.py`

Simple test to verify the adapter works with any Tumblr blog.

```bash
python3 test_tumblr_adapter.py
```

**Features:**
- Fetches 5 posts from blackswandive.tumblr.com
- Displays post metadata
- Shows blog information

**Use when:**
- Verifying adapter installation
- Quick sanity check
- Testing network connectivity

---

### 2. Semantic Layer Builder: `tumblr_semantic_layer.py`

Builds a knowledge graph from Tumblr posts for semantic analysis.

```bash
python3 tumblr_semantic_layer.py
```

**Features:**
- Fetches posts and extracts semantic entities
- Identifies entity types (location, activity, mood)
- Detects hashtags and mentions
- Exports to JSON for analysis
- Generates Neo4j Cypher statements for graph import

**Outputs:**
- `data/tumblr_semantic_YYYYMMDD_HHMMSS.json` - Raw semantic entities
- `data/tumblr_neo4j_YYYYMMDD_HHMMSS.cypher` - Neo4j import statements

**Use when:**
- Building knowledge graphs
- Entity relationship mapping
- Cross-platform content analysis
- Semantic search indexing

---

### 3. User Feed Analyzer: `tumblr_feed_example.py`

Analyzes a specific user's feed with detailed statistics and patterns.

```bash
python3 tumblr_feed_example.py
```

**Features:**
- Analyzes barbie-expectations.tumblr.com feed
- Calculates posting frequency
- Extracts top tags and themes
- Shows content length statistics
- Displays image-to-post ratio
- Exports entities for semantic layer

**Outputs:**
- `data/tumblr_feeds/barbie-expectations_analysis_YYYYMMDD_HHMMSS.json` - Full analysis
- `data/tumblr_feeds/barbie-expectations_entities_YYYYMMDD_HHMMSS.json` - Semantic entities

**Use when:**
- Understanding user behavior patterns
- Content theme analysis
- Image collection and cataloging
- Trend tracking over time

---

## Quick Start

### Analyze Any Tumblr Blog

Edit `tumblr_feed_example.py` and change the blog URL:

```python
# Target blog
blog_url = "https://your-blog.tumblr.com"
blog_name = "your-blog"
```

Then run:
```bash
python3 tumblr_feed_example.py
```

---

## Custom Usage Examples

### Fetch Posts with Entity Filter

```python
from src.feed.platforms.tumblr import TumblrAdapter

adapter = TumblrAdapter()

# Only fetch posts mentioning specific entity
posts, _ = adapter.fetch_posts(
    source="barbie-expectations",
    entity_filter="pink",  # Posts with "pink" in content
    limit=20
)
```

### Crawl Multiple Blogs

```python
blogs = [
    "blackswandive",
    "barbie-expectations",
    "nasa"
]

for blog in blogs:
    posts, _ = adapter.fetch_posts(blog, limit=10)
    print(f"{blog}: {len(posts)} posts")
```

### Extract All Images

```python
adapter = TumblrAdapter()
posts, _ = adapter.fetch_posts("barbie-expectations", limit=50)

all_images = []
for post in posts:
    metadata = adapter.get_post_metadata(post.id)
    if metadata:
        all_images.extend(metadata['images'])

print(f"Found {len(all_images)} images")
```

### Build Knowledge Graph

```python
# Use tumblr_semantic_layer.py outputs

# Import to Neo4j
cypher_file = "data/tumblr_neo4j_YYYYMMDD_HHMMSS.cypher"

# Using cypher-shell:
# cat cypher_file | cypher-shell -u neo4j -p password
```

---

## Data Models

### Post Object

```python
{
    "id": "123456789",
    "title": "Photo",
    "created_utc": "2018-07-25T22:01:30",
    "url": "https://blog.tumblr.com/post/123456789",
    "selftext": "Post content text...",
    "author": "blogname",
    "subreddit": "blogname"
}
```

### Extended Metadata

```python
{
    "images": ["https://64.media.tumblr.com/...", ...],
    "tags": ["pink", "fashion", "style"],
    "entity_matched": "pink"  # If entity filter was used
}
```

### Semantic Entity

```python
{
    "post_id": "123456789",
    "url": "https://...",
    "created_at": "2018-07-25T22:01:30",
    "blog": "barbie-expectations",
    "author": "barbie-expectations",
    "images": [...],
    "tags": [...],
    "entity_types": ["tag", "location"],
    "mentions": [
        {"type": "location", "value": "nyc"}
    ],
    "hashtags": ["#pink", "#fashion"]
}
```

---

## Integration Patterns

### With Post Service

```python
from src.feed.services.post_service import PostService
from src.feed.platforms.tumblr import TumblrAdapter

adapter = TumblrAdapter()
service = PostService(repository=..., adapter=adapter)

# Fetch and store posts
posts, _ = adapter.fetch_posts("barbie-expectations", limit=20)
for post in posts:
    service.store_post(post)
```

### With Dependency Injection

```python
from src.feed.di.container import DIContainer

container = DIContainer()
container.register('tumblr_adapter', lambda: TumblrAdapter())

# Use in application
tumblr = container.get('tumblr_adapter')
posts, _ = tumblr.fetch_posts("barbie-expectations")
```

---

## Advanced Features

### Rate Limiting Control

```python
adapter = TumblrAdapter(
    delay_min=1.0,   # Faster requests (use carefully)
    delay_max=3.0
)
```

### Mock Mode for Testing

```python
adapter = TumblrAdapter(mock=True)
# Returns fake data, no network requests
```

### Pagination (Future Enhancement)

```python
# RSS feeds return first 20 posts by default
# For more posts, implement page-based fetching
```

---

## Troubleshooting

### "Import Error: feedparser not found"
```bash
# Install missing dependencies
uv add feedparser beautifulsoup4
```

### "No posts found"
- Check blog URL is correct
- Blog may be private or deleted
- Network connectivity issue

### "Rate limit errors"
- Increase delay_min and delay_max
- Reduce limit parameter
- Use mock mode for testing

---

## Next Steps

1. **Run examples**: Start with `test_tumblr_adapter.py` to verify setup
2. **Analyze feed**: Use `tumblr_feed_example.py` with your target blog
3. **Build semantic layer**: Use `tumblr_semantic_layer.py` for knowledge graphs
4. **Integrate with Neo4j**: Import Cypher statements to graph database
5. **Analyze patterns**: Use exported JSON for data science workflows
