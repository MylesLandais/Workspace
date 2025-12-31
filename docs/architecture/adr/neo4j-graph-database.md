# Neo4j Graph Database

## Status

Accepted

## Context

We need to store and query relationships between Posts, Subreddits, Users, and Media. The data model is inherently graph-like with many relationships.

## Decision

Use Neo4j as the primary database instead of a relational database (PostgreSQL) or document store.

## Rationale

**Native Graph Operations**: Relationships are first-class citizens in Neo4j. Queries like "all posts from subreddits user subscribes to" are natural and performant.

**Cypher Query Language**: More intuitive for graph traversals than SQL joins. Example: `(p:Post)-[:POSTED_IN]->(s:Subreddit)` is clearer than multi-table joins.

**Flexible Schema**: Easy to add new relationship types or node properties without migrations. Good for evolving requirements.

**Performance**: Graph traversals are optimized. Finding related content (e.g., "posts by same author") is fast.

## Consequences

**Positive**:
- Natural fit for social/content graph data
- Expressive queries for feed generation
- Easy to model complex relationships (e.g., FeedGroup -> Source -> IngestRule)

**Negative**:
- Team needs to learn Cypher
- Smaller ecosystem than PostgreSQL
- Horizontal scaling more complex
- Some operations (aggregations, full-text search) may be slower

**Neutral**:
- Requires separate database infrastructure
- Tooling and drivers are mature

## Alternatives Considered

**PostgreSQL with recursive CTEs**: Can model graphs but queries become complex and less performant.

**ArangoDB**: Multi-model database, but Neo4j has better tooling and community.

**DynamoDB**: NoSQL but not optimized for graph queries.

## Implementation Notes

### Current Schema

The graph database uses the following node types and relationships:

**Core Feed Schema** (Migration 001):
- `(:Post)` - Reddit posts with metadata (id, title, url, image_hash, created_utc, score)
- `(:Subreddit)` - Subreddit metadata (name, subscribers, description)
- `(:User)` - User accounts (username)
- `(:Post)-[:POSTED_IN]->(:Subreddit)` - Post to subreddit relationship

**Creator/Handle/Media Schema** (Migration 002):
- `(:Creator)` - Canonical creator identity (uuid, name, slug, bio)
- `(:Handle)` - Platform-specific accounts (uuid, username, profile_url)
- `(:Platform)` - Social media platforms (name, slug)
- `(:Media)` - Media content (uuid, title, source_url, publish_date, media_type)
- `(:Video)` - Video media (extends Media with duration, view_count)
- `(:Image)` - Image media (extends Media with width, height)
- `(:Text)` - Text media (extends Media with body_content)
- `(:Creator)-[:OWNS_HANDLE]->(:Handle)` - Creator ownership with verification status
- `(:Handle)-[:ON_PLATFORM]->(:Platform)` - Handle platform association
- `(:Handle)-[:PUBLISHED]->(:Media)` - Content publishing relationship

**Web Crawler Schema** (Migration 003):
- `(:WebPage)` - Web pages for adaptive crawling (normalized_url, content_hash, simhash)
- `(:WebPage)-[:CRAWLED_AT]->()` - Crawl history with timestamps

**Image Deduplication** (Migration 005):
- `image_hash` property on Post nodes for duplicate detection
- Indexes on `image_hash` and `url` for fast duplicate queries

### Query Patterns

**Feed Generation**:
```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE p.created_utc >= $since
RETURN p
ORDER BY p.created_utc DESC
LIMIT $limit
```

**Creator Unified Feed**:
```cypher
MATCH (c:Creator {uuid: $creator_uuid})
  -[:OWNS_HANDLE {verified: true, status: 'Active'}]
  ->(h:Handle)
MATCH (h)-[:PUBLISHED]->(m:Media)
WHERE m.publish_date IS NOT NULL
RETURN m
ORDER BY m.publish_date DESC
LIMIT $limit
```

**Duplicate Detection**:
```cypher
MATCH (p:Post)
WHERE p.image_hash IS NOT NULL
WITH p.image_hash as hash, collect(p) as posts
WHERE size(posts) > 1
RETURN hash, size(posts) as count, posts
```

### Indexes

- `post_id_unique` - Unique constraint on Post.id
- `post_created_utc_index` - Index on Post.created_utc for time-based queries
- `post_image_hash_index` - Index on Post.image_hash for duplicate detection
- `creator_slug_unique` - Unique constraint on Creator.slug
- `handle_username_index` - Index on Handle.username
- `webpage_url_unique` - Unique constraint on WebPage.normalized_url

### Migration Files

- `src/feed/storage/migrations/001_initial_schema.cypher` - Core feed schema
- `src/feed/storage/migrations/002_creator_handle_media_schema.cypher` - Creator/Handle/Media ontology
- `src/feed/storage/migrations/003_web_crawler_schema.cypher` - Web crawler schema
- `src/feed/storage/migrations/004_temporal_versioning.cypher` - Temporal versioning
- `src/feed/storage/migrations/005_post_image_hash.cypher` - Image hash support

## References

- [ADR: Multi-Source Entity Organization](./multi-source-entities.md)
- [ADR: Ontology Management](./ontology-management.md)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)
- Neo4j Cypher manual
- Implementation: `src/feed/storage/neo4j_connection.py`
- Migrations: `src/feed/storage/migrations/`




