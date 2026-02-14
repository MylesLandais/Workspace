# Spider/Crawler Design Decisions

## Overview
This document outlines design decisions for the Reddit crawler/spider system that tracks Taylor Swift content across multiple subreddits.

## Architecture Principles

### 1. Separation of Concerns
- **Crawler Logic**: Separate from platform-specific adapters (RedditAdapter handles Reddit API)
- **Storage Logic**: Separate from crawling logic (thread_storage handles Neo4j operations)
- **Business Logic**: Separate from data access (creator_service handles entity management)

### 2. Idempotency
- All operations must be idempotent - processing the same post multiple times should not create duplicates
- Use `MERGE` operations in Neo4j to ensure uniqueness
- Check for existing posts before processing

### 3. URL Index System
- Maintain a URL index to track which posts have been seen/processed
- Check URL before processing to avoid duplicate work
- Support batch URL checking for crawler monitoring

### 4. Session Tracking
- Track when crawler last ran using most recent post timestamp
- Estimate activity since last crawl to plan resumption
- Calculate estimated requests needed for catch-up

## Design Decisions

### URL Processing

**Decision**: Extract post ID from URL and use it as primary identifier

**Rationale**:
- Post IDs are stable and unique
- URLs may change format, but IDs remain constant
- Allows checking if post exists without parsing full URL

**Implementation**:
```python
post_id = extract_post_id_from_url(post_url)
# Check if post exists by ID
MATCH (p:Post {id: $post_id})
```

### Metadata Storage

**Decision**: Store all metadata in Neo4j database, not local files

**Rationale**:
- Single source of truth
- Enables cache-hit checking without file I/O
- Supports distributed crawling
- No file system dependencies
- Metadata is queryable via Cypher

**Implementation**:
- All post metadata stored as Post node properties
- Images stored as Image nodes linked to posts
- No JSON/JSONL files for metadata
- Cache checking queries Neo4j directly

### Cache Hit Strategy

**Decision**: Check Neo4j before fetching from Reddit API

**Rationale**:
- Reduces API requests (respects rate limits)
- Faster processing (no network call if cached)
- Prevents duplicate processing
- Can update existing posts without re-fetching

**Implementation**:
```python
# Check cache first
metadata = check_post_metadata_in_neo4j(post_id)
if metadata.get("cache_hit"):
    return metadata  # Use cached data
else:
    # Fetch from Reddit API
    process_post(post_url)
```

### Duplicate Prevention

**Decision**: Use Neo4j MERGE operations and pre-check existence

**Rationale**:
- Prevents duplicate posts in database
- Allows crawler to resume safely after interruption
- Supports incremental crawling

**Implementation**:
```python
# Check before processing
check_query = "MATCH (p:Post {id: $post_id}) RETURN p"

# Use MERGE when storing
MERGE (p:Post {id: $post_id})
```

### Session Tracking

**Decision**: Use most recent post timestamp as proxy for last crawl time

**Rationale**:
- No need for separate crawl log table
- Timestamp is automatically maintained by post creation
- Easy to query and understand

**Implementation**:
```python
# Find most recent post
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
RETURN p.created_utc
ORDER BY p.created_utc DESC
LIMIT 1
```

### Era Tagging

**Decision**: Store era as optional property on Post nodes

**Rationale**:
- Not all posts have identifiable eras
- Can be added later if initially unknown
- Simple to query and filter

**Implementation**:
```cypher
SET p.era = $era,
    p.era_full_name = $era_full_name
```

### Creator Entity Linking

**Decision**: Link posts to Creator entity via `ABOUT` relationship

**Rationale**:
- Enables querying all posts about a creator across subreddits
- Supports future cross-platform aggregation
- Maintains separation between content and entity

**Implementation**:
```cypher
MATCH (p:Post {id: $post_id})
MATCH (c:Creator {slug: $creator_slug})
MERGE (p)-[:ABOUT]->(c)
```

### Subreddit as Source

**Decision**: Link Creator to Subreddit via `HAS_SOURCE` relationship

**Rationale**:
- Tracks which subreddits are monitored for each creator
- Enables discovering all sources for a creator
- Supports adding new sources dynamically

**Implementation**:
```cypher
MATCH (c:Creator {slug: $creator_slug})
MATCH (s:Subreddit {name: $subreddit})
MERGE (c)-[r:HAS_SOURCE]->(s)
```

### Image Handling

**Decision**: Store images as separate nodes linked to posts

**Rationale**:
- Supports gallery posts (multiple images)
- Enables image similarity search
- Allows tracking images across posts

**Implementation**:
```cypher
MERGE (img:Image {url: $url})
MERGE (p:Post {id: $post_id})-[:HAS_IMAGE]->(img)
```

### Error Handling

**Decision**: Continue processing other posts on individual failures

**Rationale**:
- Prevents single post failure from stopping entire crawl
- Logs errors for review
- Allows partial success

**Implementation**:
```python
try:
    process_post(post)
except Exception as e:
    log_error(post, e)
    continue
```

### Rate Limiting

**Decision**: Use delays between requests (configurable per adapter)

**Rationale**:
- Respects Reddit API limits
- Prevents being blocked
- Configurable per platform

**Implementation**:
```python
RedditAdapter(delay_min=2.0, delay_max=5.0)
```

## Crawler Workflow

### 1. Initialization
- Connect to Neo4j
- Initialize platform adapter (RedditAdapter)
- Load subreddit list

### 2. Session Check
- Check last crawl time
- Estimate new posts since last crawl
- Calculate requests needed

### 3. URL Checking
- For each URL, check if already processed
- Skip if already seen
- Process if new

### 4. Post Processing
- Fetch post from Reddit API
- Extract images
- Store in Neo4j
- Link to Creator entity
- Tag with era (if known)
- Link subreddit to Creator

### 5. Error Recovery
- Log errors
- Continue with next post
- Can resume from where it left off

## Data Flow

```
Reddit API
    ↓
RedditAdapter (fetch_thread)
    ↓
Post, Comments, Images
    ↓
store_thread() → Neo4j
    ↓
Creator Linking
    ↓
Era Tagging
    ↓
Subreddit Linking
```

## Monitoring and Observability

### Metrics to Track
- Posts processed per session
- Errors per session
- Time since last crawl
- Estimated backlog
- URLs checked vs processed

### Queries for Monitoring

#### Check crawl status:
```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
RETURN count(p) as total_posts,
       max(p.created_utc) as last_post_time
```

#### Check URL index:
```cypher
MATCH (p:Post {id: $post_id})
RETURN p.id, p.title, p.created_utc
```

## Future Enhancements

1. **Crawl State Persistence**: Store crawl state (last post ID, current page) for exact resumption
2. **Adaptive Rate Limiting**: Adjust delays based on API response times
3. **Parallel Processing**: Process multiple posts concurrently (with rate limiting)
4. **Incremental Updates**: Only fetch posts newer than last crawl
5. **Crawl Scheduling**: Automatic periodic crawls
6. **Health Checks**: Monitor crawler health and alert on issues

## Performance Considerations

- Batch operations where possible (e.g., batch URL checking)
- Use indexes on frequently queried properties (post.id, created_utc)
- Limit query results when possible
- Cache subreddit lookups

## Security Considerations

- Respect robots.txt (future enhancement)
- Implement proper rate limiting
- Handle API errors gracefully
- Don't expose API keys in logs
