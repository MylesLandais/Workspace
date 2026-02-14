# Cross-Thread Relationship Mapping

## Overview

This system enables mapping and correlating related Reddit threads across subreddits. It automatically detects when threads reference each other and builds a knowledge graph of these relationships.

## Use Cases

- Track how discussions spread across subreddits
- Find related threads when monitoring specific topics (e.g., z.ai releases discussed in r/SillyTavernAI and r/LocalLLaMA)
- Build subscriber feeds with rich context from related discussions
- Discover conversation networks around specific topics

## How It Works

### 1. URL Detection

When crawling a Reddit thread, the system scans:
- Post selftext (original post content)
- All comments (including nested replies)

It extracts Reddit URLs in various formats:
- `https://www.reddit.com/r/subreddit/comments/post_id/title/`
- `https://old.reddit.com/r/subreddit/comments/post_id/title/`
- `/r/subreddit/comments/post_id/title/` (relative permalinks)
- `https://redd.it/post_id` (short URLs)

### 2. Relationship Storage

When a Reddit URL is found, the system creates a `RELATES_TO` relationship in Neo4j:

```cypher
(source:Post)-[:RELATES_TO {
  relationship_type: "cross_reference",
  source_type: "comment",  // or "post"
  source_author: "username",
  comment_id: "comment_id",  // if from comment
  discovered_at: datetime()
}]->(target:Post)
```

### 3. Graph Schema

The migration `007_thread_relationships.cypher` adds:
- Indexes on `Post.permalink` and `Post.url` for fast lookups
- Support for `RELATES_TO` relationships between posts

## Usage

### Basic Crawling (Automatic Relationship Detection)

When using `reddit_thread_crawler.py`, relationships are automatically extracted and stored:

```bash
python reddit_thread_crawler.py r/SillyTavernAI --limit 10
```

This will:
1. Crawl threads from r/SillyTavernAI
2. Extract Reddit URLs from comments/posts
3. Store relationships in Neo4j automatically

### Recursive Related Thread Crawling

Use `crawl_related_threads.py` to start from a seed thread and recursively crawl related threads:

```bash
python crawl_related_threads.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --depth 2 \
    --max-threads 50
```

This will:
1. Crawl the seed thread
2. Extract all Reddit URLs found
3. Recursively crawl discovered threads (up to `--depth` levels)
4. Stop when hitting `--max-threads` limit

**Example: Tracking z.ai Release Discussion**

```bash
# Start from the original r/LocalLLaMA thread
python crawl_related_threads.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --depth 3 \
    --max-threads 100

# This will discover and crawl:
# - r/LocalLLaMA/comments/1ptxm3x/... (seed)
# - r/SillyTavernAI/comments/1pu1nx1/... (discusses the seed)
# - Any other threads referenced in those discussions
```

## Querying Relationships

### Find All Threads Discussing a Specific Post

```cypher
MATCH (source:Post {id: "1ptxm3x"})<-[:RELATES_TO]-(related:Post)
RETURN related.id, related.title, related.subreddit, related.permalink
ORDER BY related.created_utc DESC
```

### Find Conversation Chains

```cypher
MATCH path = (start:Post {id: "1ptxm3x"})<-[:RELATES_TO*1..3]-(related:Post)
RETURN path
LIMIT 50
```

### Find Cross-Subreddit Relationships

```cypher
MATCH (p1:Post)-[:RELATES_TO]->(p2:Post)
WHERE p1.subreddit <> p2.subreddit
RETURN p1.subreddit, p2.subreddit, count(*) as relationship_count
ORDER BY relationship_count DESC
```

### Get Rich Context for a Thread

```cypher
MATCH (main:Post {id: "1ptxm3x"})
OPTIONAL MATCH (main)<-[:RELATES_TO]-(discussed:Post)
OPTIONAL MATCH (main)-[:RELATES_TO]->(references:Post)
RETURN 
  main.title as main_thread,
  main.subreddit as main_subreddit,
  collect(DISTINCT discussed.title) as discussed_in,
  collect(DISTINCT references.title) as references
```

## Implementation Details

### Files

- `src/feed/utils/reddit_url_extractor.py` - URL extraction utilities
- `src/feed/storage/thread_storage.py` - Relationship storage functions
- `src/feed/storage/migrations/007_thread_relationships.cypher` - Schema migration
- `crawl_related_threads.py` - Recursive crawler for related threads
- `reddit_thread_crawler.py` - Enhanced with automatic relationship detection

### Relationship Types

Currently supported:
- `cross_reference` - Direct URL link found in comment/post

Future enhancements could include:
- `discusses` - Semantic relationship (e.g., mentions topic without URL)
- `duplicate` - Same content posted in multiple subreddits
- `follow_up` - Explicit follow-up or continuation thread

## Best Practices

1. **Start Small**: Use `--depth 1` or `--depth 2` initially to avoid excessive crawling
2. **Monitor Limits**: Set `--max-threads` to prevent runaway crawls
3. **Respect Rate Limits**: The crawler includes delays, but monitor Reddit API limits
4. **Regular Updates**: Re-crawl key threads periodically to capture new relationships
5. **Use Placeholders**: The system creates placeholder nodes for referenced threads that haven't been crawled yet

## Limitations

- Short URLs (redd.it) don't include subreddit info until fetched
- Relationships are only discovered when threads are crawled
- No automatic crawling of referenced threads (use `crawl_related_threads.py` for that)
- Relationship confidence/scoring not yet implemented

## Future Enhancements

- Semantic relationship detection (topic modeling, embeddings)
- Relationship confidence scoring
- Automatic background crawling of referenced threads
- Timeline visualization of discussion spread
- Subscriber feed integration with related thread context






