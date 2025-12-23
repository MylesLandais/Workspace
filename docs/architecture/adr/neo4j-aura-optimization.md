# Neo4j Aura Free Tier Optimization

## Status

Accepted (Planned - Not Yet Implemented)

## Context

We're using Neo4j Aura free tier which has strict limits:
- **50,000 nodes** maximum
- **175,000 relationships** maximum
- No ability to upgrade individual instances incrementally

As the application grows, we need strategies to stay within these limits while maintaining functionality and data quality. We cannot simply delete all old data, as some historical content may be valuable (cited items, user annotations, trending topics).

**Current Status**: This optimization strategy is planned but not yet implemented. The system is currently in early stages and has not yet approached the free tier limits. This ADR documents the planned approach for when limits become a concern.

## Decision

Implement a multi-layered optimization strategy:
1. **Data archival** - Aggregate old content into summary nodes
2. **Relationship pruning** - Remove weak or redundant relationships
3. **Selective retention** - Keep high-value content (cited, annotated, referenced)
4. **Valkey offloading** - Move frequently accessed but non-critical data to cache layer
5. **Monitoring and alerts** - Track usage and warn before hitting limits

## Rationale

**Cost Efficiency**: Staying on free tier as long as possible reduces infrastructure costs during early growth.

**Data Preservation**: Archival strategy preserves important information (aggregates, summaries) while removing detailed nodes.

**Performance**: Pruning weak relationships improves query performance and reduces storage.

**Selective Retention**: Prioritizing high-value content ensures important data isn't lost.

**Proactive Management**: Monitoring prevents unexpected limit hits that could break the application.

**Migration Path**: Clear strategy for when to upgrade, with data already optimized for migration.

## Consequences

**Positive**:
- Extends free tier viability significantly
- Improves query performance by reducing graph size
- Maintains data quality by keeping important content
- Provides clear upgrade path when needed
- Reduces storage costs even after upgrading

**Negative**:
- Loss of detailed historical data (mitigated by aggregation)
- More complex data management logic
- Need to implement archival and pruning processes
- Potential user confusion if old content disappears (mitigated by clear archival)

**Neutral**:
- Requires ongoing monitoring and maintenance
- May need to adjust retention policies based on usage patterns

## Alternatives Considered

**Upgrade Immediately**: Paying for Aura from the start eliminates limits but increases costs unnecessarily during early development.

**Delete Old Data**: Simple but loses valuable historical context and user annotations.

**External Storage**: Moving old data to PostgreSQL or S3 adds complexity and breaks graph queries across time periods.

**Multiple Free Tier Instances**: Splitting data across instances breaks graph relationships and adds operational complexity.

## Implementation Notes

### Data Archival Strategy

**Monthly Aggregation**:

```cypher
// Aggregate old items into Archive nodes
MATCH (i:Item) 
WHERE i.created_at < date() - duration('P90D')
  AND NOT (i)<-[:CITES]-()
  AND NOT (i)<-[:ANNOTATED]-()
  AND NOT (i)<-[:READ]-()

WITH i.source_id as source, 
     collect(i)[0..1000] as itemsToArchive,
     count(i) as totalCount

// Create Archive node with aggregated data
CREATE (a:Archive {
  source_id: source,
  period: '2024-Q4',
  item_count: totalCount,
  top_topics: [t IN 
    [topic IN [i IN itemsToArchive | i.topics] | topic] 
    WHERE topic IS NOT NULL 
    | topic][0..10],
  date_range: {
    start: date() - duration('P90D'),
    end: date()
  },
  created_at: datetime()
})

// Link archive to source
MATCH (s:Source {id: source})
CREATE (a)-[:ARCHIVES]->(s)

// Delete archived items
DETACH DELETE i IN itemsToArchive

RETURN count(a) as archivesCreated, 
       sum(a.item_count) as itemsArchived
```

**Preserve High-Value Content**:

```cypher
// Items to keep (cited, annotated, or recently accessed)
MATCH (i:Item)
WHERE (i)<-[:CITES]-() 
   OR (i)<-[:ANNOTATED]-()
   OR (i)<-[:READ {read_at: date() - duration('P30D')}]->()

SET i.retention_priority = 'high'
SET i.retention_reason = 
  CASE 
    WHEN (i)<-[:CITES]-() THEN 'cited'
    WHEN (i)<-[:ANNOTATED]-() THEN 'annotated'
    ELSE 'recently_read'
  END
```

### Relationship Pruning

**Remove Weak Similarity Relationships**:

```cypher
// Keep only strong similarity connections
MATCH (i:Item)-[r:SIMILAR_TO]->(j:Item)
WHERE r.score < 0.5
  AND NOT (i)-[:CITES]->(j)
  AND NOT (j)-[:CITES]->(i)

DELETE r

RETURN count(r) as relationshipsPruned
```

**Consolidate Redundant Tags**:

```cypher
// Merge similar tags (e.g., "AI" and "artificial-intelligence")
MATCH (t1:Tag), (t2:Tag)
WHERE t1.name <> t2.name
  AND toLower(t1.name) = toLower(t2.name)
  OR levenshteinDistance(t1.name, t2.name) < 3

// Move relationships to canonical tag
MATCH (t1)-[r]->(item)
CREATE (t2)-[r2:RELATED_TO]->(item)
SET r2 = properties(r)

// Delete duplicate tag
DETACH DELETE t1

RETURN count(t1) as tagsConsolidated
```

### APOC TTL for Automatic Expiration

```cypher
// Enable APOC TTL for automatic node expiration
// Note: Requires APOC library installation

// Set TTL on low-priority items
MATCH (i:Item)
WHERE i.retention_priority IS NULL
  OR i.retention_priority = 'low'

CALL apoc.ttl.expire(i, duration('P180D'))
YIELD node
RETURN count(node) as nodesWithTTL
```

### Usage Monitoring

```cypher
// Monitor current usage
MATCH (n)
WITH count(n) as nodeCount
MATCH ()-[r]->()
WITH nodeCount, count(r) as relCount

RETURN 
  nodeCount,
  relCount,
  nodeCount / 50000.0 * 100 as nodeUsagePercent,
  relCount / 175000.0 * 100 as relUsagePercent,
  CASE 
    WHEN nodeCount > 45000 OR relCount > 157500 THEN 'CRITICAL'
    WHEN nodeCount > 40000 OR relCount > 140000 THEN 'WARNING'
    ELSE 'OK'
  END as status
```

### Valkey Offloading

Move frequently accessed but non-critical data to Valkey:

```python
# Store old item metadata in Valkey instead of Neo4j
async def archive_item_metadata(item_id: str):
    # Get full item data
    item = await neo4j.get_item(item_id)
    
    # Store in Valkey with long TTL
    await valkey.setex(
        f"archive:item:{item_id}",
        31536000,  # 1 year
        json.dumps({
            "title": item.title,
            "url": item.url,
            "source": item.source_id,
            "created_at": item.created_at,
            "topics": item.topics
        })
    )
    
    # Delete from Neo4j, keep only essential relationships
    await neo4j.delete_item_keep_relationships(item_id)
```

### Migration Path

When approaching limits, prepare for upgrade:

```cypher
// Generate migration report
MATCH (n)
WITH labels(n) as nodeLabels, count(n) as count
RETURN nodeLabels, count
ORDER BY count DESC

// Identify largest relationship types
MATCH ()-[r]->()
WITH type(r) as relType, count(r) as count
RETURN relType, count
ORDER BY count DESC

// Estimate upgrade needs
// If > 80% of limits, recommend upgrade
```

### Retention Policy Configuration

```typescript
interface RetentionPolicy {
  // Items older than this are candidates for archival
  archiveAgeDays: number;
  
  // Always keep items with these characteristics
  keepCriteria: {
    hasCitations: boolean;
    hasAnnotations: boolean;
    hasRecentReads: boolean; // within last N days
    highEngagement: boolean; // above threshold
  };
  
  // Relationship pruning thresholds
  relationshipThresholds: {
    similarityScore: number; // below this, prune
    weakConnectionAge: number; // days
  };
  
  // Monitoring thresholds
  alertThresholds: {
    nodeWarning: number; // percentage
    nodeCritical: number;
    relWarning: number;
    relCritical: number;
  };
}
```

### Implementation Schedule

**Status**: Not yet started. Implementation will begin when:
- Node count approaches 40,000 (80% of limit)
- Relationship count approaches 140,000 (80% of limit)
- Or when data growth rate indicates limits will be reached within 3 months

**Planned Implementation Order**:
1. **Phase 1**: Set up usage monitoring and alerts
2. **Phase 2**: Implement retention priority tagging
3. **Phase 3**: Deploy relationship pruning
4. **Phase 4**: Implement archival process
5. **Phase 5**: Set up automated archival jobs
6. **Ongoing**: Monitor and adjust retention policies

## References

- [Neo4j Aura Pricing](https://neo4j.com/cloud/aura/pricing/)
- [APOC TTL Documentation](https://neo4j.com/labs/apoc/4.4/overview/apoc.ttl/)
- [ADR: Neo4j Graph Database](./neo4j-graph-database.md)
- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)

