# Subscriptions GraphQL Schema

GraphQL types and operations for the Subscriptions domain.

## Types

### FeedGroup

Organizational container for sources.

**Fields**:
- `id` (ID!): Unique identifier
- `name` (String!): Group name
- `sources` ([Source!]!): Sources in this group
- `createdAt` (DateTime!): Creation timestamp

### Source

A Subreddit being ingested.

**Fields**:
- `id` (ID!): Unique identifier
- `name` (String!): Display name
- `subredditName` (String!): Reddit subreddit name
- `iconUrl` (String): Subreddit icon URL
- `isPaused` (Boolean!): Whether ingestion is paused
- `lastSynced` (DateTime): Last sync timestamp
- `mediaCount` (Int!): Total items ingested
- `ingestRule` (IngestRule): Filtering rule
- `group` (FeedGroup): Parent group
- `subreddit` (Subreddit!): Subreddit node

### IngestRule

Configuration for filtering ingested content.

**Fields**:
- `id` (ID!): Unique identifier
- `minScore` (Int!): Minimum upvote score
- `mediaOnly` (Boolean!): Only ingest media posts
- `minResolution` (String): Minimum resolution filter

### RejectedItem

Item rejected by ingestion rules.

**Fields**:
- `id` (ID!): Unique identifier
- `url` (String!): Original post URL
- `thumbnailUrl` (String): Thumbnail image
- `reason` (String!): Rejection reason
- `rejectedAt` (DateTime!): Rejection timestamp
- `source` (Source!): Source that rejected this item

### PipelineStatus

Current status of ingestion pipeline.

**Fields**:
- `activeSyncs` ([ActiveSync!]!): Currently running syncs

### ActiveSync

Individual active sync operation.

**Fields**:
- `sourceName` (String!): Source being synced
- `newItemsCount` (Int!): Items ingested in this sync
- `status` (String!): Sync status ("syncing", "complete", "error")

## Queries

### searchSubreddits

Search Reddit for subreddits.

**Arguments**:
- `query` (String!): Search query

**Returns**: `[Subreddit!]!`

**Example**:
```graphql
query SearchSubreddits($query: String!) {
  searchSubreddits(query: $query) {
    name
    displayName
    subscriberCount
    description
    iconUrl
    isSubscribed
  }
}
```

### getFeedGroups

Get all feed groups for the current user.

**Returns**: `[FeedGroup!]!`

### getSourcesByGroup

Get sources in a specific group.

**Arguments**:
- `groupId` (ID!): Feed group ID

**Returns**: `[Source!]!`

### getRejectedItems

Get items rejected by ingestion rules.

**Arguments**:
- `sourceId` (ID): Filter by source (optional)
- `limit` (Int): Max items to return (default: 50)

**Returns**: `[RejectedItem!]!`

### getPipelineStatus

Get current pipeline sync status.

**Returns**: `PipelineStatus!`

## Mutations

### subscribeToSource

Subscribe to a new subreddit source.

**Arguments**:
- `subredditName` (String!): Subreddit name (without "r/")
- `groupId` (ID): Optional group ID (defaults to "Unsorted")

**Returns**: `Source!`

**Example**:
```graphql
mutation SubscribeToSource($subredditName: String!, $groupId: ID) {
  subscribeToSource(subredditName: $subredditName, groupId: $groupId) {
    id
    name
    subredditName
  }
}
```

### moveSourceToGroup

Move a source to a different group.

**Arguments**:
- `sourceId` (ID!): Source ID
- `groupId` (ID!): Target group ID

**Returns**: `Source!`

### toggleSourcePause

Pause or resume ingestion for a source.

**Arguments**:
- `sourceId` (ID!): Source ID

**Returns**: `Source!`

### updateIngestRule

Update ingestion rule for a source.

**Arguments**:
- `sourceId` (ID!): Source ID
- `rule` (IngestRuleInput!): Rule configuration

**Returns**: `IngestRule!`

**Example**:
```graphql
mutation UpdateIngestRule($sourceId: ID!, $rule: IngestRuleInput!) {
  updateIngestRule(sourceId: $sourceId, rule: $rule) {
    id
    minScore
    mediaOnly
    minResolution
  }
}
```

### forceImportItem

Force import a rejected item (override rule).

**Arguments**:
- `itemId` (ID!): Rejected item ID

**Returns**: `Post!`

### createFeedGroup

Create a new feed group.

**Arguments**:
- `name` (String!): Group name

**Returns**: `FeedGroup!`

### deleteFeedGroup

Delete a feed group (sources move to "Unsorted").

**Arguments**:
- `groupId` (ID!): Group ID

**Returns**: `Boolean!`

## Inputs

### IngestRuleInput

Configuration for ingestion rules.

**Fields**:
- `minScore` (Int): Minimum upvote score
- `mediaOnly` (Boolean): Only ingest media posts
- `minResolution` (String): Minimum resolution ("720p", "1080p")

## Subscriptions

### pipelineStatus

Real-time updates on pipeline sync status.

**Returns**: `PipelineStatus!`

**Example**:
```graphql
subscription PipelineStatus {
  pipelineStatus {
    activeSyncs {
      sourceName
      newItemsCount
      status
    }
  }
}
```






