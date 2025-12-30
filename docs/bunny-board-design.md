# Board/FeedGroup/Channel Design Exploration

## Context

We need to design an organizational system that supports:
- Saved filter presets (Bunny "Boards")
- Source collections (Bunny "FeedGroups")
- Entity and source selection applied as filters
- User-specific organization
- Channels/subscriptions model
- Modern use cases beyond traditional OPML folder structure

## Problem Statement

Traditional OPML folder systems are stale and don't handle new organizational needs. We need a flexible model that supports:
1. **Filter Presets**: Save combinations of entity/source filters for quick switching
2. **Source Collections**: Group sources together (current FeedGroup concept)
3. **Channels/Subscriptions**: Organizational structure for content discovery
4. **User Personalization**: Each user has their own organizational structure

## Current Concepts

### Bunny "Boards"
- Saved filter presets (persons, sources, search query)
- Quick switching between different feed views
- Example: "Linux Rice" board with filters for r/unixporn, r/hyprland, etc.

### Bunny "FeedGroups"
- Collections of sources (subreddits, handles, etc.)
- Organizational grouping of content sources
- Example: "Gaming" group containing multiple gaming subreddits

### Overlap and Differences
- **Boards** are query/filter presets
- **FeedGroups** are source collections
- Both serve organizational purposes
- Could be unified or kept separate

## Design Options

### Option 1: Unified "Collection" Model

Create a single flexible `Collection` entity that can be:
- **Filter-based**: Like Bunny boards (filters applied to all content)
- **Source-based**: Like FeedGroups (specific sources grouped)
- **Hybrid**: Combination of both

```cypher
(:Collection {
  id: ID!,
  name: String!,
  userId: String!,
  type: CollectionType!,  // FILTER, SOURCE, HYBRID
  filters: FilterState,   // Optional: entity/source filters
  sourceIds: [ID!]!,      // Optional: specific source/handle IDs
  createdAt: DateTime!
})
```

**Pros**:
- Single concept to learn
- Flexible enough for various use cases
- Can support both patterns

**Cons**:
- More complex queries
- Less clear semantics
- Might be too abstract

### Option 2: Separate But Related

Keep Boards and FeedGroups separate but allow relationships:

```cypher
(:SavedBoard {
  id: ID!,
  name: String!,
  userId: String!,
  filters: FilterState!,
  createdAt: DateTime!
})

(:FeedGroup {
  id: ID!,
  name: String!,
  userId: String!,
  sourceIds: [ID!]!,
  createdAt: DateTime!
})

// Optional: Board can reference FeedGroup
(:SavedBoard)-[:USES_GROUP]->(:FeedGroup)
```

**Pros**:
- Clear separation of concerns
- Explicit semantics
- Easier to query

**Cons**:
- Two concepts to maintain
- Potential duplication
- Less flexible

### Option 3: FeedGroup with Filter Support

Extend FeedGroups to support optional filters:

```cypher
(:FeedGroup {
  id: ID!,
  name: String!,
  userId: String!,
  sourceIds: [ID!]!,      // Sources in this group
  filters: FilterState,   // Optional: additional filters to apply
  createdAt: DateTime!
})
```

**Pros**:
- Single concept
- Backward compatible with existing FeedGroups
- Clear upgrade path

**Cons**:
- Mixes concerns (sources + filters)
- May confuse users

### Option 4: Channel/Subscription Model

Introduce a "Channel" concept that encompasses both:

```cypher
(:Channel {
  id: ID!,
  name: String!,
  userId: String!,
  description: String,
  // Sources included in channel
  sourceIds: [ID!]!,
  // Filters applied to channel content
  filters: FilterState,
  // Organization metadata
  category: String,
  tags: [String!]!,
  createdAt: DateTime!
})
```

Channels can be:
- **Subscriptions**: Source-based channels
- **Views**: Filter-based channels
- **Curated**: Hybrid channels

**Pros**:
- Modern terminology (channels/subscriptions)
- Flexible and extensible
- Supports organizational hierarchies (categories, tags)
- Familiar mental model

**Cons**:
- New concept to introduce
- Migration needed from FeedGroups
- More complex initially

## Recommendation: Option 4 (Channel Model)

The Channel model best fits the requirements:

1. **Familiar Mental Model**: Channels/subscriptions are well-understood
2. **Flexibility**: Supports both source collections and filter presets
3. **Extensibility**: Can add categories, tags, nesting, sharing
4. **Future-Proof**: Handles new use cases beyond OPML folders
5. **User-Centric**: Each user has their own channel organization

## Implementation Approach

### Phase 1: Basic Channels
- Channel entity with sources and optional filters
- CRUD operations
- User-specific channels

### Phase 2: Enhanced Channels
- Categories/tags for organization
- Channel descriptions
- Channel ordering/preferences

### Phase 3: Advanced Features
- Channel hierarchies/nesting
- Channel sharing (if needed)
- Channel templates
- Channel discovery

## GraphQL Schema

```graphql
type Channel {
  id: ID!
  name: String!
  description: String
  userId: String!
  
  # Source-based organization
  sources: [Source!]!  # Handles/sources in this channel
  
  # Filter-based organization (optional)
  filters: FilterState
  
  # Organization metadata
  category: String
  tags: [String!]!
  
  # Metadata
  createdAt: DateTime!
  updatedAt: DateTime!
  mediaCount: Int!  # Computed: number of media items
}

input ChannelInput {
  name: String!
  description: String
  sourceIds: [ID!]!
  filters: FilterInput
  category: String
  tags: [String!]
}

extend type Query {
  channels: [Channel!]!
  channel(id: ID!): Channel
  channelsByCategory(category: String!): [Channel!]!
}

extend type Mutation {
  createChannel(input: ChannelInput!): Channel!
  updateChannel(id: ID!, input: ChannelInput!): Channel!
  deleteChannel(id: ID!): Boolean!
  addSourcesToChannel(channelId: ID!, sourceIds: [ID!]!): Channel!
  removeSourcesFromChannel(channelId: ID!, sourceIds: [ID!]!): Channel!
}
```

## Migration Strategy

### From FeedGroups
- Migrate existing FeedGroups to Channels
- Set `filters` to null (source-only channels)
- Preserve source associations

### From Bunny Boards
- Migrate SavedBoards to Channels
- Set `sourceIds` to empty (filter-only channels)
- Preserve filter state

## Use Cases

### Use Case 1: Source Collection
"I want all Linux-related subreddits in one channel"
- Create channel with multiple source IDs
- No filters needed

### Use Case 2: Filter Preset
"I want to see all content from Taylor Swift and Selena Gomez"
- Create channel with person filters
- No specific sources (aggregates from all their handles)

### Use Case 3: Hybrid Channel
"I want gaming content from Reddit, but only posts about RPGs"
- Create channel with gaming source IDs
- Add search filter for "RPG"

### Use Case 4: Category Organization
"Organize my channels by topic: Gaming, Tech, Pop Culture"
- Use category field for organization
- Channels grouped by category in UI

## Open Questions

1. **Nesting**: Should channels support sub-channels or folders? (Defer to Phase 3)

2. **Sharing**: Should channels be shareable between users? (Defer to future)

3. **Templates**: Should there be channel templates for common patterns? (Phase 3)

4. **Discovery**: Should there be public/shared channels for discovery? (Future)

5. **Naming**: Is "Channel" the right term, or prefer "Collection", "Feed", "Board"? (Channel seems best)

## Next Steps

1. **Validate Concept**: Review channel model with team
2. **Design UI**: How channels appear in sidebar/navigation
3. **Schema Implementation**: Implement Channel node in Neo4j
4. **GraphQL API**: Create Channel queries and mutations
5. **Migration Plan**: Plan migration from FeedGroups/Boards
6. **Phase 1 Implementation**: Basic channels with sources and filters

## References

- [Bunny Analysis](./bunny-analysis.md)
- [Component Interface Map](./bunny-component-interface-map.md)
- [Data Schema Expectations](./bunny-data-schema-expectations.md)
- [Integration ADR](./architecture/adr/bunny-feed-integration.md)





