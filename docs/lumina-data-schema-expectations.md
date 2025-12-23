# Lumina Data Schema Expectations

This document defines the data schema requirements needed to support Lumina Feed features in the Bunny architecture, including Neo4j node/relationship structures and GraphQL schema extensions.

## Overview

Lumina Feed uses a simplified data model stored in LocalStorage. To integrate with Bunny, we need to map these concepts to Neo4j graph structures while preserving functionality and enhancing capabilities.

## Core Entity Mappings

### IdentityProfile → Creator + Handle

**Lumina Model**:
```typescript
interface IdentityProfile {
  id: string;
  name: string;
  bio: string;
  avatarUrl: string;
  aliases: string[];
  sources: SourceLink[];
  contextKeywords: string[];
  imagePool: string[];
  relationships: Relationship[];
}
```

**Bunny Neo4j Mapping**:

#### Creator Node
```cypher
(:Creator {
  id: ID!,
  slug: String!,
  name: String!,
  displayName: String!,
  bio: String,
  avatarUrl: String,
  aliases: [String!]!,  // NEW
  contextKeywords: [String!]!,  // NEW
  imagePool: [String!]!,  // NEW (optional)
  verified: Boolean!,
  createdAt: DateTime!,
  updatedAt: DateTime!
})
```

**Indexes**:
- `CREATE CONSTRAINT creator_id FOR (c:Creator) REQUIRE c.id IS UNIQUE`
- `CREATE INDEX creator_slug FOR (c:Creator) ON (c.slug)`
- `CREATE INDEX creator_name FOR (c:Creator) ON (c.name)`

#### Handle Node (Existing, Enhanced)
```cypher
(:Handle {
  id: ID!,
  platform: Platform!,
  username: String!,
  handle: String!,
  url: String!,
  verified: Boolean!,
  status: HandleStatus!,
  label: String,  // NEW: e.g., "Main", "Spam", "Fan Page"
  hidden: Boolean!,  // NEW: visibility toggle
  createdAt: DateTime!,
  lastSynced: DateTime
})
```

**Indexes**:
- `CREATE CONSTRAINT handle_id FOR (h:Handle) REQUIRE h.id IS UNIQUE`
- `CREATE INDEX handle_platform_username FOR (h:Handle) ON (h.platform, h.username)`

#### Relationship: Creator → Handle
```cypher
(:Creator)-[:HAS_HANDLE]->(:Handle)
```

**Properties** (optional on relationship):
- None needed initially, but could add `addedAt`, `priority`, etc.

---

### SourceLink → Handle

**Lumina Model**:
```typescript
interface SourceLink {
  platform: PlatformType;
  id: string;  // handle, subreddit name, or url
  label?: string;
  hidden?: boolean;
}
```

**Mapping**:
- `platform` → `Handle.platform`
- `id` → `Handle.username` or `Handle.handle`
- `label` → `Handle.label`
- `hidden` → `Handle.hidden`

**Note**: SourceLink is already represented by Handle nodes, so this is a direct mapping.

---

### Relationship → Graph Relationship

**Lumina Model**:
```typescript
interface Relationship {
  targetId: string;
  type: string;  // e.g., "Best Friend", "Dating", "Co-star"
}
```

**Bunny Neo4j Mapping**:

#### Relationship Type
```cypher
(:Creator)-[:RELATED_TO {
  type: String!,
  createdAt: DateTime!,
  updatedAt: DateTime!
}]->(:Creator)
```

**Example**:
```cypher
(c1:Creator {id: "taylor-swift"})-[:RELATED_TO {
  type: "Best Friend",
  createdAt: datetime(),
  updatedAt: datetime()
}]->(c2:Creator {id: "selena-gomez"})
```

**Indexes**:
- `CREATE INDEX related_to_type FOR ()-[r:RELATED_TO]-() ON (r.type)`

**Notes**:
- Bidirectional: May want to query both directions
- Type is free-form string (decision: team prefers type safety but relationship types are beyond domain expertise)
- Could normalize to enum in future if patterns emerge
- Could add inverse type property for clarity

---

### SavedBoard → SavedBoard Node

**Lumina Model**:
```typescript
interface SavedBoard {
  id: string;
  name: string;
  filters: FilterState;
  createdAt: number;
}

interface FilterState {
  persons: string[];
  sources: string[];
  searchQuery: string;
}
```

**Bunny Neo4j Mapping**:

#### SavedBoard Node
```cypher
(:SavedBoard {
  id: ID!,
  name: String!,
  persons: [String!]!,  // Array of creator slugs or IDs
  sources: [String!]!,  // Array of platform names or source identifiers
  searchQuery: String,
  createdAt: DateTime!,
  updatedAt: DateTime!,
  userId: String!  // REQUIRED: Multi-user support
})
```

**Indexes**:
- `CREATE CONSTRAINT saved_board_id FOR (b:SavedBoard) REQUIRE b.id IS UNIQUE`
- `CREATE INDEX saved_board_user FOR (b:SavedBoard) ON (b.userId)` // Required for multi-user queries

**Relationships** (optional, for query efficiency):
```cypher
(:SavedBoard)-[:FILTERS_BY]->(:Creator)  // For person filters
(:SavedBoard)-[:FILTERS_BY]->(:Handle)   // For source filters
```

**Alternative Approach** (store as properties):
- Keep filter arrays as node properties (simpler)
- Query boards by checking array membership
- Trade-off: Less graph-native, but simpler queries

**Recommendation**: Start with properties, add relationships if query performance becomes an issue.

---

### FeedItem → Media Node

**Lumina Model**:
```typescript
interface FeedItem {
  id: string;
  type: MediaType;
  caption: string;
  author: Author;
  source: string;
  timestamp: string;
  aspectRatio: string;
  width: number;
  height: number;
  likes: number;
  mediaUrl?: string;
}
```

**Bunny Neo4j Mapping**:

Media node already exists in Bunny schema. Key mappings:

- `id` → `Media.id`
- `type` → `Media.mediaType` (enum: IMAGE, VIDEO, TEXT)
- `caption` → `Media.title`
- `author` → `Media.author` (User node relationship)
- `source` → `Media.platform` + `Media.handle` relationship
- `timestamp` → `Media.publishDate`
- `width` → `Media.width`
- `height` → `Media.height`
- `likes` → `Media.score`
- `mediaUrl` → `Media.imageUrl` or `Media.sourceUrl`

**Relationships**:
- `(:Media)-[:POSTED_BY]->(:User)` for author
- `(:Media)-[:FROM_HANDLE]->(:Handle)` for source
- `(:Handle)-[:BELONGS_TO]->(:Creator)` for creator aggregation

**Derived Fields**:
- `aspectRatio`: Calculate from `width`/`height` (client-side or add computed property)

---

## GraphQL Schema Extensions

### Type Extensions

```graphql
# Extend existing Creator type
extend type Creator {
  aliases: [String!]!
  contextKeywords: [String!]!
  imagePool: [String!]!
  relationships: [Relationship!]!
}

# Extend existing Handle type
extend type Handle {
  label: String
  hidden: Boolean!
}

# New types
type Relationship {
  target: Creator!
  type: String!
  createdAt: DateTime!
}

type SavedBoard {
  id: ID!
  name: String!
  filters: FilterState!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type FilterState {
  persons: [String!]!
  sources: [String!]!
  searchQuery: String
}

input FilterInput {
  persons: [String!]!
  sources: [String!]!
  searchQuery: String
}

input UpdateCreatorInput {
  name: String
  displayName: String
  bio: String
  avatarUrl: String
  aliases: [String!]
  contextKeywords: [String!]
}

input AddRelationshipInput {
  targetId: ID!
  type: String!
}
```

### Query Extensions

```graphql
extend type Query {
  # Entity management
  creatorWithRelations(slug: String!): Creator
  
  # Board management
  savedBoards: [SavedBoard!]!
  savedBoard(id: ID!): SavedBoard
  
  # Enhanced feed query
  feed(
    cursor: String
    limit: Int
    persons: [String!]  # NEW: Filter by creator slugs
    sources: [String!]  # NEW: Filter by source/platform
    searchQuery: String  # NEW: Text search
  ): FeedConnection!
}
```

### Mutation Extensions

```graphql
extend type Mutation {
  # Creator management
  updateCreator(
    id: ID!
    input: UpdateCreatorInput!
  ): Creator!
  
  deleteCreator(id: ID!): Boolean!
  
  # Handle management
  updateHandleVisibility(
    handleId: ID!
    hidden: Boolean!
  ): Handle!
  
  updateHandleLabel(
    handleId: ID!
    label: String
  ): Handle!
  
  # Relationship management
  addRelationship(
    creatorId: ID!
    input: AddRelationshipInput!
  ): Creator!
  
  removeRelationship(
    creatorId: ID!
    targetId: ID!
  ): Creator!
  
  # Board management
  createSavedBoard(
    name: String!
    filters: FilterInput!
  ): SavedBoard!
  
  updateSavedBoard(
    id: ID!
    name: String
    filters: FilterInput
  ): SavedBoard!
  
  deleteSavedBoard(id: ID!): Boolean!
}
```

---

## Cypher Query Patterns

### Create Creator with Handles

```cypher
MERGE (c:Creator {
  id: $creatorId,
  slug: $slug,
  name: $name,
  displayName: $displayName
})
SET c.bio = $bio,
    c.avatarUrl = $avatarUrl,
    c.aliases = $aliases,
    c.contextKeywords = $contextKeywords,
    c.updatedAt = datetime()

WITH c
UNWIND $handles AS handleData
MERGE (h:Handle {
  platform: handleData.platform,
  username: handleData.username
})
SET h.handle = handleData.handle,
    h.url = handleData.url,
    h.label = handleData.label,
    h.hidden = handleData.hidden ?? false,
    h.verified = handleData.verified ?? false,
    h.status = handleData.status ?? 'ACTIVE'
MERGE (c)-[:HAS_HANDLE]->(h)

RETURN c, collect(h) AS handles
```

### Query Feed with Filters

```cypher
MATCH (m:Media)
WHERE m.mediaType IN ['IMAGE', 'VIDEO']

// Filter by persons (creators)
OPTIONAL MATCH (m)-[:FROM_HANDLE]->(h:Handle)-[:BELONGS_TO]->(c:Creator)
WHERE size($persons) = 0 OR c.slug IN $persons OR c.id IN $persons

// Filter by sources/platforms
OPTIONAL MATCH (m)-[:FROM_HANDLE]->(h2:Handle)
WHERE size($sources) = 0 OR h2.platform IN $sources OR h2.label IN $sources
  AND (h2.hidden IS NULL OR h2.hidden = false)

// Filter by search query
WHERE $searchQuery IS NULL OR $searchQuery = '' OR 
      m.title CONTAINS $searchQuery OR
      (m.author IS NOT NULL AND m.author CONTAINS $searchQuery)

WITH m, c, h2
WHERE (size($persons) = 0 OR c IS NOT NULL)
  AND (size($sources) = 0 OR h2 IS NOT NULL)

RETURN m
ORDER BY m.publishDate DESC
SKIP $skip
LIMIT $limit
```

### Get Creator with Relationships

```cypher
MATCH (c:Creator {slug: $slug})
OPTIONAL MATCH (c)-[:HAS_HANDLE]->(h:Handle)
OPTIONAL MATCH (c)-[r:RELATED_TO]->(target:Creator)
RETURN c,
       collect(DISTINCT h) AS handles,
       collect(DISTINCT {
         target: target,
         type: r.type,
         createdAt: r.createdAt
       }) AS relationships
```

### Create Saved Board

```cypher
CREATE (b:SavedBoard {
  id: $id,
  name: $name,
  persons: $persons,
  sources: $sources,
  searchQuery: $searchQuery,
  createdAt: datetime(),
  updatedAt: datetime()
})
RETURN b
```

---

## Migration Considerations

### Data Migration from LocalStorage

1. **Identity Profiles → Creators**:
   - Extract `IdentityProfile` objects from LocalStorage
   - Create `Creator` nodes with mapped properties
   - Create `Handle` nodes from `sources` array
   - Create `RELATED_TO` relationships from `relationships` array

2. **Saved Boards → SavedBoard Nodes**:
   - Extract `SavedBoard` objects from LocalStorage
   - Create `SavedBoard` nodes with filter properties
   - Associate with user (if multi-user support exists)

3. **Validation**:
   - Verify all creators have at least one handle
   - Verify all relationships reference valid creators
   - Verify all boards reference valid creator slugs

### Backward Compatibility

- Keep existing `Creator` and `Handle` structures
- Add new fields as optional initially
- Migrate gradually with default values

---

## Indexes and Performance

### Recommended Indexes

```cypher
// Creator lookups
CREATE INDEX creator_slug IF NOT EXISTS FOR (c:Creator) ON (c.slug)
CREATE INDEX creator_name IF NOT EXISTS FOR (c:Creator) ON (c.name)

// Handle filtering
CREATE INDEX handle_hidden IF NOT EXISTS FOR (h:Handle) ON (h.hidden)
CREATE INDEX handle_platform_label IF NOT EXISTS FOR (h:Handle) ON (h.platform, h.label)

// Relationship queries
CREATE INDEX related_to_type IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.type)

// Saved board queries
CREATE INDEX saved_board_user IF NOT EXISTS FOR (b:SavedBoard) ON (b.userId)
```

### Query Optimization

1. **Feed Queries with Filters**:
   - Use indexes on `Handle.hidden` and `Handle.platform`
   - Use indexes on `Media.publishDate` for sorting
   - Consider composite indexes for common filter combinations

2. **Creator Queries**:
   - Index on `slug` for lookups
   - Index on `name` for search
   - Use relationship traversal efficiently

3. **Board Queries**:
   - Index on `userId` if multi-user
   - Consider materialized views for frequently accessed boards

---

## Validation Rules

### Creator Validation
- `name` and `displayName` are required
- `slug` must be unique and URL-safe
- `aliases` and `contextKeywords` are arrays (can be empty)

### Handle Validation
- `platform` must be valid enum value
- `username` is required
- `hidden` defaults to `false`
- At least one non-hidden handle per creator (recommended)

### Relationship Validation
- `targetId` must reference existing Creator
- Cannot create self-referential relationship (unless allowed)
- `type` should be non-empty string

### SavedBoard Validation
- `name` is required and non-empty
- `persons` array contains valid creator slugs/IDs
- `sources` array contains valid platform names or source identifiers
- `searchQuery` is optional string
- `userId` is required (multi-user support)
- `userId` is required (multi-user support)

---

## Future Enhancements

1. **Tag System**: Add tags to creators, handles, and media for better organization
2. **Board Sharing**: Add sharing/permissions for saved boards
3. **Board Templates**: Pre-defined board templates for common use cases
4. **Relationship Types**: Normalize relationship types into enum or separate node type
5. **Image Pool**: Store image pool URLs as separate Media nodes with relationship
6. **Search Index**: Full-text search index on creator names, bios, context keywords

