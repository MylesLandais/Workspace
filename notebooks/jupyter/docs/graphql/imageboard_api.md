# GraphQL API for 4chan Crawled Data

## Overview

The GraphQL API exposes crawled 4chan thread data from Neo4j and cached data from Valkey, providing a unified interface for clients to query threads, posts, images, and thread relationships.

## Endpoint

- **GraphQL Endpoint**: `http://localhost:8001/graphql`
- **WebSocket**: `ws://localhost:8001/graphql` (for subscriptions)

## Starting the Server

```bash
# From host
./start_graphql_server.sh

# Or directly in container
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py
```

## Schema Types

### ChanThread

```graphql
type ChanThread {
  board: String!
  thread_id: Int!
  title: String
  url: String!
  post_count: Int!
  last_crawled_at: String
  created_at: String
  posts: [ChanPost!]
  linked_threads: [ChanThread!]
}
```

### ChanPost

```graphql
type ChanPost {
  id: String!
  post_no: Int!
  subject: String
  comment: String
  image_url: String
  image_filename: String
  image_hash: String
  image_path: String
  post_time: String
  created_at: String
}
```

### ChanImage

```graphql
type ChanImage {
  hash: String!
  url: String!
  path: String
  filename: String
  thread_id: Int
  board: String
  post_no: Int
}
```

### ChanStats

```graphql
type ChanStats {
  total_threads: Int!
  total_posts: Int!
  total_images: Int!
  boards: [String!]!
  threads_today: Int!
}
```

## Queries

### Get Thread

Get a specific thread with all posts:

```graphql
query {
  chanThread(board: "b", threadId: 944154000) {
    board
    threadId
    title
    url
    postCount
    lastCrawledAt
    posts {
      postNo
      subject
      comment
      imageUrl
      imageHash
    }
  }
}
```

### Get Threads List

Get list of threads with filtering:

```graphql
query {
  chanThreads(filter: {
    board: "b"
    limit: 20
    offset: 0
  }) {
    board
    threadId
    title
    postCount
    lastCrawledAt
  }
}
```

### Get Thread Chain

Get continuation thread chain:

```graphql
query {
  chanThreadChain(board: "b", threadId: 944154000) {
    board
    threadId
    title
    postCount
    url
  }
}
```

### Get Posts

Get posts with filtering:

```graphql
query {
  chanPosts(filter: {
    board: "b"
    threadId: 944154000
    hasImage: true
    limit: 50
  }) {
    postNo
    comment
    imageUrl
    imageHash
    imagePath
  }
}
```

### Get Images

Get images from threads:

```graphql
query {
  chanImages(board: "b", threadId: 944154000, limit: 100) {
    hash
    url
    path
    filename
    threadId
    postNo
  }
}
```

### Get Statistics

```graphql
query {
  chanStats {
    totalThreads
    totalPosts
    totalImages
    boards
    threadsToday
  }
}
```

### Get Cached Data

Get data from Valkey cache:

```graphql
query {
  cachedData(key: "cache:key:name")
}
```

## Example: Complete Thread with Images

```graphql
query GetThreadWithImages {
  thread: chanThread(board: "b", threadId: 944154000) {
    board
    threadId
    title
    postCount
    posts {
      postNo
      comment
      imageUrl
      imageHash
      imagePath
    }
  }
  
  images: chanImages(board: "b", threadId: 944154000) {
    hash
    url
    path
    filename
  }
  
  stats: chanStats {
    totalThreads
    totalPosts
    totalImages
  }
}
```

## Example: Thread Chain Navigation

```graphql
query GetThreadChain {
  chain: chanThreadChain(board: "b", threadId: 944154000) {
    board
    threadId
    title
    postCount
    url
  }
}
```

## Using with cURL

```bash
# Get thread
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ chanThread(board: \"b\", threadId: 944154000) { title postCount posts { postNo comment imageUrl } } }"
  }'

# Get statistics
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ chanStats { totalThreads totalPosts totalImages boards } }"
  }'
```

## Using with Python

```python
import requests

url = "http://localhost:8001/graphql"

query = """
{
  chanThread(board: "b", threadId: 944154000) {
    title
    postCount
    posts {
      postNo
      comment
      imageUrl
    }
  }
}
"""

response = requests.post(url, json={"query": query})
data = response.json()
print(data)
```

## Using with JavaScript/TypeScript

```javascript
const query = `
  query {
    chanThread(board: "b", threadId: 944154000) {
      title
      postCount
      posts {
        postNo
        comment
        imageUrl
      }
    }
  }
`;

fetch('http://localhost:8001/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Data Sources

- **Neo4j**: Threads, posts, images, relationships
- **Valkey**: Cached data, session state, rate limiting
- **File System**: Image paths organized by board/thread

## Performance

- Queries are optimized with Neo4j indexes
- Valkey cache reduces database load
- Pagination supported via `limit` and `offset`
- Images can be filtered by thread or board

## Next Steps

- Add subscriptions for real-time thread updates
- Add image deduplication queries
- Add search/filter by post content
- Add board statistics per board



