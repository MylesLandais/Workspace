# Cursor-Based Pagination

## Status

Accepted

## Context

The feed view needs to support infinite scroll with thousands of posts. Traditional offset-based pagination becomes slow and unreliable at scale.

## Decision

Use cursor-based pagination (timestamp-based cursors) instead of offset/limit pagination for feed queries.

## Rationale

**Performance**: Offset pagination requires scanning all skipped rows. Cursor pagination uses indexed timestamp lookups.

**Consistency**: With offset pagination, new items inserted during pagination can cause duplicates or skipped items. Cursor pagination is stable.

**Infinite Scroll**: Cursor-based is the standard pattern for infinite scroll implementations (used by Twitter, Reddit, etc.).

**GraphQL Best Practice**: Cursor pagination aligns with Relay-style pagination patterns.

## Consequences

**Positive**:
- Fast queries even with large datasets
- Stable pagination (no duplicates/skips)
- Standard pattern for social feeds

**Negative**:
- Cannot jump to arbitrary page numbers
- Cursor format must be stable (we use ISO 8601 timestamps)
- Slightly more complex client implementation

**Neutral**:
- Apollo Client has built-in support via fetchMore

## Implementation

Cursor format: ISO 8601 timestamp string (e.g., "2025-12-22T08:14:39Z")

Query pattern:
```cypher
WHERE ($cursor IS NULL OR p.created_utc < datetime($cursor))
ORDER BY p.created_utc DESC
LIMIT $limit
```

## Alternatives Considered

**Offset/Limit**: Simple but doesn't scale. Rejected for performance reasons.

**Keyset Pagination**: Similar to cursor but using ID. Timestamps are more intuitive for chronological feeds.

## References

- Apollo Client pagination documentation
- Relay connection specification






