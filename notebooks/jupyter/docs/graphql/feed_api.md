# Feed Monitor GraphQL API Documentation

## Overview

The Feed Monitor GraphQL API provides real-time access to collected Reddit posts with WebSocket subscriptions for live updates.

## Endpoint

- **GraphQL Endpoint**: `http://localhost:8001/graphql`
- **WebSocket**: `ws://localhost:8001/graphql` (for subscriptions)

## Starting the Server

```bash
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py
```

## Schema Types

### Post
```graphql
type Post {
  id: String!
  title: String!
  created_utc: String!
  score: Int!
  num_comments: Int!
  upvote_ratio: Float!
  over_18: Boolean!
  url: String!
  selftext: String!
  permalink: String
  subreddit: String!
  author: String
  is_image: Boolean!
  image_url: String
}
```

### FeedList
```graphql
type FeedList {
  subreddit: String!
  posts: [Post!]!
  total_count: Int!
}
```

### FeedStats
```graphql
type FeedStats {
  total_posts: Int!
  total_subreddits: Int!
  total_users: Int!
  posts_today: Int!
}
```

### Subreddit
```graphql
type Subreddit {
  name: String!
  post_count: Int!
}
```

### PostFilter
```graphql
input PostFilter {
  subreddit: String
  min_score: Int
  is_image: Boolean
  limit: Int = 20
  offset: Int = 0
}
```

## Queries

### Get Statistics

```graphql
query {
  stats {
    total_posts
    total_subreddits
    total_users
    posts_today
  }
}
```

**Response:**
```json
{
  "data": {
    "stats": {
      "total_posts": 20,
      "total_subreddits": 2,
      "total_users": 5,
      "posts_today": 3
    }
  }
}
```

### Get All Subreddits

```graphql
query {
  subreddits {
    name
    post_count
  }
}
```

**Response:**
```json
{
  "data": {
    "subreddits": [
      {
        "name": "BrookeMonkTheSecond",
        "post_count": 10
      },
      {
        "name": "BestOfBrookeMonk",
        "post_count": 10
      }
    ]
  }
}
```

### Get Feed Lists

```graphql
query {
  feedList(subreddit: "BrookeMonkTheSecond") {
    subreddit
    total_count
    posts {
      id
      title
      score
      num_comments
      url
      image_url
      is_image
      author
      created_utc
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "feedList": [
      {
        "subreddit": "BrookeMonkTheSecond",
        "total_count": 10,
        "posts": [
          {
            "id": "anc6w05ekr8g1",
            "title": "Brooke monk",
            "score": 7,
            "num_comments": 1,
            "url": "https://i.redd.it/anc6w05ekr8g1.jpeg",
            "image_url": "https://i.redd.it/anc6w05ekr8g1.jpeg",
            "is_image": true,
            "author": "letsgoon45",
            "created_utc": "2025-12-22T08:14:39Z"
          }
        ]
      }
    ]
  }
}
```

### Get Posts with Filtering

```graphql
query {
  posts(filter: {
    subreddit: "BrookeMonkTheSecond"
    is_image: true
    min_score: 50
    limit: 10
  }) {
    id
    title
    score
    image_url
    subreddit
  }
}
```

## Subscriptions (Real-time Updates)

### Subscribe to Feed Updates

```graphql
subscription {
  feedUpdates(subreddit: "BrookeMonkTheSecond") {
    id
    title
    score
    url
    image_url
    is_image
    subreddit
    created_utc
  }
}
```

**How it works:**
- Establishes a WebSocket connection
- Polls for new posts every 5 seconds
- Yields new posts as they appear
- Continues until connection is closed

## Client Examples

### JavaScript/TypeScript (Apollo Client)

```typescript
import { ApolloClient, InMemoryCache, gql } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';

// HTTP link for queries
const httpLink = new HttpLink({
  uri: 'http://localhost:8001/graphql',
});

// WebSocket link for subscriptions
const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:8001/graphql',
}));

// Split link: queries over HTTP, subscriptions over WebSocket
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink,
);

const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});

// Query example
const GET_STATS = gql`
  query GetStats {
    stats {
      total_posts
      total_subreddits
      posts_today
    }
  }
`;

// Subscription example
const FEED_UPDATES = gql`
  subscription FeedUpdates($subreddit: String) {
    feedUpdates(subreddit: $subreddit) {
      id
      title
      score
      image_url
      subreddit
    }
  }
`;

// Use in component
function FeedMonitor() {
  const { data: stats } = useQuery(GET_STATS);
  const { data: updates } = useSubscription(FEED_UPDATES, {
    variables: { subreddit: 'BrookeMonkTheSecond' }
  });

  return (
    <div>
      <h1>Total Posts: {stats?.stats.total_posts}</h1>
      {updates?.feedUpdates && (
        <div>New post: {updates.feedUpdates.title}</div>
      )}
    </div>
  );
}
```

### Python Client

```python
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport
from gql.transport.aiohttp import AIOHTTPTransport

# HTTP transport for queries
http_transport = AIOHTTPTransport(url="http://localhost:8001/graphql")
http_client = Client(transport=http_transport, fetch_schema_from_transport=True)

# WebSocket transport for subscriptions
ws_transport = WebsocketsTransport(url="ws://localhost:8001/graphql")
ws_client = Client(transport=ws_transport, fetch_schema_from_transport=True)

# Query
query = gql("""
  query {
    stats {
      total_posts
      total_subreddits
    }
  }
""")

result = http_client.execute(query)
print(result)

# Subscription
subscription = gql("""
  subscription {
    feedUpdates {
      id
      title
      score
      image_url
    }
  }
""")

for result in ws_client.subscribe(subscription):
    print(f"New post: {result['feedUpdates']['title']}")
```

### cURL Examples

```bash
# Query
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ stats { total_posts total_subreddits } }"
  }'

# Query with variables
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($subreddit: String) { feedList(subreddit: $subreddit) { subreddit posts { title score } } }",
    "variables": { "subreddit": "BrookeMonkTheSecond" }
  }'
```

## Mock Data

The API includes mock data based on collected posts:

### BrookeMonkTheSecond (10 posts)
- All posts are images (i.redd.it URLs)
- Date range: 2025-12-20 to 2025-12-22
- Top post: "Brooke monk tease" (249 upvotes)

### BestOfBrookeMonk (10 posts)
- All posts are Reddit galleries
- Date range: 2025-12-16 to 2025-12-21
- Top post: "Brooke Monk" (27 upvotes)

## Image Display

All posts include:
- `is_image`: Boolean indicating if post contains an image
- `image_url`: Direct URL to image (for i.redd.it) or gallery URL
- `url`: Original post URL

For client display:
```typescript
{post.is_image && (
  <img 
    src={post.image_url} 
    alt={post.title}
    loading="lazy"
  />
)}
```

## Error Handling

GraphQL returns errors in a standard format:
```json
{
  "errors": [
    {
      "message": "Error message",
      "locations": [{"line": 2, "column": 3}],
      "path": ["queryName"]
    }
  ],
  "data": null
}
```

## Performance Considerations

- Subscriptions poll every 5 seconds (configurable)
- Queries are optimized with Neo4j indexes
- Use `limit` and `offset` for pagination
- Filter by `subreddit` to reduce query scope

## Security

- CORS enabled for all origins (configure for production)
- No authentication required (add for production)
- Rate limiting recommended for production use







