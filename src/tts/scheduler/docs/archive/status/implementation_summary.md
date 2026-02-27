# Cross-Thread Relationship System - Implementation Summary

## What Was Built

A complete system for mapping and correlating Reddit threads across subreddits, specifically designed to track how discussions spread (e.g., z.ai releases discussed in r/LocalLLaMA and r/SillyTavernAI).

## Files Created/Modified

### New Files

1. **`src/feed/utils/reddit_url_extractor.py`**
   - Extracts Reddit URLs from text (comments, posts)
   - Handles multiple URL formats (new/old Reddit, permalinks, short URLs)
   - Parses post IDs and subreddit information

2. **`src/feed/storage/migrations/007_thread_relationships.cypher`**
   - Neo4j schema migration for thread relationships
   - Adds indexes for relationship queries

3. **`crawl_related_threads.py`**
   - Recursive crawler that starts from a seed thread
   - Follows discovered Reddit URLs to build relationship graph
   - Configurable depth and thread limits

4. **`test_thread_relationships.py`**
   - Test suite for URL extraction functionality

5. **Documentation:**
   - `docs/CROSS_THREAD_RELATIONSHIPS.md` - Complete system documentation
   - `THREAD_RELATIONSHIP_QUICKSTART.md` - Quick start guide
   - `USAGE_EXAMPLES.md` - Docker-based usage examples
   - `IMPLEMENTATION_SUMMARY.md` - This file

### Modified Files

1. **`src/feed/storage/thread_storage.py`**
   - Added `store_thread_relationships()` function
   - Added `create_thread_relationship()` function
   - Automatically extracts and stores relationships when storing threads
   - Enhanced `store_thread_from_crawl_result()` to call relationship extraction

2. **`reddit_thread_crawler.py`**
   - Already had relationship storage integration
   - Now automatically extracts relationships during crawling

## How It Works

### 1. Automatic Relationship Detection

When you crawl a thread using `reddit_thread_crawler.py`, it:
- Scans post selftext for Reddit URLs
- Scans all comments for Reddit URLs
- Creates `RELATES_TO` relationships in Neo4j automatically

### 2. Recursive Relationship Discovery

Use `crawl_related_threads.py` to:
- Start from a seed thread (e.g., the GLM-4.7 AMA)
- Extract all Reddit URLs found
- Recursively crawl discovered threads
- Build a complete relationship graph

### 3. Graph Schema

Relationships are stored as:
```cypher
(source:Post)-[:RELATES_TO {
  relationship_type: "cross_reference",
  source_type: "comment",  // or "post"
  source_author: "username",
  comment_id: "comment_id",  // if from comment
  discovered_at: datetime()
}]->(target:Post)
```

## Quick Start

### For Your Specific Use Case (GLM-4.7 Tracking)

```bash
# 1. Make sure Docker is running
docker compose ps

# 2. Crawl the original thread and discover relationships
docker compose exec jupyterlab python crawl_related_threads.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --depth 2 \
    --max-threads 50

# 3. Query relationships in Neo4j
# (Use Neo4j Browser or cypher-shell)
MATCH (source:Post {id: "1ptxm3x"})<-[:RELATES_TO]-(related:Post)
RETURN related.subreddit, related.title, related.permalink
```

## Key Features

1. **Automatic Detection**: Relationships are found automatically during normal crawling
2. **Recursive Discovery**: Follow links to build complete relationship graphs
3. **Cross-Subreddit Tracking**: Track how discussions spread across subreddits
4. **Rich Context**: Store metadata about where relationships were discovered
5. **Placeholder Support**: Creates placeholder nodes for referenced threads not yet crawled

## Next Steps

1. **Test the System**:
   ```bash
   docker compose exec jupyterlab python test_thread_relationships.py
   ```

2. **Run Your First Crawl**:
   ```bash
   docker compose exec jupyterlab python crawl_related_threads.py \
       --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
       --depth 1 \
       --max-threads 10
   ```

3. **Query Results**:
   - Access Neo4j Browser (if configured)
   - Or use cypher-shell in Docker container
   - See `USAGE_EXAMPLES.md` for query examples

4. **Set Up Continuous Monitoring**:
   - Regularly crawl r/SillyTavernAI to catch new discussions
   - Use cron or a monitoring script (see `USAGE_EXAMPLES.md`)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  reddit_thread_crawler.py                               │
│  - Crawls threads with full comments                    │
│  - Automatically extracts relationships                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  reddit_url_extractor.py                                 │
│  - Detects Reddit URLs in text                           │
│  - Parses post IDs and subreddits                       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  thread_storage.py                                       │
│  - Stores threads, comments, images                     │
│  - Creates RELATES_TO relationships                     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Neo4j Knowledge Graph                                   │
│  - Post nodes                                            │
│  - Comment nodes                                         │
│  - RELATES_TO relationships                              │
└─────────────────────────────────────────────────────────┘
```

## Integration Points

- **Existing Crawlers**: All existing crawlers automatically extract relationships
- **Neo4j Storage**: Uses existing Neo4j connection infrastructure
- **Feed System**: Can be integrated into subscriber feed generation
- **GraphQL API**: Can expose relationships via existing GraphQL endpoints

## Limitations & Future Enhancements

Current limitations:
- Only detects explicit URL links (not semantic relationships)
- Short URLs (redd.it) don't include subreddit until fetched
- No automatic background crawling of referenced threads

Future enhancements:
- Semantic relationship detection (topic modeling)
- Relationship confidence scoring
- Automatic background crawling
- Timeline visualization
- Subscriber feed integration

## Support

- **Documentation**: See `docs/CROSS_THREAD_RELATIONSHIPS.md`
- **Examples**: See `USAGE_EXAMPLES.md`
- **Quick Start**: See `THREAD_RELATIONSHIP_QUICKSTART.md`
- **Tests**: Run `test_thread_relationships.py` to verify functionality






