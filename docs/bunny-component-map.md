# Bunny Component Interface Map

This document maps Bunny Feed UI components to required interfaces, GraphQL queries/mutations, and integration points with the Bunny architecture.

## Component Inventory

### 1. EntityManager Component

**File**: `components/EntityManager.tsx`

**Purpose**: Full-screen admin interface for managing entity/identity profiles

**Current Interface**:
```typescript
interface EntityManagerProps {
  onBack: () => void;
}
```

**Required GraphQL Operations**:

**Queries**:
```graphql
query GetCreators($query: String, $limit: Int) {
  creators(query: $query, limit: $limit) {
    id
    slug
    name
    displayName
    bio
    avatarUrl
    verified
    handles {
      id
      platform
      username
      handle
      url
      verified
      status
      hidden  # NEW: Add hidden flag
    }
  }
}

query GetCreator($slug: String!) {
  creator(slug: $slug) {
    id
    slug
    name
    displayName
    bio
    avatarUrl
    aliases  # NEW: Add aliases field
    contextKeywords  # NEW: Add context keywords
    relationships {  # NEW: Add relationships
      target {
        id
        name
      }
      type
    }
    handles {
      id
      platform
      username
      handle
      url
      verified
      status
      hidden
      label  # NEW: Add label field
    }
  }
}
```

**Mutations**:
```graphql
mutation CreateCreator($name: String!, $displayName: String!) {
  createCreator(name: $name, displayName: $displayName) {
    id
    slug
    name
    displayName
  }
}

mutation UpdateCreator(
  $id: ID!
  $name: String
  $displayName: String
  $bio: String
  $avatarUrl: String
  $aliases: [String!]
  $contextKeywords: [String!]
) {
  updateCreator(
    id: $id
    name: $name
    displayName: $displayName
    bio: $bio
    avatarUrl: $avatarUrl
    aliases: $aliases
    contextKeywords: $contextKeywords
  ) {
    id
    name
    displayName
    bio
    aliases
    contextKeywords
  }
}

mutation DeleteCreator($id: ID!) {
  deleteCreator(id: $id)
}

mutation AddHandle(
  $creatorId: ID!
  $platform: Platform!
  $username: String!
  $url: String!
  $label: String
  $hidden: Boolean
) {
  addHandle(
    creatorId: $creatorId
    platform: $platform
    username: $username
    url: $url
    label: $label
    hidden: $hidden
  ) {
    id
    platform
    username
    handle
    url
    label
    hidden
  }
}

mutation UpdateHandleVisibility($handleId: ID!, $hidden: Boolean!) {
  updateHandleVisibility(handleId: $handleId, hidden: $hidden) {
    id
    hidden
  }
}

mutation RemoveHandle($handleId: ID!) {
  removeHandle(handleId: $handleId)
}

mutation AddRelationship($creatorId: ID!, $targetId: ID!, $type: String!) {
  addRelationship(creatorId: $creatorId, targetId: $targetId, type: $type) {
    id
    relationships {
      target {
        id
        name
      }
      type
    }
  }
}

mutation RemoveRelationship($creatorId: ID!, $targetId: ID!) {
  removeRelationship(creatorId: $creatorId, targetId: $targetId) {
    id
    relationships {
      target {
        id
        name
      }
      type
    }
  }
}
```

**Required GraphQL Schema Extensions**:
- Add `aliases: [String!]!` to Creator type
- Add `contextKeywords: [String!]!` to Creator type
- Add `relationships: [Relationship!]!` to Creator type
- Add `label: String` to Handle type
- Add `hidden: Boolean!` to Handle type
- Add `Relationship` type with `target: Creator!` and `type: String!`
- Add `updateCreator` mutation
- Add `deleteCreator` mutation
- Add `updateHandleVisibility` mutation
- Add relationship management mutations

**State Management**:
- Use Apollo Client `useQuery` for fetching creators
- Use Apollo Client `useMutation` for all mutations
- Use Apollo Client cache for optimistic updates
- Replace LocalStorage persistence with GraphQL

**Integration Points**:
- Replace `getIdentityGraph()` with GraphQL query
- Replace `saveIdentityGraph()` with GraphQL mutations
- Map `IdentityProfile` to `Creator` type
- Map `SourceLink[]` to `Handle[]` array

---

### 2. Sidebar Component

**File**: `components/Sidebar.tsx`

**Purpose**: Left sidebar with navigation, saved boards, person filters, and source filters

**Current Interface**:
```typescript
interface SidebarProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  isMobileOpen: boolean;
  savedBoards: SavedBoard[];
  onSelectBoard: (board: SavedBoard) => void;
  onDeleteBoard: (id: string) => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
  onViewChange: (view: AppView) => void;
  currentView: AppView;
}
```

**Required GraphQL Operations**:

**Queries**:
```graphql
query GetSavedBoards {
  savedBoards {
    id
    name
    filters {
      persons
      sources
      searchQuery
    }
    createdAt
  }
}

query GetCreatorsForFilter {
  creators(limit: 100) {
    id
    slug
    name
    displayName
    avatarUrl
  }
}
```

**Mutations**:
```graphql
mutation CreateSavedBoard($name: String!, $filters: FilterInput!) {
  createSavedBoard(name: $name, filters: $filters) {
    id
    name
    filters {
      persons
      sources
      searchQuery
    }
    createdAt
  }
}

mutation DeleteSavedBoard($id: ID!) {
  deleteSavedBoard(id: $id)
}
```

**Required GraphQL Schema Extensions**:
- Add `SavedBoard` type with `id`, `name`, `filters`, `createdAt`
- Add `FilterInput` input type with `persons: [String!]`, `sources: [String!]`, `searchQuery: String`
- Add `FilterState` type (same structure as FilterInput)
- Add `savedBoards` query
- Add `createSavedBoard` mutation
- Add `deleteSavedBoard` mutation

**State Management**:
- Use Apollo Client for saved boards
- Keep local state for current filters (derive from URL params or state)
- Use local state for theme (can persist in localStorage)

**Integration Points**:
- Replace LocalStorage board storage with GraphQL
- Keep filter state local (pass to feed query)
- Theme can remain local (UI preference)

---

### 3. FilterBar Component

**File**: `components/FilterBar.tsx`

**Purpose**: Top bar with search, active filter chips, and action buttons

**Current Interface**:
```typescript
interface FilterBarProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  onMenuClick: () => void;
  onRefresh: () => void;
  onSaveBoard: () => void;
}
```

**Required GraphQL Operations**:
- No direct GraphQL operations needed
- Triggers feed query refresh via filter changes
- Calls `onSaveBoard` which uses Sidebar's mutation

**State Management**:
- Local state for filter inputs
- Passes filters to parent for feed query

**Integration Points**:
- Filter state should trigger feed query
- Search query should be passed to feed query
- Save board action should use GraphQL mutation

---

### 4. FeedItem Component

**File**: `components/FeedItem.tsx`

**Purpose**: Individual media card in the feed grid

**Current Interface**:
```typescript
interface FeedItemProps {
  item: FeedItemType;
}
```

**Current Data Model**:
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

**Required GraphQL Operations**:

**Query** (used by parent FeedView):
```graphql
query GetFeed(
  $cursor: String
  $limit: Int
  $persons: [String!]
  $sources: [String!]
  $searchQuery: String
) {
  feed(
    cursor: $cursor
    limit: $limit
    persons: $persons
    sources: $sources
    searchQuery: $searchQuery
  ) {
    edges {
      node {
        id
        title
        sourceUrl
        publishDate
        imageUrl
        mediaType
        platform
        width
        height
        score
        viewCount
        handle {
          id
          username
          handle
          platform
        }
        author {
          username
        }
        subreddit {
          name
          displayName
        }
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**Required GraphQL Schema Extensions**:
- Extend `feed` query to support `persons: [String!]`, `sources: [String!]`, `searchQuery: String`
- Ensure `Media` type includes all needed fields
- Add `author` field to Media (if not present)
- Add `aspectRatio` calculation field or derive client-side

**State Management**:
- Component is presentational (receives data via props)
- Parent FeedView manages query and state

**Integration Points**:
- Map GraphQL `Media` type to `FeedItem` interface
- Calculate aspect ratio from width/height
- Format timestamps client-side
- Handle different media types (image, video, GIF)

---

### 5. FeedView (App.tsx Feed Section)

**Purpose**: Main feed display with masonry layout

**Required GraphQL Operations**:
- Uses `GetFeed` query (see FeedItem section)
- Supports infinite scroll with cursor pagination

**State Management**:
- Apollo Client `useQuery` with `fetchMore` for pagination
- Local state for loading indicators
- Filter state (can be in URL params or local state)

**Integration Points**:
- Replace `generateFeedItems` service with GraphQL query
- Implement cursor-based pagination
- Handle filter changes (refetch on filter change)
- Map GraphQL response to component props

---

### 6. Theme System

**Current Implementation**: CSS variables in `index.html`

**Required Changes**:
- Extract CSS variables to theme configuration file
- Integrate with existing Bunny theme system (if any)
- Keep CSS variable approach (compatible with most systems)

**Integration Points**:
- Can remain client-side (UI preference)
- Optionally sync theme preference via GraphQL user preferences mutation

---

## Component Dependency Graph

```
App.tsx
├── Sidebar (navigation, boards, filters)
│   └── Uses: GetSavedBoards, GetCreatorsForFilter, CreateSavedBoard, DeleteSavedBoard
├── FilterBar (search, active filters)
│   └── Uses: No direct GraphQL (triggers feed query)
└── FeedView / EntityManager (conditional)
    ├── FeedView
    │   ├── FeedItem[] (grid of cards)
    │   └── Uses: GetFeed query
    └── EntityManager
        └── Uses: GetCreators, GetCreator, CreateCreator, UpdateCreator, DeleteCreator, Handle mutations, Relationship mutations
```

## Data Flow

### Entity Management Flow
1. User opens EntityManager view
2. `GetCreators` query fetches all creators
3. User selects creator → `GetCreator` query fetches details
4. User edits → `UpdateCreator` mutation
5. User adds handle → `AddHandle` mutation
6. Apollo cache updates → UI re-renders

### Feed Display Flow
1. User applies filters (persons, sources, search)
2. Filters trigger `GetFeed` query with parameters
3. GraphQL resolver queries Neo4j with filters
4. Results returned as `FeedConnection`
5. FeedView renders `FeedItem[]` components
6. User scrolls → `fetchMore` loads next page

### Board Management Flow
1. User applies filters
2. User clicks "Save Board" → `CreateSavedBoard` mutation
3. Board saved to Neo4j
4. Sidebar `GetSavedBoards` query fetches updated list
5. User selects board → filters applied → feed query triggered

## Migration Checklist

### Schema Extensions Required
- [ ] Add `aliases` to Creator type
- [ ] Add `contextKeywords` to Creator type
- [ ] Add `relationships` to Creator type
- [ ] Add `label` to Handle type
- [ ] Add `hidden` to Handle type
- [ ] Add `Relationship` type
- [ ] Add `SavedBoard` type
- [ ] Add `FilterInput` input type
- [ ] Extend `feed` query with filter parameters

### Mutations Required
- [ ] `updateCreator`
- [ ] `deleteCreator`
- [ ] `updateHandleVisibility`
- [ ] `addRelationship`
- [ ] `removeRelationship`
- [ ] `createSavedBoard`
- [ ] `deleteSavedBoard`

### Components to Port
- [ ] EntityManager → GraphQL queries/mutations
- [ ] Sidebar → GraphQL for boards, local state for filters
- [ ] FilterBar → No changes (triggers queries)
- [ ] FeedItem → Map GraphQL Media type
- [ ] FeedView → GraphQL feed query
- [ ] App.tsx → Integrate with GraphQL

### Services to Replace
- [ ] `contentGraph.ts` → GraphQL queries
- [ ] `geminiService.ts` → Backend AI service (optional)
- [ ] `fixtures.ts` → Remove (use real data)





