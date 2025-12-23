# Ontology & Graph Management

## Status

Accepted

## Context

As the knowledge graph grows, we need strategies to maintain data quality, handle identity resolution, and manage graph hygiene to prevent degradation over time.

## Decision

Establish strict ontology rules for node types, relationship types, and data quality management.

## Rationale

**Data Integrity**: Prevents graph pollution from incorrect relationships or duplicate identities.

**Query Performance**: Consistent patterns enable efficient Cypher queries.

**Maintainability**: Clear rules make the graph easier to understand and debug.

**Scalability**: Proper taxonomy supports growth to thousands of creators and millions of media items.

## Implementation

### 1. Canonicalization & Identity Resolution

**Slug Uniqueness**:
- Creator slugs must be unique
- System generates slug from display name with collision handling
- If collision: append platform or number (e.g., `sjokz-csgo`, `sjokz-2`)

**Aliasing Strategy**:
- Creator node holds canonical name (real name: "Eefje Depoortere")
- Handle nodes hold platform usernames (can differ: "@sjokz", "Sjokz", "sjokz")
- No forced matching between Creator name and Handle username

### 2. Edge Taxonomy

**Strict Relationship Types**:

- `[:OWNS_HANDLE]`: Ownership relationship (Creator -> Handle)
  - Properties: `status` (active/suspended/abandoned), `verified` (boolean), `verifiedAt` (datetime)

- `[:ON_PLATFORM]`: Structural (Handle -> Platform)
  - Properties: `joinedAt` (datetime), `followerCount` (integer)

- `[:REFERENCES]`: Soft connection for discovery
  - Properties: `discoveredAt` (datetime), `confidence` (high/medium/low), `sourceUrl` (string)

- `[:POSTED]`: Content relationship (Handle -> Media)
  - Properties: `postedAt` (datetime)

**Query Benefit**: `MATCH (c:Creator)-[:OWNS_HANDLE]->(h:Handle)` is clear and readable.

### 3. Confidence & Verification

**Verification Levels**:
- `verified: false`: Unverified (from crawler, needs confirmation)
- `verified: true`: Verified (user confirmed or high-confidence heuristic)

**Verification Pathways**:
1. **Heuristic**: Link in official bio (High confidence → auto-verify)
2. **Inference**: Exact username match across platforms (Medium confidence → requires review)
3. **Manual**: User clicks "Confirm" (100% confidence)

**Ingestion Rule**: Only ingest Media from `verified: true` handles.

### 4. Graph Hygiene

**Soft Deletes**:
- Never delete Handle nodes (breaks historical analytics)
- Use `status` property on `[:OWNS_HANDLE]` edge:
  - `active`: Normal operation
  - `suspended`: Account banned, skip ingestion
  - `abandoned`: Account inactive, optional ingestion

**Status Check in Workers**:
```cypher
MATCH (c:Creator)-[r:OWNS_HANDLE {status: "active"}]->(h:Handle)
WHERE r.verified = true
RETURN h
```

### 5. Media Polymorphism

**Label Strategy**:
- Base label: `:Media` (common fields: id, url, createdAt)
- Auxiliary labels: `:Video`, `:Image`, `:Text` (platform-specific fields)

**Query Benefits**:
```cypher
// Find all videos (efficient, no null filtering)
MATCH (m:Media:Video)
RETURN m

// Find all images with dimensions
MATCH (m:Media:Image)
WHERE m.width IS NOT NULL
RETURN m
```

**Avoids Sparse Tables**: Images don't have `duration`, videos don't have `dimensions`.

## Consequences

**Positive**:
- Clean, maintainable graph structure
- Efficient queries with labels
- Clear audit trail via reference edges
- Prevents data quality degradation

**Negative**:
- Requires discipline to follow taxonomy
- More complex queries (need to check status/verification)
- Soft deletes use storage space

**Neutral**:
- Can add new relationship types as needed
- Labels can be added/removed without breaking queries

## Alternatives Considered

**Hard Deletes**: Rejected because it breaks historical analytics and relationships.

**Single Media Type**: Rejected because it creates sparse tables with many null fields.

**No Verification**: Rejected because false positives would pollute the graph.

## Implementation Notes

- Document all relationship types in schema documentation
- Enforce relationship types in application code (don't create ad-hoc relationships)
- Regular graph audits to find orphaned nodes or incorrect relationships
- Migration scripts to clean up legacy data
- Monitoring for verification rates and confidence scores

## References

- Knowledge graph best practices
- Neo4j relationship modeling
- Data quality management


