# OmniPane Data Schema Expectations

This document defines the Neo4j schema requirements for integrating OmniPane Reader with Bunny's backend.

## Overview

OmniPane's data model centers around Articles, Boards, Sources, Tags, and User-specific state. This needs to be mapped to Neo4j graph structure while maintaining compatibility with Bunny's existing schema.

## Core Node Types

### User Node

**Purpose**: Represent users of the system (multi-user support required)

**Properties**:
- `id: String` (unique identifier, UUID)
- `username: String` (unique)
- `email: String` (optional, for authentication)
- `createdAt: DateTime`
- `preferences: Map` (optional, JSON blob for user preferences like layout mode)

**Constraints**:
- Unique constraint on `User.id`
- Unique constraint on `User.username`

**Indexes**:
- Index on `User.username` (for login/lookup)

**Example**:
```cypher
CREATE (u:User {
  id: "user-123",
  username: "johndoe",
  email: "john@example.com",
  createdAt: datetime()
})
```

### Article Node (extends Media/Post)

**Purpose**: Represent content items from various sources

**Properties**:
- `id: String` (unique identifier)
- `title: String`
- `author: String`
- `content: String` (HTML or text content)
- `summary: String` (optional, AI-generated)
- `keyTakeaways: List<String>` (optional, AI-generated)
- `publishedAt: DateTime`
- `url: String` (original source URL)
- `imageUrl: String` (optional, main image URL)
- `imageWidth: Int` (optional)
- `imageHeight: Int` (optional)
- `sourceType: String` (RSS, TWITTER, NEWSLETTER, YOUTUBE, REDDIT, BOORU, MONITOR)
- `createdAt: DateTime` (when ingested into system)

**Note**: This extends Bunny's existing `Media` or `Post` node. We may need to unify these or create Article as an alias.

**Constraints**:
- Unique constraint on `Article.id`

**Indexes**:
- Index on `Article.publishedAt` (for sorting)
- Index on `Article.sourceType` (for filtering)
- Index on `Article.createdAt` (for cursor pagination)

**Example**:
```cypher
CREATE (a:Article:Media {
  id: "article-456",
  title: "The Future of AI",
  author: "John Doe",
  content: "<p>Article content...</p>",
  publishedAt: datetime("2024-01-15T10:00:00Z"),
  url: "https://example.com/article",
  sourceType: "RSS",
  createdAt: datetime()
})
```

### Source Node (extends Handle/Subreddit)

**Purpose**: Represent feed sources (RSS feeds, Twitter accounts, etc.)

**Properties**:
- `id: String` (unique identifier)
- `name: String` (display name)
- `type: String` (RSS, TWITTER, NEWSLETTER, YOUTUBE, REDDIT, BOORU, MONITOR)
- `icon: String` (optional, icon URL)
- `url: String` (source URL)
- `createdAt: DateTime`

**Note**: This may map to existing `Handle` or `Subreddit` nodes, or be a new node type.

**Constraints**:
- Unique constraint on `Source.id`

**Indexes**:
- Index on `Source.type` (for filtering)

**Example**:
```cypher
CREATE (s:Source:Handle {
  id: "source-789",
  name: "TechCrunch",
  type: "RSS",
  url: "https://techcrunch.com/feed",
  createdAt: datetime()
})
```

### Board Node

**Purpose**: User-created collections of articles (Pinterest-style boards)

**Properties**:
- `id: String` (unique identifier, UUID)
- `name: String`
- `createdAt: DateTime`
- `updatedAt: DateTime`

**Constraints**:
- Unique constraint on `Board.id`

**Indexes**:
- Index on `Board.createdAt` (for sorting)

**Example**:
```cypher
CREATE (b:Board {
  id: "board-abc",
  name: "UI Inspiration",
  createdAt: datetime(),
  updatedAt: datetime()
})
```

### Tag Node

**Purpose**: Represent tags for organizing and filtering articles

**Properties**:
- `name: String` (unique tag name, e.g., "rem_(re:zero)", "width:1080")
- `createdAt: DateTime` (when first used)

**Constraints**:
- Unique constraint on `Tag.name`

**Indexes**:
- Index on `Tag.name` (for lookup and autocomplete)

**Example**:
```cypher
CREATE (t:Tag {
  name: "rem_(re:zero)",
  createdAt: datetime()
})
```

### SauceResult Node (Optional)

**Purpose**: Store SauceNAO reverse image search results

**Properties**:
- `id: String` (unique identifier)
- `similarity: Float` (0-100)
- `sourceUrl: String`
- `artistName: String`
- `extUrl: String` (optional, external URL like Danbooru)
- `searchedAt: DateTime`

**Alternative**: Store as properties on Article node (simpler, less normalized)

**Recommendation**: Store as properties on Article node unless we need to track multiple sauce results per image.

## Relationships

### User-Specific State Relationships

#### READ Relationship
`(:User)-[:READ]->(:Article)`

**Purpose**: Track which articles a user has read

**Properties**: None

**Example**:
```cypher
MATCH (u:User {id: "user-123"}), (a:Article {id: "article-456"})
CREATE (u)-[:READ {readAt: datetime()}]->(a)
```

#### SAVED Relationship
`(:User)-[:SAVED]->(:Article)`

**Purpose**: Track which articles a user has saved for later

**Properties**:
- `savedAt: DateTime`

**Example**:
```cypher
MATCH (u:User {id: "user-123"}), (a:Article {id: "article-456"})
CREATE (u)-[:SAVED {savedAt: datetime()}]->(a)
```

#### ARCHIVED Relationship
`(:User)-[:ARCHIVED]->(:Article)`

**Purpose**: Track which articles a user has archived

**Properties**:
- `archivedAt: DateTime`

**Example**:
```cypher
MATCH (u:User {id: "user-123"}), (a:Article {id: "article-456"})
CREATE (u)-[:ARCHIVED {archivedAt: datetime()}]->(a)
```

### Board Relationships

#### OWNS Relationship
`(:User)-[:OWNS]->(:Board)`

**Purpose**: Link boards to their owners

**Properties**: None

**Example**:
```cypher
MATCH (u:User {id: "user-123"}), (b:Board {id: "board-abc"})
CREATE (u)-[:OWNS]->(b)
```

#### CONTAINS Relationship
`(:Board)-[:CONTAINS]->(:Article)`

**Purpose**: Link articles to boards (many-to-many)

**Properties**:
- `pinnedAt: DateTime`

**Example**:
```cypher
MATCH (b:Board {id: "board-abc"}), (a:Article {id: "article-456"})
CREATE (b)-[:CONTAINS {pinnedAt: datetime()}]->(a)
```

### Source Relationships

#### BELONGS_TO Relationship
`(:Article)-[:BELONGS_TO]->(:Source)`

**Purpose**: Link articles to their source

**Properties**: None

**Example**:
```cypher
MATCH (a:Article {id: "article-456"}), (s:Source {id: "source-789"})
CREATE (a)-[:BELONGS_TO]->(s)
```

**Note**: This may overlap with existing relationships like `POSTED_IN` for Reddit posts.

### Tag Relationships

#### TAGGED_WITH Relationship
`(:Article)-[:TAGGED_WITH]->(:Tag)`

**Purpose**: Link articles to tags (many-to-many)

**Properties**: None

**Example**:
```cypher
MATCH (a:Article {id: "article-456"}), (t:Tag {name: "rem_(re:zero)"})
CREATE (a)-[:TAGGED_WITH]->(t)
```

## Query Patterns

### Get Unread Articles (Inbox)

```cypher
MATCH (u:User {id: $userId})
MATCH (a:Article)
WHERE NOT (u)-[:READ]->(a) AND NOT (u)-[:ARCHIVED]->(a)
OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:Source)
RETURN a, s
ORDER BY a.publishedAt DESC
SKIP $skip
LIMIT $limit
```

### Get Saved Articles (Read Later)

```cypher
MATCH (u:User {id: $userId})-[:SAVED]->(a:Article)
WHERE NOT (u)-[:ARCHIVED]->(a)
OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:Source)
RETURN a, s
ORDER BY a.publishedAt DESC
SKIP $skip
LIMIT $limit
```

### Get Articles by Tag

```cypher
MATCH (t:Tag {name: $tagName})<-[:TAGGED_WITH]-(a:Article)
MATCH (u:User {id: $userId})
WHERE NOT (u)-[:ARCHIVED]->(a)
OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:Source)
RETURN a, s
ORDER BY a.publishedAt DESC
SKIP $skip
LIMIT $limit
```

### Get Articles in Board

```cypher
MATCH (u:User {id: $userId})-[:OWNS]->(b:Board {id: $boardId})-[:CONTAINS]->(a:Article)
OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:Source)
RETURN a, s
ORDER BY a.publishedAt DESC
SKIP $skip
LIMIT $limit
```

### Get User's Boards

```cypher
MATCH (u:User {id: $userId})-[:OWNS]->(b:Board)
OPTIONAL MATCH (b)-[:CONTAINS]->(a:Article)
WITH b, count(a) as articleCount
RETURN b, articleCount
ORDER BY b.updatedAt DESC
```

### Get Tags with Counts

```cypher
MATCH (u:User {id: $userId})
MATCH (t:Tag)<-[:TAGGED_WITH]-(a:Article)
WHERE NOT (u)-[:ARCHIVED]->(a)
WITH t, count(DISTINCT a) as count
RETURN t.name as name, count
ORDER BY count DESC
LIMIT $limit
```

### Get Source Unread Counts

```cypher
MATCH (u:User {id: $userId})
MATCH (s:Source)
OPTIONAL MATCH (s)<-[:BELONGS_TO]-(a:Article)
WHERE NOT (u)-[:READ]->(a) AND NOT (u)-[:ARCHIVED]->(a)
WITH s, count(DISTINCT a) as unreadCount
RETURN s, unreadCount
ORDER BY s.name
```

### Mark Article as Read

```cypher
MATCH (u:User {id: $userId}), (a:Article {id: $articleId})
MERGE (u)-[r:READ]->(a)
ON CREATE SET r.readAt = datetime()
RETURN a
```

### Toggle Article Saved State

```cypher
MATCH (u:User {id: $userId}), (a:Article {id: $articleId})
OPTIONAL MATCH (u)-[r:SAVED]->(a)
WITH u, a, r
CALL apoc.do.when(
  r IS NULL,
  'CREATE (u)-[:SAVED {savedAt: datetime()}]->(a) RETURN a',
  'DELETE r RETURN a',
  {u: u, a: a, r: r}
) YIELD value
RETURN value.a as a
```

### Pin Article to Board

```cypher
MATCH (u:User {id: $userId})-[:OWNS]->(b:Board {id: $boardId}), (a:Article {id: $articleId})
MERGE (b)-[r:CONTAINS]->(a)
ON CREATE SET r.pinnedAt = datetime()
SET b.updatedAt = datetime()
RETURN b
```

### Get Article with User State

```cypher
MATCH (a:Article {id: $articleId})
OPTIONAL MATCH (u:User {id: $userId})
OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:Source)
OPTIONAL MATCH (a)-[:TAGGED_WITH]->(t:Tag)
OPTIONAL MATCH (u)-[:READ]->(a)
OPTIONAL MATCH (u)-[:SAVED]->(a)
OPTIONAL MATCH (u)-[:ARCHIVED]->(a)
RETURN a, s, collect(DISTINCT t.name) as tags,
  (u)-[:READ]->(a) IS NOT NULL as read,
  (u)-[:SAVED]->(a) IS NOT NULL as saved,
  (u)-[:ARCHIVED]->(a) IS NOT NULL as archived
```

## Integration with Existing Schema

### Media/Post Nodes

OmniPane's `Article` should map to Bunny's existing `Media` or `Post` nodes. Options:

1. **Use Media Node**: Extend `Media` node with Article properties
2. **Unified Content Node**: Create a base `Content` node that both `Media` and `Article` extend
3. **Separate Article Node**: Create new `Article` node, link to `Media` where applicable

**Recommendation**: Extend existing `Media` node to support article content. Add properties:
- `content: String` (HTML/text content)
- `summary: String` (AI summary)
- `keyTakeaways: List<String>` (AI takeaways)

### Handle/Subreddit Nodes

OmniPane's `Source` maps to existing `Handle` or `Subreddit` nodes. Options:

1. **Use Handle Node**: Extend `Handle` to support all source types
2. **Unified Source Node**: Create base `Source` node
3. **Separate Source Node**: Create new node, link to `Handle` where applicable

**Recommendation**: Use existing `Handle` node, extend `Platform` enum to include new types (RSS, NEWSLETTER, BOORU, MONITOR).

## Migration Strategy

### Phase 1: Add New Node Types
1. Create `User` nodes
2. Create `Board` nodes
3. Create `Tag` nodes
4. Extend `Media` nodes with article properties
5. Extend `Platform` enum

### Phase 2: Add Relationships
1. Add user-state relationships (READ, SAVED, ARCHIVED)
2. Add board relationships (OWNS, CONTAINS)
3. Add tag relationships (TAGGED_WITH)
4. Ensure source relationships (BELONGS_TO) exist

### Phase 3: Data Migration
1. Create default user for existing data
2. Migrate any existing article/bookmark data
3. Create initial tags from existing content
4. Set up indexes and constraints

## Indexes Summary

**Node Indexes**:
- `User.id` (unique)
- `User.username` (unique)
- `Article.id` (unique)
- `Article.publishedAt`
- `Article.sourceType`
- `Article.createdAt`
- `Board.id` (unique)
- `Board.createdAt`
- `Tag.name` (unique)
- `Source.id` (unique)
- `Source.type`

**Relationship Indexes** (if supported):
- Index on `(:User)-[:READ]->(:Article)` for read queries
- Index on `(:User)-[:SAVED]->(:Article)` for saved queries
- Index on `(:Board)-[:CONTAINS]->(:Article)` for board queries

## Performance Considerations

1. **User-State Queries**: Use relationship existence checks (WHERE NOT (u)-[:READ]->(a)) - ensure indexes exist
2. **Tag Aggregations**: Pre-compute tag counts or use efficient aggregation queries
3. **Board Article Counts**: Use `OPTIONAL MATCH` with `count()` for efficiency
4. **Pagination**: Use `SKIP` and `LIMIT` with indexed `ORDER BY` fields
5. **Cursor Pagination**: Use `publishedAt` or `createdAt` for cursor-based pagination

## Schema Validation

Ensure:
- All required properties are present
- Unique constraints are enforced
- Indexes are created for query patterns
- Relationships are properly typed
- Multi-user isolation is maintained (user-scoped queries)

