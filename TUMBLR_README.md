# Tumblr Integration Complete Package

## Summary

Complete Tumblr integration for your feed system including:
- **TumblrAdapter**: Platform adapter for fetching posts
- **Historical Importer**: Pull full historical posts to graph
- **Source Management**: Add blogs to crawl queue
- **Data Inspector**: Check what's stored in Neo4j
- **Semantic Layer**: Build knowledge graph with tags/images

## Files Overview

| File | Purpose | Usage |
|------|----------|--------|
| `src/feed/platforms/tumblr.py` | Tumblr adapter for fetching posts | Import and use `TumblrAdapter` |
| `src/feed/platforms/__init__.py` | Export TumblrAdapter | Auto-imported from feed package |
| `import_tumblr_historical.py` | Import historical posts to graph | `python3 import_tumblr_historical.py` |
| `check_tumblr_data.py` | Inspect Neo4j data | `python3 check_tumblr_data.py` |
| `test_tumblr_adapter.py` | Basic adapter test | `python3 test_tumblr_adapter.py` |
| `tumblr_feed_example.py` | Analyze single blog feed | `python3 tumblr_feed_example.py` |
| `tumblr_semantic_layer.py` | Build knowledge graph export | `python3 tumblr_semantic_layer.py` |
| `config/tumblr_sources.json` | Source configuration | Edit to add more blogs |

## Quick Start

### 1. Import Historical Data

```bash
# Pull all historical posts from configured sources
python3 import_tumblr_historical.py
```

This:
- Adds `blackswandive.tumblr.com` and `barbie-expectations.tumblr.com` to crawl queue
- Fetches up to 1000 posts per blog
- Stores posts, images, and tags to Neo4j
- Shows detailed progress

### 2. Verify Import

```bash
# Check what was imported
python3 check_tumblr_data.py
```

This shows:
- Sources in URL Frontier
- Posts stored per source
- Images extracted
- Tags indexed

### 3. Query Knowledge Graph

```cypher
# Find all Tumblr posts
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE s.source_type = 'blog'
RETURN p.title, p.url, p.created_utc
ORDER BY p.created_utc DESC
LIMIT 10
```

## Workflow Diagram

```
┌─────────────────┐
│  Tumblr Blog   │
│  RSS Feed      │
└────────┬────────┘
         │
         │ 1. Fetch RSS
         ▼
┌───────────────────────────┐
│  TumblrAdapter          │
│  - Parse RSS           │
│  - Scrape HTML         │
│  - Extract images/tags   │
└────────┬──────────────────┘
         │
         │ 2. Store to Neo4j
         ▼
┌───────────────────────────────┐
│  URLFrontier (Source Mgmt)   │
│  - WebPage nodes          │
│  - Schedule crawls         │
└────────┬──────────────────────┘
         │
         │ 3. Add to crawl queue
         ▼
┌───────────────────────────────┐
│  Knowledge Graph (Neo4j)      │
│  - Post nodes            │
│  - Image nodes           │
│  - Tag nodes            │
│  - Relationships        │
└───────────────────────────────┘
```

## Adding More Sources

### Edit `config/tumblr_sources.json`

```json
{
  "tumblr_sources": [
    {
      "url": "https://blackswandive.tumblr.com",
      "blog_name": "blackswandive",
      "limit": 1000,
      "priority": 1.0
    },
    {
      "url": "https://your-new-blog.tumblr.com",
      "blog_name": "your-new-blog",
      "limit": 500,
      "priority": 0.8,
      "creator_slug": "optional-creator-entity",
      "description": "Add description here",
      "category": "category-name"
    }
  ]
}
```

### Add Single Source via CLI

```bash
# Quick add to crawl queue
python3 add_url_to_crawl.py https://your-blog.tumblr.com
```

## Data Structures

### Post Node

```cypher
(:Post {
  id: "123456789",
  title: "Photo",
  url: "https://blog.tumblr.com/post/123456789",
  created_utc: datetime(...),
  selftext: "Full content text...",
  author: "blogname",
  entity_matched: "optional-entity-name"
})
```

### Blog Source Node

```cypher
(:Subreddit {
  name: "blackswandive",
  source_type: "blog",
  created_at: datetime(...)
})
```

### Relationships

```
(:Post)-[:POSTED_IN]->(:Subreddit)
(:Post)-[:HAS_IMAGE]->(:Image)
(:Post)-[:HAS_TAG]->(:Tag)
(:User)-[:POSTED]->(:Post)
(:Creator)-[:HAS_SOURCE]->(:Subreddit)
```

## Common Tasks

### Import New Blogs

```bash
# Add to config
vim config/tumblr_sources.json

# Run importer
python3 import_tumblr_historical.py
```

### Analyze Single Blog

```bash
# Detailed feed analysis
python3 tumblr_feed_example.py
```

### Export Semantic Layer

```bash
# Generate Neo4j Cypher + JSON
python3 tumblr_semantic_layer.py

# Import to Neo4j
cat data/tumblr_neo4j_TIMESTAMP.cypher | cypher-shell -u neo4j -p password
```

### Check What's Imported

```bash
# Full data inspection
python3 check_tumblr_data.py
```

## Query Examples

### Find Recent Posts

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE s.source_type = 'blog'
RETURN p.title, p.url, p.created_utc
ORDER BY p.created_utc DESC
LIMIT 10
```

### Find Image-Heavy Posts

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE s.source_type = 'blog'
MATCH (p)-[r:HAS_IMAGE]->(i:Image)
WITH p, s, count(r) as img_count
WHERE img_count > 3
RETURN p.title, img_count, s.name
ORDER BY img_count DESC
LIMIT 10
```

### Find Posts by Tag

```cypher
MATCH (p:Post)-[:HAS_TAG]->(t:Tag {name: 'pink'})
MATCH (p)-[:POSTED_IN]->(s:Subreddit)
RETURN p.title, p.url, s.name
ORDER BY p.created_utc DESC
LIMIT 10
```

### Cross-Reference Sources

```cypher
MATCH (p1:Post)-[:POSTED_IN]->(s1:Subreddit)
MATCH (p1)-[:HAS_TAG]->(t:Tag)
MATCH (p2:Post)-[:HAS_TAG]->(t)
MATCH (p2)-[:POSTED_IN]->(s2:Subreddit)
WHERE s1.name <> s2.name
AND s1.source_type = 'blog'
AND s2.source_type = 'blog'
RETURN s1.name as blog1, s2.name as blog2, t.name as shared_tag, count(*) as posts
ORDER BY posts DESC
LIMIT 10
```

## Troubleshooting

### Import Fails

```bash
# Check Neo4j connection
docker compose ps neo4j

# Verify credentials
cat .env | grep NEO4J

# Test adapter only
python3 test_tumblr_adapter.py
```

### No Posts Found

```bash
# Check if blog exists
curl -I https://blackswandive.tumblr.com

# Check RSS feed
curl https://blackswandive.tumblr.com/rss
```

### Slow Import

```bash
# Edit config to reduce limit
# Set "limit": 100 instead of 1000

# Increase delay in importer
# Modify delay_min=5.0, delay_max=10.0
```

## Integration with Existing Systems

### Reddit Threads

Compatible with existing Reddit thread schema:
- Both use `Post` nodes
- Both use `HAS_IMAGE` relationships
- Both use `HAS_TAG` relationships
- Distinguished by `source_type` field on `Subreddit`

### Crawler System

Works with existing crawler:
- URLFrontier manages queue
- Crawler picks up Tumblr sources
- Respects rate limits automatically
- Schedules recurring crawls

### Neo4j Schema

Extends existing graph:
- New `source_type='blog'` on Subreddit nodes
- Tag system already exists
- Image indexing already exists
- No schema conflicts

## Documentation

- **TUMBLR_ADAPTER_GUIDE.md**: Adapter API reference
- **TUMBLR_EXAMPLES_GUIDE.md**: Example scripts
- **TUMBLR_HISTORICAL_IMPORT_GUIDE.md**: Import workflow details

## Next Steps

1. Run `import_tumblr_historical.py` to pull data
2. Run `check_tumblr_data.py` to verify
3. Query Neo4j for insights
4. Start crawler for ongoing updates
5. Build semantic layer queries for analysis
