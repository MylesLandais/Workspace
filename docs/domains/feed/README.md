# Feed Domain

The Feed domain handles content ingestion, storage, and display in a Scrolller-inspired infinite scroll interface. Content from multiple sources (Reddit, RSS, social media) is normalized into a unified feed experience.

## Overview

The Feed domain is responsible for:

- **Content Ingestion**: Normalizing content from multiple sources into a unified Media model
- **Storage**: Storing content in Neo4j with rich metadata and relationships
- **Display**: Serving content via GraphQL with cursor-based pagination for infinite scroll
- **Deduplication**: Detecting and linking duplicate content across sources
- **Visual Search**: Image similarity search using perceptual hashing and CLIP embeddings

## Key Concepts

### Media Items

Media items represent content from any source (Reddit posts, RSS articles, social media posts). Each media item includes:

- **Metadata**: Title, publish date, source URL, platform
- **Media Properties**: Image dimensions, file size, MIME type, hashes (SHA256, pHash, dHash)
- **Relationships**: Linked to Creator/Handle, Subreddit, User (author), ImageCluster
- **Engagement**: Score, view count, duplicate status

### Feed Query

The feed query uses cursor-based pagination for efficient infinite scroll:

- **Cursor**: ISO 8601 timestamp of the last item
- **Limit**: Number of items per page (default: 20, max: 100)
- **Filters**: Optional filtering by source, date range, media type

### Image Clustering

Images are automatically clustered based on visual similarity:

- **Perceptual Hashing**: pHash and dHash for fast similarity detection
- **CLIP Embeddings**: ML embeddings for semantic visual understanding
- **Duplicate Detection**: Automatic detection of reposts and duplicates
- **Lineage Tracking**: Track image relationships across sources

## Documentation

- [Data Model](./data-model.md) - Neo4j graph structure and Cypher patterns
- [GraphQL Schema](./schema.md) - API types and queries
- **[Mock Data Guide](./mock-data-guide.md)** - Using mock data for frontend development and testing
- **[GraphQL Mock Data Generation](./graphql-mock-data-generation.md)** - Pre-transforming mock data to GraphQL format

## Quick Start

### Query Feed with Cursor Pagination

```typescript
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

const FEED_QUERY = gql`
  query Feed($cursor: String, $limit: Int) {
    feed(cursor: $cursor, limit: $limit) {
      edges {
        node {
          id
          title
          imageUrl
          publishDate
          platform
          handle {
            username
            platform
          }
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

function FeedComponent() {
  const { data, fetchMore } = useQuery(FEED_QUERY, {
    variables: { limit: 20, cursor: null }
  });

  const loadMore = () => {
    if (data?.feed.pageInfo.hasNextPage) {
      fetchMore({
        variables: {
          cursor: data.feed.pageInfo.endCursor
        }
      });
    }
  };

  return (
    <div>
      {data?.feed.edges.map(({ node }) => (
        <MediaItem key={node.id} media={node} />
      ))}
      {data?.feed.pageInfo.hasNextPage && (
        <button onClick={loadMore}>Load More</button>
      )}
    </div>
  );
}
```

### Query Similar Images

```typescript
const SIMILAR_IMAGES_QUERY = gql`
  query SimilarImages($mediaId: ID!) {
    similarImages(mediaId: $mediaId, limit: 10) {
      id
      title
      imageUrl
      similarity
    }
  }
`;
```

### Query Image Lineage

```typescript
const IMAGE_LINEAGE_QUERY = gql`
  query ImageLineage($mediaId: ID!) {
    imageLineage(mediaId: $mediaId) {
      id
      title
      imageUrl
      relationship
    }
  }
`;
```

## GraphQL API

### Queries

- `feed(cursor, limit, filters)` - Get paginated feed with cursor
- `media(id)` - Get single media item by ID
- `similarImages(mediaId, limit)` - Find visually similar images
- `imageLineage(mediaId)` - Get image relationship chain
- `imageCluster(id)` - Get cluster of similar images

### Types

- `Media` - Content item with metadata and relationships
- `FeedConnection` - Cursor-based pagination wrapper
- `FeedEdge` - Individual media item with cursor
- `PageInfo` - Pagination metadata (hasNextPage, endCursor)
- `ImageCluster` - Group of visually similar images

See [GraphQL Schema](./schema.md) for complete type definitions.

## Data Flow

```
1. Content Ingestion
   ↓
2. Normalize to Media format
   ↓
3. Extract image metadata (dimensions, hashes)
   ↓
4. Check for duplicates (SHA256, pHash)
   ↓
5. Store in Neo4j with relationships
   ↓
6. Index in Valkey cache
   ↓
7. Serve via GraphQL with pagination
```

## Performance Considerations

- **Cursor Pagination**: More efficient than offset-based for large datasets
- **Valkey Caching**: Feed queries cached for 5 minutes (300s TTL)
- **Image Indexing**: Perceptual hashes indexed for fast similarity search
- **Lazy Loading**: Media metadata loaded on-demand, not in feed query

## Related Domains

- [Subscriptions](../subscriptions/README.md) - Managing data sources and ingestion rules
- [Architecture Decisions](../../architecture/adr/) - Technical decisions
  - [Cursor Pagination](../../architecture/adr/cursor-pagination.md)
  - [Media Normalization](../../architecture/adr/media-normalization.md)
  - [Duplicate Detection Stacking](../../architecture/adr/duplicate-detection-stacking.md)



