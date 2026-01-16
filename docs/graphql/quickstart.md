# Quick Start - GraphQL API

## Start the GraphQL Server

```bash
./start_graphql_server.sh
```

Or directly:
```bash
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py
```

## Access Points

- **GraphQL Endpoint**: http://localhost:8001/graphql
- **WebSocket**: ws://localhost:8001/graphql (for subscriptions)

## Test with cURL

```bash
# Get statistics
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ stats { total_posts total_subreddits } }"}'

# Get feed list
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ feedList { subreddit posts { title score image_url } } }"}'
```

## Use the Example Client

Open `examples/graphql_client_example.html` in a browser to see:
- Real-time statistics
- Feed lists with images
- Live subscription updates

## Full Documentation

See `docs/FEED_GRAPHQL_API.md` for complete API documentation including:
- All query types
- Subscription examples
- Client code examples (JavaScript, Python)
- Mock data structure







