# Subscriptions Data Model

Neo4j graph structure for feed groups, sources, and ingestion rules.

## Node Types

### Entity

Represents a person, brand, or topic that may have sources across multiple platforms.

**Properties**:
- `id` (string): Unique identifier (slug, e.g., "sjokz", "brooke-monk")
- `name` (string): Display name
- `type` (string): Entity type ("person", "brand", "topic")
- `description` (string): Optional description

**Relationships**:
- `(:Entity)-[:HAS_SOURCE]->(:Source)`: Links entity to its sources

**Example**:
```cypher
CREATE (e:Entity {
  id: "sjokz",
  name: "Sjokz",
  type: "person",
  description: "Esports host and personality"
})
```

### FeedGroup

Organizational container for sources (e.g., "Design", "Memes", "Dev").

**Properties**:
- `id` (string): Unique identifier (UUID)
- `name` (string): Group name
- `created_at` (datetime): When group was created

**Indexes**:
- `FeedGroup.id` (unique constraint)

### Source

A content source being ingested (Reddit, YouTube, etc.).

**Properties**:
- `id` (string): Unique identifier (UUID)
- `name` (string): Display name
- `source_type` (string): Platform type ("reddit", "youtube", "twitter", etc.)
- `subreddit_name` (string): Reddit subreddit name (if source_type == "reddit")
- `youtube_channel_id` (string): YouTube channel ID (if source_type == "youtube")
- `youtube_channel_handle` (string): YouTube handle (e.g., "@sjokz")
- `icon_url` (string): Source icon URL (optional)
- `is_paused` (boolean): Whether ingestion is paused
- `last_synced` (datetime): Last successful sync timestamp
- `media_count` (integer): Total number of items ingested

**Indexes**:
- `Source.id` (unique constraint)
- `Source.subreddit_name` (for Reddit lookups)
- `Source.youtube_channel_id` (for YouTube lookups)

**Note**: Platform-specific fields are only populated based on `source_type`.

### IngestRule

Configuration that filters what content gets ingested from a source.

**Properties**:
- `id` (string): Unique identifier (UUID)
- `min_score` (integer): Minimum upvote score required (default: 0)
- `media_only` (boolean): Only ingest posts with images/videos (default: true)
- `min_resolution` (string): Minimum resolution filter (e.g., "720p", "1080p")

**Indexes**:
- `IngestRule.id` (unique constraint)

### RejectedItem

Item that was rejected by ingestion rules (for quality control review).

**Properties**:
- `id` (string): Unique identifier (UUID)
- `url` (string): Original post URL
- `thumbnail_url` (string): Thumbnail image URL
- `reason` (string): Rejection reason (e.g., "Score too low", "Resolution too low")
- `rejected_at` (datetime): When item was rejected

## Relationships

### HAS_SOURCE

`(Entity)-[:HAS_SOURCE]->(Source)`

Links an entity to its sources across platforms. A source can belong to one entity.

**Example**: Sjokz entity has both r/Sjokz (Reddit) and @sjokz (YouTube) sources.

### MANAGES

`(User)-[:MANAGES]->(FeedGroup)`

User who owns/manages a feed group. Used for access control.

### CONTAINS

`(FeedGroup)-[:CONTAINS]->(Source)`

Sources belong to feed groups. A source can be moved between groups.

### USING_RULE

`(Source)-[:USING_RULE]->(IngestRule)`

Each source has one ingestion rule that controls filtering.

### POSTED_IN (inherited from Feed domain)

`(Post)-[:POSTED_IN]->(Subreddit)`

Posts are linked to subreddits. Sources reference the same Subreddit nodes.

## Design Decisions

### Separate IngestRule Nodes

Rules are stored as separate nodes rather than properties on Source.

**Why**:
- Rules can be shared/reused across sources
- Easier to query "all sources using this rule"
- Supports rule versioning/history in the future

### FeedGroup Organization

Sources are organized into groups for better management.

**Why**:
- Users can organize sources by topic/interest
- Enables bulk operations (pause all in group)
- Better UX for managing many sources

## Example Cypher Queries

### Get Sources in a Group

```cypher
MATCH (fg:FeedGroup {id: $groupId})-[:CONTAINS]->(s:Source)
OPTIONAL MATCH (s)-[:USING_RULE]->(r:IngestRule)
RETURN s, r, fg.name AS groupName
ORDER BY s.name
```

### Move Source to Group

```cypher
MATCH (s:Source {id: $sourceId})
MATCH (fg:FeedGroup {id: $groupId})
OPTIONAL MATCH (s)-[old:CONTAINS]-()
DELETE old
CREATE (fg)-[:CONTAINS]->(s)
RETURN s
```

### Get Sources with Health Status

```cypher
MATCH (s:Source)
OPTIONAL MATCH (s)-[:USING_RULE]->(r:IngestRule)
WITH s, r, 
  CASE 
    WHEN s.last_synced IS NULL THEN 'red'
    WHEN duration.between(s.last_synced, datetime()) < duration({hours: 1}) THEN 'green'
    WHEN duration.between(s.last_synced, datetime()) < duration({hours: 24}) THEN 'yellow'
    ELSE 'red'
  END AS health
RETURN s, r, health
ORDER BY s.name
```

### Create Source with Rule

```cypher
MATCH (sub:Subreddit {name: $subredditName})
MATCH (fg:FeedGroup {id: $groupId})

CREATE (r:IngestRule {
  id: randomUUID(),
  min_score: $minScore,
  media_only: $mediaOnly,
  min_resolution: $minResolution
})

CREATE (s:Source {
  id: randomUUID(),
  name: $subredditName,
  source_type: "reddit",
  subreddit_name: $subredditName,
  is_paused: false,
  media_count: 0
})

CREATE (fg)-[:CONTAINS]->(s)
CREATE (s)-[:USING_RULE]->(r)

RETURN s, r
```

### Create Entity with Multiple Sources

```cypher
// Create entity
CREATE (e:Entity {
  id: "sjokz",
  name: "Sjokz",
  type: "person",
  description: "Esports host and personality"
})

// Create Reddit source
CREATE (s1:Source {
  id: randomUUID(),
  name: "Sjokz",
  source_type: "reddit",
  subreddit_name: "Sjokz",
  is_paused: false,
  media_count: 0
})

// Create YouTube source
CREATE (s2:Source {
  id: randomUUID(),
  name: "Sjokz YouTube",
  source_type: "youtube",
  youtube_channel_handle: "@sjokz",
  is_paused: false,
  media_count: 0
})

// Link sources to entity
CREATE (e)-[:HAS_SOURCE]->(s1)
CREATE (e)-[:HAS_SOURCE]->(s2)

RETURN e, s1, s2
```

### Get All Sources for an Entity

```cypher
MATCH (e:Entity {id: $entityId})-[:HAS_SOURCE]->(s:Source)
OPTIONAL MATCH (s)-[:USING_RULE]->(r:IngestRule)
RETURN e, collect(s) AS sources, collect(r) AS rules
```

