# Thread Relationship Mapping - Quick Start

## Your Use Case: Tracking z.ai Discussions Across Subreddits

You want to track when threads from r/LocalLLaMA (like the GLM-4.7 AMA) get discussed in r/SillyTavernAI and other subreddits you follow.

## Quick Solution

### Option 1: Fast Parallel Crawler (Recommended)

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --speed medium \
    --max-threads 100
```

This will:
- Crawl the seed thread and all discovered related threads
- Use parallel processing (3 workers) for speed
- Automatically discover and queue related threads
- Store relationships in Neo4j automatically
- Skip already-crawled threads (resume capability)

### Option 2: Sequential Crawler (Slower but Safe)

```bash
# Step 1: Crawl the original thread
docker compose exec jupyterlab python reddit_thread_crawler.py \
    --permalink "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --limit 1

# Step 2: Recursively crawl related threads
docker compose exec jupyterlab python crawl_related_threads.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --depth 2 \
    --max-threads 50
```

This will:
- Start from the seed thread
- Find all Reddit URLs in comments (like the r/SillyTavernAI discussion)
- Recursively crawl those threads (up to 2 levels deep)
- Build a complete relationship graph

### Step 3: Query Your Knowledge Graph

Find all threads that reference the GLM-4.7 AMA:

```cypher
MATCH (source:Post {id: "1ptxm3x"})<-[:RELATES_TO]-(related:Post)
RETURN 
  related.id,
  related.title,
  related.subreddit,
  related.permalink
ORDER BY related.created_utc DESC
```

Find cross-subreddit relationships for topics you care about:

```cypher
MATCH (p1:Post)-[:RELATES_TO]->(p2:Post)
WHERE p1.subreddit = "LocalLLaMA" 
  AND p2.subreddit = "SillyTavernAI"
RETURN p1.title, p2.title, p1.permalink, p2.permalink
```

## For Subscriber Feeds

Once you have the relationships stored, you can enrich subscriber feeds:

```cypher
// Get a thread with all related discussions
MATCH (main:Post {id: "1ptxm3x"})
OPTIONAL MATCH (main)<-[:RELATES_TO]-(discussed:Post)
WHERE discussed.subreddit IN ["SillyTavernAI", "LocalLLaMA"]
RETURN 
  main,
  collect(discussed) as related_discussions
```

## Continuous Monitoring

To continuously track new relationships:

1. Regularly crawl r/SillyTavernAI (or any subreddit you follow):
   ```bash
   python reddit_thread_crawler.py r/SillyTavernAI --sort new --limit 25
   ```

2. The crawler automatically:
   - Detects Reddit URLs in comments
   - Creates relationships when threads reference each other
   - Stores everything in Neo4j

3. Query for new cross-references:
   ```cypher
   MATCH (p1:Post)-[:RELATES_TO]->(p2:Post)
   WHERE p1.created_utc > datetime() - duration({days: 7})
     AND p1.subreddit = "SillyTavernAI"
   RETURN p1, p2
   ```

## Files Created

- `src/feed/utils/reddit_url_extractor.py` - Detects Reddit URLs
- `src/feed/storage/migrations/007_thread_relationships.cypher` - Graph schema
- `crawl_related_threads.py` - Recursive relationship crawler
- Enhanced `reddit_thread_crawler.py` - Now automatically extracts relationships

## Documentation

See `docs/CROSS_THREAD_RELATIONSHIPS.md` for complete documentation.

