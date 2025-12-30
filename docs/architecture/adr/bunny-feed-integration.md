# Bunny Feed Integration

## Status

Accepted (with pending design exploration on Boards/FeedGroups)

## Context

The Bunny Feed application (extracted from `bunny-feed.zip`) demonstrates a well-designed UI/UX for entity management, visual feed display, and saved filter presets ("Boards"). We need to integrate these features into the Bunny architecture while maintaining our graph-native approach and GraphQL API.

Key features from Bunny:
- Entity/Identity Management interface with source mapping
- Saved Boards (filter presets)
- Visual masonry feed layout
- Advanced filtering system (persons, sources, search)
- Relationship management between entities
- Theme system

Bunny is a client-side React application using LocalStorage, while Bunny uses Neo4j + GraphQL. We need to bridge this architectural gap.

## Decision

Integrate Bunny's UI/UX patterns and features into Bunny by:

1. **Extending Creator-Handle Model**: Add fields for aliases, context keywords, and relationships
2. **Adding Saved Boards**: Introduce SavedBoard nodes for filter presets
3. **Porting UI Components**: Adapt Bunny React components to use GraphQL instead of LocalStorage
4. **Enhancing Feed Queries**: Extend feed query to support person/source/search filters
5. **Preserving UX Patterns**: Maintain Bunny's excellent UI/UX while using Bunny's backend

## Rationale

**UI/UX Excellence**: Bunny demonstrates excellent patterns for entity management, filtering, and feed display that should be preserved.

**Feature Completeness**: Bunny's features (boards, relationships, source visibility) enhance Bunny's capabilities without conflicting with core architecture.

**Incremental Integration**: Features can be integrated incrementally, allowing gradual migration and testing.

**Architectural Compatibility**: Bunny's concepts map well to Bunny's graph model:
- IdentityProfile → Creator + Handle
- SourceLink → Handle nodes
- SavedBoard → SavedBoard nodes
- Relationships → RELATED_TO edges

## Implementation

### 1. Schema Extensions

#### Creator Node Extensions
```cypher
// Add to existing Creator node
SET c.aliases = $aliases,           // Array of name variations
    c.contextKeywords = $keywords,  // Array for AI/content discovery
    c.imagePool = $imagePool        // Optional: Array of image URLs
```

#### Handle Node Extensions
```cypher
// Add to existing Handle node
SET h.label = $label,      // e.g., "Main", "Spam", "Fan Page"
    h.hidden = $hidden     // Boolean: visibility toggle for feeds
```

#### New Relationship Type
```cypher
// Creator-to-Creator relationships
(:Creator)-[:RELATED_TO {
  type: String!,           // e.g., "Best Friend", "Partner", "Co-star"
  createdAt: DateTime!,
  updatedAt: DateTime!
}]->(:Creator)
```

#### SavedBoard Node
```cypher
(:SavedBoard {
  id: ID!,
  name: String!,
  persons: [String!]!,     // Array of creator slugs/IDs
  sources: [String!]!,     // Array of platform/source identifiers
  searchQuery: String,
  createdAt: DateTime!,
  updatedAt: DateTime!,
  userId: String           // For multi-user support
})
```

### 2. GraphQL Schema Extensions

```graphql
# Extend Creator type
extend type Creator {
  aliases: [String!]!
  contextKeywords: [String!]!
  imagePool: [String!]!
  relationships: [Relationship!]!
}

# Extend Handle type
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

# Extend feed query
extend type Query {
  feed(
    cursor: String
    limit: Int
    persons: [String!]      # NEW
    sources: [String!]      # NEW
    searchQuery: String     # NEW
  ): FeedConnection!
  
  savedBoards: [SavedBoard!]!
  savedBoard(id: ID!): SavedBoard
}

# New mutations
extend type Mutation {
  updateCreator(id: ID!, input: UpdateCreatorInput!): Creator!
  deleteCreator(id: ID!): Boolean!
  updateHandleVisibility(handleId: ID!, hidden: Boolean!): Handle!
  addRelationship(creatorId: ID!, targetId: ID!, type: String!): Creator!
  removeRelationship(creatorId: ID!, targetId: ID!): Creator!
  createSavedBoard(name: String!, filters: FilterInput!): SavedBoard!
  updateSavedBoard(id: ID!, name: String, filters: FilterInput): SavedBoard!
  deleteSavedBoard(id: ID!): Boolean!
}
```

### 3. Component Integration Strategy

**Phase 1: Backend Schema**
- Extend Neo4j schema with new fields
- Add GraphQL types and resolvers
- Implement Cypher queries for new operations

**Phase 2: Component Porting**
- Port EntityManager to use GraphQL queries/mutations
- Replace LocalStorage calls with Apollo Client hooks
- Maintain Bunny's UI/UX patterns

**Phase 3: Feature Enhancement**
- Integrate with existing Bunny features (deduplication, etc.)
- Add performance optimizations
- Enhance with Bunny's advanced capabilities

### 4. Data Migration

Migration from Bunny LocalStorage to Neo4j:

1. **Identity Profiles → Creators**:
   - Extract IdentityProfile objects
   - Create Creator nodes with mapped properties
   - Create Handle nodes from sources array
   - Create RELATED_TO relationships

2. **Saved Boards → SavedBoard Nodes**:
   - Extract SavedBoard objects
   - Create SavedBoard nodes
   - Associate with user (if multi-user)

## Consequences

**Positive**:
- Excellent UI/UX patterns preserved
- Feature-rich entity management
- Enhanced filtering capabilities
- Saved filter presets improve user workflow
- Relationship management enables content discovery
- Source visibility controls provide fine-grained filtering

**Negative**:
- Additional schema complexity
- More GraphQL operations to maintain
- Migration required from LocalStorage to Neo4j
- Component refactoring needed (LocalStorage → GraphQL)

**Neutral**:
- Can be implemented incrementally
- Backward compatible with existing Creator/Handle model
- Optional features (relationships, image pools) can be added gradually

## Alternatives Considered

**1. Rebuild UI from Scratch**: Rejected because Bunny's UI/UX is excellent and rebuilding would waste effort.

**2. Keep Bunny Separate**: Rejected because integration provides better user experience and leverages Bunny's backend capabilities.

**3. Hybrid Approach (Bunny UI + Bunny API)**: This is the chosen approach - best of both worlds.

**4. Simplified Integration (No Relationships/Boards)**: Rejected because these features add significant value and are worth the integration effort.

## Implementation Notes

- Start with schema extensions, then backend, then frontend
- Test migrations thoroughly with sample Bunny data
- Preserve Bunny's UI/UX patterns in component porting
- Use Apollo Client cache for optimistic updates
- Consider relationship type normalization in future (currently free-form strings)

## Resolved Questions

1. **✅ React Version**: Upgrade to React 19 (team encourages latest)

2. **✅ AI Integration**: Future/beta feature, leave hooks for agent dev toolkit integration

3. **✅ Relationship Types**: Free-form strings (team prefers type safety but relationship types are beyond domain)

4. **✅ Multi-user Support**: Required - users need to track and configure views specific to their tastes

5. **🔄 Board/FeedGroup Concept**: Needs design exploration - see design doc for organizational model

## Remaining Open Questions

1. **Image Pool Storage**: Store as URL array or as separate Media nodes? Start with array, consider nodes if relationships needed.

2. **Board Sharing**: Should boards be shareable? Defer to future enhancement.

3. **Board/FeedGroup Organizational Model**: How to reconcile Boards (filter presets), FeedGroups (source collections), and channels/subscriptions? See design exploration document.

## References

- [Bunny Analysis](../bunny-analysis.md)
- [Component Interface Map](../bunny-component-interface-map.md)
- [Data Schema Expectations](../bunny-data-schema-expectations.md)
- [Tech Stack Conflicts](../bunny-tech-stack-conflicts.md)
- [Creator-Handle Model](./creator-handle-model.md)
- [Multi-Source Entities](./multi-source-entities.md)

