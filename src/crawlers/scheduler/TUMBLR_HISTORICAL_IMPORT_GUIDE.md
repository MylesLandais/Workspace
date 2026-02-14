# Tumblr Historical Data Import Guide

## Overview

This guide explains how to pull full historical posts from Tumblr blogs and add them to:
1. **Source Management Tables** (URL Frontier for ongoing crawling)
2. **Knowledge Graph** (Neo4j with full semantic data)

## Files Created

| File | Purpose |
|-------|----------|
| `import_tumblr_historical.py` | Main script to import historical Tumblr data |
| `check_tumblr_data.py` | Inspect existing data in Neo4j |
| `config/tumblr_sources.json` | Configuration file for Tumblr sources |

---

## Quick Start

### 1. Import Historical Posts

```bash
# Run the importer with predefined sources
python3 import_tumblr_historical.py
```

This will:
- Add `blackswandive.tumblr.com` and `barbie-expectations.tumblr.com` to URL Frontier
- Fetch up to 1000 posts from each blog
- Store posts, images, and tags to Neo4j knowledge graph
- Display detailed progress and statistics

### 2. Check What Was Imported

```bash
# Inspect the knowledge graph
python3 check_tumblr_data.py
```

This shows:
- Sources in URL Frontier
- Posts stored per source
- Images extracted
- Tags indexed
- Overall statistics

---

## Configuration

### Edit `config/tumblr_sources.json`

```json
{
  "tumblr_sources": [
    {
      "url": "https://your-blog.tumblr.com",
      "blog_name": "your-blog",
      "limit": 1000,
      "priority": 1.0,
      "creator_slug": "optional-creator-entity",
      "description": "Blog description",
      "category": "personal"
    }
  ]
}
```

### Source Fields

| Field | Type | Required | Description |
|--------|--------|-----------|
| `url` | string | Yes | Full blog URL or name |
| `blog_name` | string | No | Short name for tracking |
| `limit` | integer | No | Max posts to fetch (default: 1000) |
| `priority` | float | No | Crawl priority (higher = more important) |
| `creator_slug` | string | No | Link to Creator entity in graph |
| `description` | string | No | Human-readable description |
| `category` | string | No | Category for organization |

---

## Import Workflow

### Step 1: Add to Source Management

The script uses `URLFrontier` to add blogs to the crawl queue:

```python
from feed.crawler.frontier import URLFrontier

frontier = URLFrontier(neo4j)
frontier.add_url("https://blackswandive.tumblr.com", priority=1.0)
```

**Result**: Creates `WebPage` node in Neo4j with:
- `original_url`: Original blog URL
- `domain`: Extracted domain
- `next_crawl_at`: When to crawl next
- `robots_allowed`: `true` by default

### Step 2: Fetch Historical Posts

Uses `TumblrAdapter` to fetch RSS feed:

```python
from feed.platforms.tumblr import TumblrAdapter

adapter = TumblrAdapter(delay_min=2.0, delay_max=5.0)

posts, _ = adapter.fetch_posts(
    source="blackswandive.tumblr.com",
    limit=1000,
    scrape_content=True
)
```

**Result**: Returns `Post` objects with:
- ID, title, URL, created date
- Full content (scraped from HTML)
- Author, source blog name

### Step 3: Extract Metadata

Retrieves extended metadata:

```python
metadata = adapter.get_post_metadata(post.id)
# metadata['images']: List of image URLs
# metadata['tags']: List of tags
# metadata['entity_matched']: Entity filter results
```

### Step 4: Store to Knowledge Graph

Uses `store_blog_post()` to persist data:

```python
from feed.storage.thread_storage import store_blog_post

store_blog_post(
    neo4j=neo4j,
    post=post,
    images=metadata['images'],
    creator_slug="optional-creator"
)
```

**Result**: Creates graph structure:
```
(Subreddit:Blog)-[:POSTED_IN]->(Post)
(Post)-[:HAS_IMAGE]->(Image)
(Post)-[:HAS_TAG]->(Tag)
(User)-[:POSTED]->(Post)
```

---

## Data Model

### Graph Schema

```
WebPage (Source Management)
├── original_url
├── domain
├── next_crawl_at
└── last_crawled_at

Subreddit (Blog Source)
├── name
└── source_type: 'blog'

Post
├── id
├── title
├── url
├── created_utc
├── selftext
├── author
└── entity_matched

Image
└── url

Tag
└── name

Relationships
- (:Post)-[:POSTED_IN]->(:Subreddit)
- (:Post)-[:HAS_IMAGE]->(:Image)
- (:Post)-[:HAS_TAG]->(:Tag)
- (:User)-[:POSTED]->(:Post)
```

---

## Usage Examples

### Import Single Blog

```bash
# Quick import of one blog
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
sys.path.insert(0, str(Path('.') / 'src'))

from import_tumblr_historical import TumblrHistoricalImporter

importer = TumblrHistoricalImporter()
importer.import_source('https://blackswandive.tumblr.com', limit=100)
"
```

### Import Multiple Blogs from Config

```python
import json
from pathlib import Path
from import_tumblr_historical import TumblrHistoricalImporter

# Load config
with open('config/tumblr_sources.json') as f:
    config = json.load(f)

# Import all sources
importer = TumblrHistoricalImporter()

for source in config['tumblr_sources']:
    importer.import_source(
        blog_url=source['url'],
        limit=source['limit'],
        priority=source['priority'],
        creator_slug=source.get('creator_slug')
    )

importer.print_final_summary()
```

### Check Data Quality

```bash
# After import, verify data
python3 check_tumblr_data.py
```

Look for:
- ✅ Sources in URL Frontier
- ✅ Posts stored per source
- ✅ Images extracted (should be > 0 for image-heavy blogs)
- ✅ Tags indexed

---

## Output Examples

### Import Progress

```
🎯 Importing Source: https://blackswandive.tumblr.com
======================================================================

📋 Adding source to management: https://blackswandive.tumblr.com
   ✓ Source added to crawl queue

📥 Fetching historical posts from: https://blackswandive.tumblr.com
   Limit: 1000 posts
   ✓ Fetched 50 posts

💾 Importing 50 posts to Neo4j...
   Progress: 10/50 posts stored
   Progress: 20/50 posts stored
   Progress: 30/50 posts stored
   Progress: 40/50 posts stored
   Progress: 50/50 posts stored
   ✓ Completed: 50 posts stored
```

### Final Summary

```
📊 FINAL IMPORT SUMMARY
======================================================================

📋 Source Management:
   Sources added: 2
   Sources already exists: 0

📥 Data Fetched:
   Total posts fetched: 100
   Total images extracted: 245
   Total tags extracted: 67

💾 Data Stored:
   Posts stored to graph: 100
   Posts skipped (errors): 0

❌ Errors:
   No errors!
```

---

## Ongoing Crawling

Once sources are in URL Frontier, the crawler system will automatically:

1. **Check scheduled time**: `next_crawl_at` field
2. **Respect rate limits**: 2-5 second delays between requests
3. **Fetch new posts**: Only adds posts since last crawl
4. **Update graph**: Adds new posts, images, tags
5. **Schedule next crawl**: Updates `next_crawl_at`

### Monitor Crawling

```bash
# Check if crawler is running
docker compose ps

# Check crawler logs
docker compose logs crawler
```

---

## Troubleshooting

### "No posts found"

**Cause**: Blog may be private or RSS feed disabled

**Fix**:
1. Check blog URL in browser
2. Verify RSS exists: `https://blogname.tumblr.com/rss`
3. Check for rate limiting (add delay)

### "Neo4j connection error"

**Cause**: Neo4j not running or wrong credentials

**Fix**:
```bash
# Check Neo4j status
docker compose ps neo4j

# Check connection
# In .env, verify NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
```

### "Import takes too long"

**Cause**: Limit too high or slow network

**Fix**:
1. Reduce `limit` in config
2. Increase delay: `delay_min=5.0, delay_max=10.0`
3. Import in batches

---

## Query Examples

### Find All Tumblr Posts

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE s.source_type = 'blog'
RETURN p, s
ORDER BY p.created_utc DESC
LIMIT 20
```

### Find Posts with Images

```cypher
MATCH (p:Post)-[:HAS_IMAGE]->(i:Image)
RETURN p.title as title, count(i) as image_count
ORDER BY image_count DESC
LIMIT 10
```

### Find Posts by Tag

```cypher
MATCH (p:Post)-[:HAS_TAG]->(t:Tag {name: 'pink'})
RETURN p.title, p.url, p.created_utc
ORDER BY p.created_utc DESC
LIMIT 10
```

### Export for Analysis

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE s.source_type = 'blog'
RETURN p.id, p.title, p.url, p.created_utc, s.name as source
CALL apoc.export.csv.query([
  'id', 'title', 'url', 'created_utc', 'source'
], '/tmp/tumblr_posts.csv')
```

---

## Next Steps

1. ✅ **Run import**: `python3 import_tumblr_historical.py`
2. ✅ **Verify data**: `python3 check_tumblr_data.py`
3. ✅ **Query graph**: Use Neo4j browser or cypher-shell
4. ✅ **Start crawler**: Ongoing updates from URL Frontier
5. ✅ **Build semantic layer**: Use tags and relationships for analysis

---

## Integration Notes

### Existing Systems

- **URLFrontier**: Manages crawl queue and scheduling
- **Thread Storage**: Persists posts, images, comments
- **Neo4j**: Knowledge graph with relationships

### Compatibility

Works with existing:
- Reddit threads (shared schema)
- Blog posts (new `source_type='blog'` field)
- Image indexing (same `HAS_IMAGE` relationship)
- Tag system (same `HAS_TAG` relationship)
