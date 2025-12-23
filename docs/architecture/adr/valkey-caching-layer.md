# Valkey Caching Layer

## Status

Accepted

## Context

As the application scales to handle multiple content sources, real-time reading progress, AI agent context, and complex graph queries, we need a high-performance caching layer to:

- Reduce load on Neo4j (especially important with Aura free tier limits)
- Provide sub-millisecond response times for hot data paths
- Support real-time features like reading progress sync and collaborative features
- Queue and rate-limit scraping operations
- Cache expensive AI operations and graph computations

Neo4j alone cannot efficiently handle all these use cases, especially for frequently accessed data that changes often.

## Decision

Use Valkey (Redis-compatible in-memory data store) as a caching and real-time data layer, positioned between the application and Neo4j.

## Rationale

**Performance**: Valkey provides sub-millisecond latency for hot data paths (feed content, session state, reading progress). This is critical for responsive user experience.

**Real-Time Features**: Built-in pub/sub, sorted sets, and atomic operations enable real-time reading progress sync, collaborative features, and live updates without polling.

**Rate Limiting & Queues**: Native support for rate limiting patterns and job queues needed for scraping operations and feed polling.

**Cost Efficiency**: Offloads frequent reads from Neo4j, reducing query costs and staying within Aura free tier limits longer.

**AI Context Caching**: Store embeddings, summaries, and conversation history in Valkey with TTL, reducing expensive LLM API calls.

**Redis Compatibility**: Valkey is Redis-compatible, so we can use existing Redis tooling, libraries, and patterns while benefiting from Valkey's open-source licensing.

## Consequences

**Positive**:
- Dramatically faster response times for frequently accessed data
- Reduces Neo4j query load, extending Aura free tier viability
- Enables real-time features (progress sync, collaborative reading)
- Supports complex caching patterns (write-through, lazy loading, TTL)
- Pub/sub enables event-driven architecture
- Bloom filters for efficient deduplication

**Negative**:
- Additional infrastructure component to manage
- Data consistency complexity (cache invalidation, write-through patterns)
- Memory costs scale with cache size
- Potential data loss if Valkey crashes (mitigated by write-through to Neo4j)
- Learning curve for team members unfamiliar with Redis patterns

**Neutral**:
- Requires connection pooling and health monitoring
- Cache warming strategies needed for optimal performance
- Monitoring cache hit rates and memory usage

## Alternatives Considered

**PostgreSQL for Caching**: Could use PostgreSQL with unlogged tables, but lacks pub/sub, sorted sets, and atomic operations needed for real-time features.

**In-Memory Application Cache**: Node.js in-memory cache (e.g., node-cache) doesn't persist across restarts, doesn't support pub/sub, and can't be shared across instances.

**Neo4j Only**: Relying solely on Neo4j would hit Aura free tier limits quickly and provide slower response times for hot data.

**Memcached**: Lacks advanced data structures (sorted sets, pub/sub) needed for queues and real-time features.

## Implementation Notes

### Cache Strategies

**1. Feed Content Cache**

```redis
# Hot content (frequently accessed items)
SET feed:{source_id}:latest {json_data} EX 300
ZADD feed:{source_id}:items {timestamp} {item_id}

# User reading queue with priority scoring
ZADD user:{user_id}:queue {priority_score} {item_id}
LPUSH user:{user_id}:recent_reads {item_id}
```

**2. Session & Real-Time State**

```redis
# Reading progress sync (faster than Neo4j for frequent updates)
HSET reading:{user_id}:{item_id} position 1234 updated_at {timestamp}

# Active annotations (before persisting to Neo4j)
SADD annotations:{user_id}:pending {annotation_json}

# Typing indicators for collaborative features
SETEX collab:{item_id}:active:{user_id} 10 "typing"
```

**3. Rate Limiting & Scraping Queue**

```redis
# Scraping job queue
LPUSH scrape:queue {job_json}
ZADD scrape:scheduled {next_run_timestamp} {source_id}

# Rate limiting per source domain
INCR ratelimit:{domain}:requests EX 60
```

**4. AI Agent Context Cache**

```redis
# Cache LiteLLM responses (with openrouter keys)
SET ai:summary:{item_id} {summary} EX 3600
HSET ai:embeddings:{item_id} model {model_name} vector {vector_bytes}

# Agent conversation history
LPUSH agent:{session_id}:history {message_json}
EXPIRE agent:{session_id}:history 1800
```

**5. Computed Graph Metrics**

```redis
# Cache expensive graph queries
SET graph:user:{user_id}:recommendations {json} EX 600
SET graph:topic:{topic_id}:trending {json} EX 1800

# Leaderboards (most-read sources, trending topics)
ZADD trending:sources {read_count} {source_id}
ZADD trending:topics:daily {score} {topic_id}
```

**6. Media Thumbnail and Image Caching**

```redis
# Thumbnail cache (multiple sizes)
SET media:thumbnail:{media_id}:small {thumbnail_url} EX 86400
SET media:thumbnail:{media_id}:medium {thumbnail_url} EX 86400
SET media:thumbnail:{media_id}:large {thumbnail_url} EX 86400

# Perceptual hash index for fast similarity lookup
SET media:phash:{perceptual_hash} {media_id}
ZADD media:phash:similarity:{media_id} {hamming_distance} {similar_media_id}

# Visual embedding cache (ML-generated)
HSET media:embedding:{media_id} model {model_name} vector {vector_bytes} EX 604800

# MD5 deduplication index
SET media:md5:{md5_hash} {media_id}
BF.ADD seen:md5 {md5_hash}

# Board feed cache (Pinterest-style collections)
SET board:feed:{board_id} {json_items} EX 300
ZADD board:items:{board_id} {score} {item_id}
```

**7. Media Search Result Caching**

```redis
# Tag search results (expensive boolean queries)
SET search:tags:{query_hash} {json_results} EX 600

# Dimensional search results
SET search:dims:width:{width}:height:{height} {json_results} EX 300

# Visual similarity search results
SET search:visual:{media_id} {json_similar_items} EX 1800

# Combined search (tags + dimensions + visual)
SET search:combined:{query_hash} {json_results} EX 300
```

### Integration Patterns

**Write-Through Cache**:

```typescript
async function saveAnnotation(userId: string, itemId: string, highlight: string) {
  // 1. Write to Neo4j (source of truth)
  await neo4j.createAnnotation(userId, itemId, highlight);
  
  // 2. Invalidate Valkey cache
  await valkey.del(`annotations:${userId}:${itemId}`);
  
  // 3. Publish event for real-time updates
  await valkey.publish(`item:${itemId}:updates`, JSON.stringify({
    type: 'annotation_added',
    userId,
    timestamp: Date.now()
  }));
}
```

**Lazy Loading Cache**:

```typescript
async function getUserReadingList(userId: string) {
  // 1. Check Valkey first
  const cached = await valkey.get(`user:${userId}:reading_list`);
  if (cached) {
    return JSON.parse(cached);
  }
  
  // 2. Query Neo4j
  const items = await neo4j.getReadingList(userId);
  
  // 3. Populate cache with 5-minute TTL
  await valkey.setex(
    `user:${userId}:reading_list`,
    300,
    JSON.stringify(items)
  );
  
  return items;
}
```

**Pub/Sub for Real-Time Updates**:

```typescript
// Publisher (when new content arrives)
await valkey.publish(`feed:${sourceId}:updates`, JSON.stringify({
  itemId,
  timestamp: Date.now()
}));

// Subscriber (frontend WebSocket handler)
const subscriber = valkey.duplicate();
await subscriber.subscribe(`feed:${sourceId}:updates`);
subscriber.on('message', (channel, message) => {
  // Push update to connected clients via WebSocket
  websocketServer.broadcast(JSON.parse(message));
});
```

### Bloom Filters for Deduplication

```redis
# Check if URL already processed
BF.ADD seen:urls {url}
BF.EXISTS seen:urls {url}
```

### Performance Optimization

- Use pipeline commands to reduce round trips
- Leverage Lua scripts for atomic operations
- Monitor memory with `INFO memory` and set `maxmemory-policy`
- Use Redis Cluster mode when outgrowing single instance
- Set appropriate TTLs to prevent memory bloat

### Media-Specific Caching Patterns

**Thumbnail Generation Cache**:

```python
async def get_thumbnail(media_id: str, size: str = "medium") -> str:
    """Get or generate thumbnail with caching."""
    cache_key = f"media:thumbnail:{media_id}:{size}"
    
    # Check cache
    cached = await valkey.get(cache_key)
    if cached:
        return cached
    
    # Generate thumbnail
    media_item = await neo4j.get_media_item(media_id)
    thumbnail_url = await generate_thumbnail(media_item.url, size)
    
    # Cache for 24 hours
    await valkey.setex(cache_key, 86400, thumbnail_url)
    
    return thumbnail_url
```

**Visual Similarity Index**:

```python
async def cache_visual_similarity(media_id: str, similar_items: list[dict]):
    """Cache visual similarity results for fast lookup."""
    for item in similar_items:
        # Store in sorted set by similarity score
        await valkey.zadd(
            f"media:phash:similarity:{media_id}",
            {item["id"]: item["similarity"]}
        )
    
    # Set TTL
    await valkey.expire(f"media:phash:similarity:{media_id}", 3600)
```

**Board Feed Caching**:

```python
async def get_board_feed(board_id: str) -> list[dict]:
    """Get board feed with caching."""
    cache_key = f"board:feed:{board_id}"
    
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query Neo4j for board items
    items = await neo4j.get_board_items(board_id)
    
    # Cache for 5 minutes
    await valkey.setex(cache_key, 300, json.dumps(items))
    
    return items
```

## References

- [Valkey Documentation](https://valkey.io/docs/)
- [Redis Patterns](https://redis.io/docs/manual/patterns/)
- [ADR: Neo4j Graph Database](./neo4j-graph-database.md)
- [ADR: Neo4j Aura Optimization](./neo4j-aura-optimization.md)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)

