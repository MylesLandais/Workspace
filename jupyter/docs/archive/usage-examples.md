# Thread Relationship System - Usage Examples

## Prerequisites

Make sure your Docker container is running:

```bash
# Check if container is running
docker compose ps

# If not running, start it
./start.sh
# or
docker compose up -d
```

## Example 1: Test URL Extraction

Test that the URL extraction works correctly:

```bash
docker compose exec jupyterlab python test_thread_relationships.py
```

## Example 2: Crawl a Single Thread with Relationship Detection

Crawl the GLM-4.7 AMA thread and automatically detect relationships:

```bash
docker compose exec jupyterlab python reddit_thread_crawler.py \
    --permalink "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --limit 1
```

This will:
- Crawl the full thread with all comments
- Extract Reddit URLs from comments
- Store relationships in Neo4j automatically

## Example 3: Recursively Crawl Related Threads

Start from the GLM-4.7 AMA and follow all related threads:

```bash
docker compose exec jupyterlab python crawl_related_threads.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --depth 2 \
    --max-threads 50
```

This will:
- Crawl the seed thread
- Find the r/SillyTavernAI discussion automatically
- Recursively crawl all discovered related threads
- Build a complete relationship graph

## Example 4: Monitor r/SillyTavernAI for New Discussions

Regularly crawl r/SillyTavernAI to catch new discussions:

```bash
docker compose exec jupyterlab python reddit_thread_crawler.py \
    r/SillyTavernAI \
    --sort new \
    --limit 25
```

The crawler automatically:
- Detects Reddit URLs in comments
- Creates relationships when threads reference each other
- Stores everything in Neo4j

## Example 5: Query Relationships in Neo4j

Once you have data, query the relationships:

### Find all threads that reference the GLM-4.7 AMA:

```cypher
MATCH (source:Post {id: "1ptxm3x"})<-[:RELATES_TO]-(related:Post)
RETURN 
  related.id,
  related.title,
  related.subreddit,
  related.permalink
ORDER BY related.created_utc DESC
```

### Find cross-subreddit relationships:

```cypher
MATCH (p1:Post)-[:RELATES_TO]->(p2:Post)
WHERE p1.subreddit = "LocalLLaMA" 
  AND p2.subreddit = "SillyTavernAI"
RETURN 
  p1.title as original,
  p2.title as discussion,
  p1.permalink as original_link,
  p2.permalink as discussion_link
```

### Get rich context for a thread:

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

## Example 6: Continuous Monitoring Script

Create a script to continuously monitor subreddits:

```bash
# monitor_relationships.sh
#!/bin/bash

while true; do
    echo "Crawling r/SillyTavernAI..."
    docker compose exec jupyterlab python reddit_thread_crawler.py \
        r/SillyTavernAI \
        --sort new \
        --limit 25
    
    echo "Waiting 1 hour before next crawl..."
    sleep 3600
done
```

## Troubleshooting

### Neo4j Connection Issues

Check if Neo4j is running and accessible:

```bash
docker compose exec jupyterlab env | grep NEO4J
```

Verify connection:

```bash
docker compose exec jupyterlab python -c "
from src.feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
print(f'Connected to: {neo4j.uri}')
"
```

### Migration Issues

Run migrations manually if needed:

```bash
docker compose exec jupyterlab python -c "
from src.feed.storage.neo4j_connection import get_connection
from pathlib import Path

neo4j = get_connection()
migration_path = Path('/home/jovyan/workspaces/src/feed/storage/migrations/007_thread_relationships.cypher')

with open(migration_path) as f:
    migration = f.read()
    
statements = [s.strip() for s in migration.split(';') if s.strip()]
for stmt in statements:
    if stmt:
        try:
            neo4j.execute_write(stmt)
            print(f'Executed: {stmt[:50]}...')
        except Exception as e:
            print(f'Warning: {e}')
"
```

### Check What's Been Crawled

Query Neo4j to see what threads have been stored:

```cypher
MATCH (p:Post)
RETURN p.subreddit, count(*) as count
ORDER BY count DESC
LIMIT 10
```

### Check Relationships

See how many relationships have been discovered:

```cypher
MATCH ()-[r:RELATES_TO]->()
RETURN count(r) as total_relationships
```






