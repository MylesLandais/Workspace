# Subscriptions Domain

The Subscriptions domain manages content sources (Creators, Handles, Subreddits), organizes them into groups, and configures ingestion rules that control what content enters the system.

## Overview

The Subscriptions domain enables users to:

- **Discover Sources**: Search for creators, subreddits, and handles across platforms
- **Organize Sources**: Group sources into FeedGroups for better organization
- **Configure Ingestion**: Set rules that filter content (min score, media only, resolution)
- **Monitor Status**: Track sync status, health, and ingestion metrics

## Key Concepts

### Creator

A Creator represents a person or entity that produces content. Creators can have multiple Handles across different platforms.

- **Identity**: Name, display name, slug, bio, avatar
- **Verification**: Verified status for trusted sources
- **Organization**: Belongs to FeedGroups for organization
- **Bunny Extensions**: Aliases, context keywords, image pools, relationships

### Handle

A Handle represents a specific account on a platform (e.g., Reddit subreddit, YouTube channel, Twitter account).

- **Platform**: REDDIT, YOUTUBE, TWITTER, INSTAGRAM, TIKTOK, VSCO
- **Status**: ACTIVE, SUSPENDED, ABANDONED
- **Ingestion**: Linked to IngestRule for content filtering
- **Metrics**: Media count, last sync time, sync status

### FeedGroup

Organizational container for grouping related creators/sources.

- **Organization**: Name, creation date
- **Creators**: List of creators in the group
- **Management**: Create, delete, move creators between groups

### IngestRule

Configuration that filters what content gets ingested from a Handle.

- **minScore**: Minimum upvote/engagement score
- **mediaOnly**: Only ingest posts with media (images/videos)
- **minResolution**: Minimum image resolution (e.g., "1920x1080")

### RejectedItem

Items that were rejected by ingestion rules, available for review.

- **Reason**: Why the item was rejected
- **Metadata**: URL, thumbnail, rejection timestamp
- **Review**: Can be force-imported if needed

## Documentation

- [Data Model](./data-model.md) - Neo4j graph structure for subscriptions
- [GraphQL Schema](./schema.md) - API types and operations
- [User Stories](./user-stories.md) - Feature requirements and use cases
- [Data Sources](./data-sources.md) - Supported platforms and ingestion methods

## Quick Start

### Search for Creators

```typescript
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

const SEARCH_CREATORS_QUERY = gql`
  query SearchCreators($query: String, $limit: Int) {
    creators(query: $query, limit: $limit) {
      id
      slug
      name
      displayName
      verified
      handles {
        platform
        username
        status
      }
    }
  }
`;

function CreatorSearch() {
  const { data } = useQuery(SEARCH_CREATORS_QUERY, {
    variables: { query: "brooke", limit: 20 }
  });

  return (
    <div>
      {data?.creators.map(creator => (
        <CreatorCard key={creator.id} creator={creator} />
      ))}
    </div>
  );
}
```

### Add a Handle to a Creator

```typescript
const ADD_HANDLE_MUTATION = gql`
  mutation AddHandle(
    $creatorId: ID!
    $platform: Platform!
    $username: String!
    $url: String!
  ) {
    addHandle(
      creatorId: $creatorId
      platform: $platform
      username: $username
      url: $url
    ) {
      id
      platform
      username
      status
    }
  }
`;
```

### Update Ingestion Rule

```typescript
const UPDATE_RULE_MUTATION = gql`
  mutation UpdateIngestRule(
    $handleId: ID!
    $rule: IngestRuleInput!
  ) {
    updateIngestRule(handleId: $handleId, rule: $rule) {
      id
      minScore
      mediaOnly
      minResolution
    }
  }
`;

// Usage
await updateIngestRule({
  variables: {
    handleId: "handle-123",
    rule: {
      minScore: 50,
      mediaOnly: true,
      minResolution: "1920x1080"
    }
  }
});
```

### Get Pipeline Status

```typescript
const PIPELINE_STATUS_QUERY = gql`
  query PipelineStatus {
    getPipelineStatus {
      activeSyncs {
        handleName
        platform
        newItemsCount
        status
      }
    }
  }
`;
```

## GraphQL API

### Queries

- `creator(slug)` - Get creator by slug
- `creators(query, limit)` - Search creators
- `searchHandles(query, platform)` - Search for handles
- `discoverHandles(anchorUrl)` - Discover handles from a URL
- `getFeedGroups` - Get all feed groups
- `getRejectedItems(handleId, limit)` - Get rejected items for review
- `getPipelineStatus` - Get current ingestion pipeline status

### Mutations

- `createCreator(name, displayName)` - Create a new creator
- `updateCreator(creatorId, ...)` - Update creator details
- `addHandle(creatorId, platform, username, url)` - Add a handle to a creator
- `verifyHandle(handleId)` - Mark handle as verified
- `updateHandleStatus(handleId, status)` - Update handle status
- `removeHandle(handleId)` - Remove a handle
- `updateIngestRule(handleId, rule)` - Update ingestion rules
- `forceImportItem(itemId)` - Force import a rejected item
- `createFeedGroup(name)` - Create a new feed group
- `deleteFeedGroup(groupId)` - Delete a feed group
- `moveCreatorToGroup(creatorId, groupId)` - Move creator to group

See [GraphQL Schema](./schema.md) for complete type definitions.

## Data Flow

```
1. User searches for creator/handle
   ↓
2. System discovers handles from anchor URL (optional)
   ↓
3. User creates/selects creator
   ↓
4. User adds handles to creator
   ↓
5. User configures ingestion rules
   ↓
6. Ingestion pipeline syncs handles
   ↓
7. Content filtered by rules
   ↓
8. Accepted content → Feed domain
   Rejected content → RejectedItems for review
```

## Platform Support

Currently supported platforms:

- **REDDIT**: Subreddit scraping (no API access)
- **YOUTUBE**: Channel ingestion (planned)
- **TWITTER**: Account ingestion (planned)
- **INSTAGRAM**: Profile ingestion (planned)
- **TIKTOK**: Account ingestion (planned)
- **VSCO**: Profile ingestion (planned)

See [Data Sources](./data-sources.md) for platform-specific details.

## Related Domains

- [Feed](../feed/README.md) - Content ingestion and display
- [Architecture Decisions](../../architecture/adr/) - Technical decisions
  - [Creator Handle Model](../../architecture/adr/creator-handle-model.md)
  - [Multi-Source Entities](../../architecture/adr/multi-source-entities.md)
  - [Unified Ingestion Layer](../../architecture/adr/unified-ingestion-layer.md)






