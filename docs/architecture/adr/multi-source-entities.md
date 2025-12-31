# Multi-Source Entity Organization

## Status

Accepted

## Context

Content creators and personalities exist across multiple platforms. For example:
- Sjokz has both a Reddit subreddit (r/Sjokz) and a YouTube channel (@sjokz)
- Brooke Monk has subreddits (r/BrookeMonkTheSecond, r/BestOfBrookeMonk) and a YouTube channel (BrookeMonk)

Users want to organize and view content from the same creator across all platforms in a unified way.

## Decision

Introduce a **Creator** node type that groups related handles (platform-specific accounts) across different platforms. Handles link to creators via `OWNS_HANDLE` relationships, enabling unified organization and filtering.

## Rationale

**Unified Organization**: Users can group all Sjokz content (Reddit + YouTube) together without manually creating separate groups.

**Cross-Platform Discovery**: When searching for "Sjokz", show both the subreddit and YouTube channel as related handles.

**Feed Aggregation**: Omni-feed feature shows all content from a creator (across platforms) in a single feed view.

**Verification System**: Handles can be verified with confidence levels (High, Medium, Manual), ensuring only verified handles are used for ingestion.

**Scalability**: Supports adding more platforms (Twitter, Instagram, TikTok) without restructuring. New platforms are added as Platform nodes.

## Implementation

### Neo4j Schema

```cypher
// Creator represents a person, brand, or topic
CREATE (c:Creator {
  uuid: "uuid-here",
  name: "Sjokz",
  slug: "sjokz",
  bio: "Esports host and personality",
  created_at: datetime()
})

// Handles represent platform-specific accounts
CREATE (h1:Handle {
  uuid: "handle-uuid-1",
  username: "Sjokz",
  profile_url: "https://www.reddit.com/r/Sjokz",
  verified_by_platform: false
})

CREATE (h2:Handle {
  uuid: "handle-uuid-2",
  username: "@sjokz",
  profile_url: "https://youtube.com/@sjokz",
  verified_by_platform: true
})

// Platforms represent social media platforms
CREATE (p1:Platform {
  name: "Reddit",
  slug: "reddit"
})

CREATE (p2:Platform {
  name: "YouTube",
  slug: "youtube"
})

// Relationships
CREATE (c)-[:OWNS_HANDLE {
  status: "Active",
  verified: true,
  confidence: "High",
  discovered_at: datetime()
}]->(h1)

CREATE (c)-[:OWNS_HANDLE {
  status: "Active",
  verified: true,
  confidence: "High",
  discovered_at: datetime()
}]->(h2)

CREATE (h1)-[:ON_PLATFORM]->(p1)
CREATE (h2)-[:ON_PLATFORM]->(p2)
```

### GraphQL Schema

```graphql
type Creator {
  uuid: ID!
  name: String!
  slug: String!
  bio: String
  avatarUrl: String
  handles: [Handle!]!
}

type Handle {
  uuid: ID!
  username: String!
  displayName: String
  profileUrl: String!
  platform: Platform!
  status: HandleStatus!
  verified: Boolean!
  confidence: VerificationConfidence
}

type Platform {
  name: String!
  slug: String!
}

enum HandleStatus {
  ACTIVE
  SUSPENDED
  ABANDONED
  UNVERIFIED
}

enum VerificationConfidence {
  HIGH
  MEDIUM
  MANUAL
}
```

## Consequences

**Positive**:
- Natural organization for multi-platform creators
- Enables omni-feed views (all content from creator across platforms)
- Scales to new platforms easily (add Platform nodes)
- Better search/discovery (find all handles for a creator)
- Verification system ensures data quality
- Handle status tracking (Active, Suspended, Abandoned)

**Negative**:
- More complex data model (Creator, Handle, Platform, relationships)
- Need handle discovery and verification logic
- UI needs to show creator/handle relationships
- Verification requires manual review or heuristics

**Neutral**:
- Backward compatible (existing sources can exist without entities)
- Optional relationship (sources don't require entities)

## Alternatives Considered

**Entity/Source Model**: Original design used Entity and Source nodes. Rejected in favor of Creator/Handle/Platform for clearer semantics and better alignment with social media terminology.

**Flat Grouping**: Just use FeedGroups to manually group sources. Rejected because it doesn't capture the semantic relationship and doesn't scale well.

**Tags Only**: Use tags to link related sources. Rejected because tags are too loose and don't represent the "same entity" relationship clearly.

## Implementation Notes

### Handle Discovery

Handles are discovered through bio crawling - scanning creator profiles for links to other platforms:

```python
from src.feed.services.bio_crawler import BioCrawler

crawler = BioCrawler()
candidates = crawler.discover_handles(anchor_url="https://youtube.com/@sjokz")
# Returns CandidateHandle objects with confidence levels
```

### Verification Process

1. **Heuristic**: Link in official bio (High confidence → auto-verify)
2. **Inference**: Exact username match across platforms (Medium confidence → requires review)
3. **Manual**: User clicks "Confirm" (100% confidence)

### Unified Feed Query

```cypher
// Get all content from a creator across all verified handles
MATCH (c:Creator {uuid: $creator_uuid})
  -[:OWNS_HANDLE {verified: true, status: 'Active'}]
  ->(h:Handle)
MATCH (h)-[:PUBLISHED]->(m:Media)
WHERE m.publish_date IS NOT NULL
RETURN m
ORDER BY m.publish_date DESC
LIMIT $limit
```

### Key Implementation Files

- `src/feed/models/creator.py` - Creator model
- `src/feed/models/handle.py` - Handle model
- `src/feed/services/creator_service.py` - Creator management
- `src/feed/services/bio_crawler.py` - Handle discovery
- `src/feed/services/verification.py` - Handle verification
- `src/feed/storage/migrations/002_creator_handle_media_schema.cypher` - Schema migration

## References

- [ADR: Ontology Management](./ontology-management.md)
- [ADR: Neo4j Graph Database](./neo4j-graph-database.md)
- Implementation: `src/feed/ONTOLOGY_IMPLEMENTATION.md`
- Implementation: `src/feed/storage/migrations/002_creator_handle_media_schema.cypher`




