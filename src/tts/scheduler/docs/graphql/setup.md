# GraphQL API Setup for Crawled Data

## Overview

The GraphQL API exposes crawled data from:
- **Neo4j**: Threads, posts, images, relationships
- **Valkey**: Cached data, session state
- **File System**: Image paths

## Quick Start

### 1. Start the GraphQL Server

```bash
./start_graphql_server.sh
```

Or manually:
```bash
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py
```

### 2. Access the API

- **GraphQL Endpoint**: http://localhost:8001/graphql
- **WebSocket**: ws://localhost:8001/graphql (for subscriptions)

### 3. Test the API

```bash
# Get 4chan statistics
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ chanStats { totalThreads totalPosts totalImages boards } }"}'

# Get a specific thread
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ chanThread(board: \"b\", threadId: 944154000) { title postCount posts { postNo comment imageUrl } } }"}'
```

## Available Queries

### 4chan Data

- `chanThread(board, threadId)` - Get specific thread
- `chanThreads(filter)` - List threads with filtering
- `chanThreadChain(board, threadId)` - Get continuation thread chain
- `chanPosts(filter)` - Get posts with filtering
- `chanImages(board, threadId, limit)` - Get images
- `chanStats()` - Get statistics

### Reddit Data (existing)

- `stats()` - Feed statistics
- `subreddits()` - List subreddits
- `feedList(subreddit)` - Get feed lists
- `posts(filter)` - Get posts with filtering

### Cache Data

- `cachedData(key)` - Get data from Valkey cache

## Example Queries

See `docs/GRAPHQL_4CHAN_API.md` for complete examples and documentation.

## Dependencies

- `strawberry-graphql[fastapi]` - GraphQL framework
- `fastapi` - Web framework
- `uvicorn` - ASGI server

All dependencies should be installed in the container.

## Troubleshooting

If you get import errors:
```bash
docker exec jupyter pip install strawberry-graphql[fastapi]
```

If Neo4j connection fails:
- Check `.env` file has correct `NEO4J_URI`
- Verify Neo4j container is running: `docker ps | grep neo4j`

If Valkey connection fails:
- Check `.env` file has correct `VALKEY_URI`
- Verify Valkey container is running: `docker ps | grep valkey`



