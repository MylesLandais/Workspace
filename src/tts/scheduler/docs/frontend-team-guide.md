# Frontend & UX Team Guide

## Essential Files for Frontend Development

### 1. API Documentation & Schema

**📄 `docs/FEED_GRAPHQL_API.md`**
- **Purpose**: Complete GraphQL API reference
- **Contains**: 
  - All query types and fields
  - Subscription examples
  - Client code examples (JavaScript/TypeScript)
  - Response formats
  - Error handling
- **Use for**: Understanding available data, building queries, integration

**📄 `src/feed/graphql/schema.py`**
- **Purpose**: GraphQL schema definition (source of truth)
- **Contains**: Type definitions, queries, subscriptions
- **Use for**: Understanding data structure, type safety, generating TypeScript types

### 2. Mock Data & Examples

**📄 `src/feed/graphql/mock_data.py`**
- **Purpose**: Realistic mock data based on collected posts
- **Contains**: 
  - 10 posts from r/BrookeMonkTheSecond (all images)
  - 10 posts from r/BestOfBrookeMonk (all galleries)
  - Complete data structures with image URLs
- **Use for**: 
  - Development without backend
  - Testing UI components
  - Understanding data format
  - Creating design mockups

**📄 `examples/graphql_client_example.html`**
- **Purpose**: Working example client implementation
- **Contains**: 
  - Complete HTML/JavaScript example
  - GraphQL queries and subscriptions
  - Image display logic
  - Real-time updates
- **Use for**: 
  - Reference implementation
  - Understanding WebSocket subscriptions
  - Testing API connectivity

### 3. Data Models

**📄 `src/feed/models/post.py`**
- **Purpose**: Post data model (Pydantic)
- **Contains**: Field definitions, types, validation
- **Use for**: Understanding post structure, generating TypeScript interfaces

**📄 `src/feed/models/subreddit.py`**
- **Purpose**: Subreddit data model
- **Use for**: Understanding subreddit structure

**📄 `src/feed/models/user.py`**
- **Purpose**: User data model
- **Use for**: Understanding user structure

### 4. Quick Start & Setup

**📄 `QUICKSTART_GRAPHQL.md`**
- **Purpose**: Quick reference for starting the API
- **Contains**: Server startup, test commands, access points
- **Use for**: Setting up local development environment

**📄 `start_graphql_server.sh`**
- **Purpose**: Script to start GraphQL server
- **Use for**: Easy server startup

## Recommended File Package for Frontend Teams

### Minimum Package (Essential)
```
docs/FEED_GRAPHQL_API.md          # API documentation
src/feed/graphql/mock_data.py      # Mock data
examples/graphql_client_example.html  # Example implementation
```

### Complete Package (Recommended)
```
docs/FEED_GRAPHQL_API.md          # Full API docs
src/feed/graphql/schema.py        # Schema source
src/feed/graphql/mock_data.py     # Mock data
src/feed/models/post.py           # Data models
examples/graphql_client_example.html  # Working example
QUICKSTART_GRAPHQL.md             # Setup guide
```

## Key Information for Frontend Teams

### GraphQL Endpoint
- **URL**: `http://localhost:8001/graphql`
- **WebSocket**: `ws://localhost:8001/graphql`

### Available Data

#### Posts Include:
- `id`: Unique identifier
- `title`: Post title
- `score`: Upvote count
- `num_comments`: Comment count
- `upvote_ratio`: Upvote ratio (0.0-1.0)
- `url`: Original post URL
- `image_url`: Direct image URL (if image post)
- `is_image`: Boolean flag for image posts
- `subreddit`: Subreddit name
- `author`: Username (may be null)
- `created_utc`: ISO timestamp

#### Image Posts
- Direct images: `https://i.redd.it/...` URLs
- Galleries: `https://www.reddit.com/gallery/...` URLs
- Check `is_image` flag before displaying images

### Example Queries

```graphql
# Get statistics
query {
  stats {
    total_posts
    total_subreddits
    posts_today
  }
}

# Get feed list with images
query {
  feedList(subreddit: "BrookeMonkTheSecond") {
    subreddit
    posts {
      id
      title
      score
      image_url
      is_image
    }
  }
}

# Subscribe to real-time updates
subscription {
  feedUpdates {
    id
    title
    image_url
    score
  }
}
```

## Mock Data Structure

The mock data includes:
- **BrookeMonkTheSecond**: 10 image posts (i.redd.it URLs)
- **BestOfBrookeMonk**: 10 gallery posts (reddit.com/gallery URLs)
- All posts have complete metadata (scores, comments, dates, authors)

## Integration Examples

### Apollo Client (React)
See `docs/FEED_GRAPHQL_API.md` for complete Apollo Client setup

### Vanilla JavaScript
See `examples/graphql_client_example.html` for working example

### TypeScript Types
Generate from GraphQL schema using tools like:
- `graphql-codegen`
- `@graphql-codegen/typescript`

## Design Considerations

### Image Display
- Use `is_image` flag to determine if post has image
- Use `image_url` for direct image display
- Handle gallery URLs (may need additional API call)
- Implement lazy loading for performance

### Real-time Updates
- Use WebSocket subscriptions for live feed
- Poll every 5 seconds (configurable)
- Handle connection errors gracefully

### Data Filtering
- Filter by subreddit
- Filter by image posts (`is_image: true`)
- Filter by minimum score
- Pagination with `limit` and `offset`

## Questions?

Refer to:
- `docs/FEED_GRAPHQL_API.md` for detailed API documentation
- `examples/graphql_client_example.html` for working code examples
- `src/feed/graphql/schema.py` for schema definition







