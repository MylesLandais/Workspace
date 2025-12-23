# Feed Domain

The Feed domain handles post ingestion, storage, and display in a Scrolller-like infinite scroll interface.

## Overview

Posts are ingested from Reddit subreddits, stored in Neo4j with rich metadata, and served via GraphQL to the Astro frontend. The feed view uses virtual scrolling for performance with large datasets.

## Key Concepts

- **Posts**: Individual Reddit posts with images, metadata, and relationships
- **Media**: Separate nodes for images/videos, linked to posts
- **Feed Query**: Cursor-based pagination for infinite scroll
- **Denormalization**: Image URLs stored on Post nodes for fast queries

## Documentation

- [Data Model](./data-model.md) - Neo4j graph structure and Cypher patterns
- [GraphQL Schema](./schema.md) - API types and queries
- [API Reference](./api-reference.md) - Complete API documentation
- [Examples](./examples/) - Runnable code snippets

## Quick Start

```typescript
// Query feed with cursor pagination
const { data } = useQuery(INFINITE_FEED_QUERY, {
  variables: { limit: 20, cursor: null }
});

// Load more
fetchMore({ variables: { cursor: data.feed.pageInfo.endCursor } });
```

## Related Domains

- [Subscriptions](../subscriptions/README.md) - Managing data sources
- [Architecture Decisions](../../architecture/adr/) - Technical decisions


