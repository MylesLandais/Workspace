# Subscriptions Domain

The Subscriptions domain manages data sources (Subreddits), organizes them into groups, and configures ingestion rules that control what content enters the system.

## Overview

Users define which Subreddits to ingest through the Feed Manager interface. Sources are organized into FeedGroups, and each source has an IngestRule that filters content (min score, media only, resolution limits).

## Key Concepts

- **Source**: A Subreddit being ingested
- **FeedGroup**: Organizational folder for sources (e.g., "Design", "Memes")
- **IngestRule**: Configuration that filters what gets ingested (minScore, mediaOnly, etc.)
- **SyncStatus**: Tracks last sync time and health of each source

## Documentation

- [Data Model](./data-model.md) - Neo4j graph structure for subscriptions
- [GraphQL Schema](./schema.md) - API types and operations
- [API Reference](./api-reference.md) - Complete API documentation
- [Examples](./examples/) - Code snippets for common operations

## Quick Start

```typescript
// Search for subreddits
const { data } = useQuery(SEARCH_SUBREDDITS, {
  variables: { query: "brooke" }
});

// Subscribe to a source
await subscribeToSource({
  subredditName: "BrookeMonkTheSecond",
  groupId: "design-group-id"
});
```

## Related Domains

- [Feed](../feed/README.md) - Content ingestion and display
- [Architecture Decisions](../../architecture/adr/) - Technical decisions


