# Neo4j Query Performance & Optimization

## Current State

### Query Organization

Queries are well-organized by domain:

- `feed.ts` - Feed queries with filtering and pagination
- `images.ts` - Image hash and cluster management
- `creators.ts` - Creator identity queries
- `sources.ts` - Source and subscription management

## Performance Issues

### 1. Complex Feed Query (feed.ts)

**Current Issues:**

- 6 OPTIONAL MATCHes creating cartesian products
- Dynamic WHERE clause building leads to suboptimal query plans
- Multiple JOINs without proper indexing hints
- Text search using CONTAINS (full-text search would be better)

**Impact:**

- Query time increases exponentially with filter combinations
- Memory usage spikes with complex filters
- Pagination cursor implementation inefficient

**Optimizations Needed:**

1. **Use Query Parameters with Index Hints**

```cypher
// Before: Dynamic query building
// After: Use index hints and static queries
MATCH (m:Media)
USING INDEX m:Media(mime_type)
WHERE m.mime_type STARTS WITH 'image/'
```

2. **Separate Query Paths**

```cypher
// Current: One complex query
// Better: Multiple focused queries combined in app layer
MATCH (m:Media)-[:APPEARED_IN]->(p:Post)
WHERE p.created_utc < $cursor
RETURN m, p
LIMIT 20
```

3. **Implement Full-Text Search**

```cypher
// Before: toLower(p.title) CONTAINS toLower($search)
// After: Full-text index
CALL db.index.fulltext.queryNodes('titleIndex', $search)
YIELD node as p
```

### 2. Nested Queries in getImageLineage

**Current Issues:**

- Loops calling `getMediaById` for each member
- N+1 query problem (1 query + N additional queries)
- Multiple roundtrips to database

**Impact:**

- Linear time complexity O(n) instead of O(1)
- High latency for large clusters
- Unnecessary database roundtrips

**Optimization Needed:**

```cypher
// Single query to fetch all media
MATCH (m:Media {id: $mediaId})-[:BELONGS_TO]->(c:ImageCluster)
MATCH (all:Media)-[:BELONGS_TO]->(c)
WITH c, all
ORDER BY all.created_at ASC
WITH c, collect(all) AS members
OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:Media)
RETURN c, members, canonical
```

### 3. Similar Images Query

**Current Issues:**

- Returns cluster members only (no actual similarity scoring)
- Calls `getMediaById` for each result
- No phash hamming distance calculation

**Impact:**

- False positives in results
- N+1 query problem
- No relevance ranking

**Optimization Needed:**

```cypher
// Use hamming distance for actual similarity
MATCH (m:Media {id: $mediaId})
MATCH (similar:Media)
WHERE similar.phash IS NOT NULL
WITH m, similar
CALL apoc.bitwise.xor(toInteger(m.phash), toInteger(similar.phash)) YIELD value
WITH similar, apoc.bitwise.popcount(value) AS hammingDistance
ORDER BY hammingDistance ASC
LIMIT $limit
RETURN similar, hammingDistance
```

## Performance Targets

### Current Baseline

- Feed query (no filters): ~200-500ms
- Feed query (complex filters): ~1-3s
- Image lineage query: ~500ms-2s
- Similar images query: ~200-1s

### Target Metrics

- Feed query (no filters): <100ms
- Feed query (complex filters): <300ms
- Image lineage query: <200ms
- Similar images query: <100ms

## Implementation Plan

### Phase 1: Quick Wins (Week 1)

1. Add index hints to feed query
2. Implement static query patterns
3. Add query logging for profiling

### Phase 2: Refactor Complex Queries (Week 2)

1. Split feed query into focused queries
2. Eliminate N+1 problems in lineage/similar queries
3. Add pagination cursor optimization

### Phase 3: Advanced Features (Week 3-4)

1. Implement full-text search index
2. Add APOC procedures for phash comparison
3. Implement query result caching

## Index Strategy

### Existing Indexes

```cypher
CREATE INDEX post_created_utc IF NOT EXISTS FOR (p:Post) ON (p.created_utc)
CREATE INDEX post_is_image IF NOT EXISTS FOR (p:Post) ON (p.is_image)
CREATE INDEX media_sha256 IF NOT EXISTS FOR (m:Media) ON (m.sha256)
CREATE INDEX media_phash IF NOT EXISTS FOR (m:Media) ON (m.phash)
CREATE INDEX cluster_canonical IF NOT EXISTS FOR (c:ImageCluster) ON (c.canonical_sha256)
```

### Recommended Additional Indexes

```cypher
-- Composite indexes for common queries
CREATE INDEX media_mime_created IF NOT EXISTS FOR (m:Media) ON (m.mime_type, m.created_at)
CREATE INDEX post_created_image IF NOT EXISTS FOR (p:Post) ON (p.created_utc, p.is_image)

-- Full-text search index
CALL db.index.fulltext.createNodeIndex('titleIndex', ['Post.title'])

-- Relationship lookups
CREATE INDEX media_post IF NOT EXISTS FOR ()-[r:APPEARED_IN]-() ON (r.position)
```

## Query Caching

### Cache Keys

```
feed:{cursor}:{limit}:{filters_hash}
media:{mediaId}
cluster:{clusterId}
lineage:{mediaId}
similar:{mediaId}:{limit}
```

### Cache TTL

- Feed queries: 5 minutes
- Media metadata: 1 hour
- Cluster data: 10 minutes
- Image lineage: 30 minutes

## Monitoring

### Metrics to Track

1. Query execution time (p50, p95, p99)
2. Database rows examined per query
3. Index usage (which indexes are hit)
4. Cache hit rate
5. Connection pool utilization

### Alerting Thresholds

- Feed query >500ms
- Lineage query >1s
- Similar query >500ms
- Cache hit rate <70%

## Best Practices

### Query Writing

1. **Always use parameters** - Prevents injection, allows caching
2. **Use specific labels** - Instead of generic `(n)`, use `(m:Media)`
3. **Limit result sets early** - Use LIMIT, LIMIT in subqueries
4. **Profile queries** - Use PROFILE keyword to find bottlenecks
5. **Avoid OPTIONAL MATCH when possible** - Use WHERE if relationship must exist

### Data Modeling

1. **Denormalize frequently accessed fields** - Trade space for speed
2. **Use composite indexes** - For multi-field queries
3. **Keep relationship counts reasonable** - Avoid supernodes
4. **Use appropriate data types** - Date for dates, Int for integers

## Next Steps

1. **Profile current queries** using PROFILE keyword
2. **Add index hints** to slow queries
3. **Implement Valkey caching** for hot data paths
4. **Refactor N+1 queries** to single-query solutions
5. **Add monitoring** and alerting
6. **Benchmark before/after** each optimization

## References

- Neo4j Performance Tuning: https://neo4j.com/docs/operations-manual/current/performance/
- Cypher Query Tuning: https://neo4j.com/docs/cypher-manual/current/query-tuning/
- APOC Procedures: https://neo4j.com/labs/apoc/5/
- Full-Text Search: https://neo4j.com/docs/operations-manual/current/indexes-for-full-text-search/
