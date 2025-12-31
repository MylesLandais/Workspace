# Creator-Handle Model

## Status

Accepted

## Context

Content creators exist across multiple platforms with different usernames/handles. We need to model the relationship between a person (Creator) and their various platform accounts (Handles) while maintaining clean identity resolution.

## Decision

Use a **Creator-Handle** model instead of Entity-Source:
- `Creator` node represents the person/brand (canonical identity)
- `Handle` node represents a specific account on a platform
- `1:Many` relationship: One Creator has many Handles

## Rationale

**Semantic Clarity**: "Creator" is more specific than "Entity" and clearly indicates a person/brand that creates content.

**Identity Resolution**: Creator node holds canonical identity (real name, bio, avatar) separate from platform-specific handles.

**Scalability**: Handles can be added/removed without affecting the Creator node. Supports platform-specific metadata.

**Query Clarity**: `creator(slug: "sjokz")` is more intuitive than `entity(id: "sjokz")`.

## Implementation

### Neo4j Schema

```cypher
// Creator node (canonical identity)
CREATE (c:Creator {
  id: "sjokz",
  slug: "sjokz",
  name: "Eefje Depoortere",
  displayName: "Sjokz",
  bio: "Esports host and personality",
  avatarUrl: "https://...",
  verified: true
})

// Handle node (platform account)
CREATE (h1:Handle {
  id: "handle-1",
  platform: "reddit",
  username: "Sjokz",
  handle: "Sjokz",
  url: "https://reddit.com/r/Sjokz",
  verified: true
})

CREATE (h2:Handle {
  id: "handle-2",
  platform: "youtube",
  username: "sjokz",
  handle: "@sjokz",
  channelId: "UC...",
  url: "https://youtube.com/@sjokz",
  verified: true
})

// Relationships
CREATE (c)-[:OWNS_HANDLE {status: "active", verified: true}]->(h1)
CREATE (c)-[:OWNS_HANDLE {status: "active", verified: true}]->(h2)
CREATE (h1)-[:ON_PLATFORM]->(p1:Platform {name: "Reddit"})
CREATE (h2)-[:ON_PLATFORM]->(p2:Platform {name: "YouTube"})
```

### GraphQL Schema

```graphql
type Creator {
  id: ID!
  slug: String!
  name: String!
  displayName: String!
  bio: String
  avatarUrl: String
  verified: Boolean!
  handles: [Handle!]!
}

type Handle {
  id: ID!
  platform: Platform!
  username: String!
  handle: String!  # Platform-specific handle (@sjokz, r/Sjokz)
  url: String!
  verified: Boolean!
  status: HandleStatus!
  creator: Creator!
}

enum Platform {
  REDDIT
  YOUTUBE
  TWITTER
  INSTAGRAM
  TIKTOK
}

enum HandleStatus {
  ACTIVE
  SUSPENDED
  ABANDONED
}

type Query {
  creator(slug: String!): Creator
  creators(query: String, limit: Int): [Creator!]!
}
```

## Consequences

**Positive**:
- Clear separation of identity (Creator) and accounts (Handles)
- Supports canonical identity resolution
- Enables aggregated queries across all handles
- Better semantic model for content creators

**Negative**:
- Migration needed from Entity-Source model
- More complex queries (need to traverse Creator -> Handle -> Media)
- Requires slug uniqueness enforcement

**Neutral**:
- Backward compatible via migration layer
- Can support both models during transition

## Alternatives Considered

**Entity-Source Model**: Current model. Rejected because "Entity" is too generic and doesn't convey the creator relationship clearly.

**Flat Structure**: Just use Handles without Creator grouping. Rejected because it doesn't solve identity resolution or enable aggregated feeds.

## Implementation Notes

- Slug must be unique and system-generated with collision handling
- Creator name (real name) can differ from Handle usernames
- Verification status tracked on both Creator and Handle levels
- Handle status (active/suspended/abandoned) on relationship edge

## References

- Identity resolution patterns
- Multi-platform content aggregation






