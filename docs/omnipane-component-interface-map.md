# OmniPane Component Interface Map

This document maps OmniPane Reader components to GraphQL operations and data requirements for integration with Bunny's backend.

## Component Overview

### App.tsx (Main Container)

**Current Props**: None (top-level component)

**Current State Management**:
- Local React state for articles, boards, view modes
- Local filtering logic

**GraphQL Operations Needed**:

#### Queries
```graphql
query GetArticles($filters: ArticleFilters, $cursor: String, $limit: Int) {
  articles(filters: $filters, cursor: $cursor, limit: $limit) {
    edges {
      node {
        id
        title
        author
        content
        summary
        publishedAt
        read
        saved
        archived
        tags
        type
        url
        imageUrl
        imageWidth
        imageHeight
        sauce {
          similarity
          sourceUrl
          artistName
          extUrl
        }
        source {
          id
          name
          type
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

query GetBoards {
  boards {
    id
    name
    articleIds
    articleCount
  }
}

query GetSources {
  sources {
    id
    name
    type
    unreadCount
  }
}

query GetTags {
  tags {
    name
    count
  }
}
```

#### Mutations
```graphql
mutation ToggleArticleRead($articleId: ID!) {
  toggleArticleRead(articleId: $articleId) {
    id
    read
  }
}

mutation ToggleArticleSaved($articleId: ID!) {
  toggleArticleSaved(articleId: $articleId) {
    id
    saved
  }
}

mutation ToggleArticleArchived($articleId: ID!) {
  toggleArticleArchived(articleId: $articleId) {
    id
    archived
  }
}

mutation PinArticleToBoard($articleId: ID!, $boardId: ID!) {
  pinArticleToBoard(articleId: $articleId, boardId: $boardId) {
    id
    articleIds
  }
}

mutation CreateBoard($name: String!) {
  createBoard(name: $name) {
    id
    name
  }
}

mutation DeleteBoard($boardId: ID!) {
  deleteBoard(boardId: $boardId)
}

mutation GenerateArticleSummary($articleId: ID!) {
  generateArticleSummary(articleId: $articleId) {
    id
    summary
    keyTakeaways
  }
}

mutation FindImageSauce($articleId: ID!) {
  findImageSauce(articleId: $articleId) {
    id
    sauce {
      similarity
      sourceUrl
      artistName
      extUrl
    }
  }
}

mutation ChatWithArticle($articleId: ID!, $question: String!) {
  chatWithArticle(articleId: $articleId, question: $question) {
    response
  }
}
```

**Input Types Needed**:
```graphql
input ArticleFilters {
  viewMode: ViewMode
  sourceId: ID
  tag: String
  boardId: ID
  saved: Boolean
  archived: Boolean
  read: Boolean
}

enum ViewMode {
  INBOX
  LATER
  ARCHIVE
  FEED
  TAG
  BOARD
}
```

---

### Sidebar.tsx

**Current Props**:
```typescript
interface SidebarProps {
  feeds: FeedSource[];
  boards: Board[];
  activeView: ViewMode;
  onViewChange: (view: ViewMode) => void;
  onFeedSelect: (feedId: string | null) => void;
  onTagSelect: (tag: string) => void;
  onBoardSelect: (boardId: string) => void;
  activeFeedId: string | null;
  activeTag: string | null;
  activeBoardId: string | null;
  tags: {name: string, count: number}[];
}
```

**GraphQL Operations Needed**:

#### Queries
```graphql
query GetSidebarData {
  sources {
    id
    name
    type
    icon
    unreadCount
  }
  boards {
    id
    name
    articleCount
  }
  tags {
    name
    count
  }
  inboxCount: articlesCount(filters: { viewMode: INBOX })
  laterCount: articlesCount(filters: { viewMode: LATER })
}
```

**Component Changes**:
- Replace `feeds` prop with GraphQL query result
- Replace `boards` prop with GraphQL query result
- Replace `tags` prop with GraphQL query result
- Keep callback props for navigation (no changes needed)
- Use Apollo Client hooks: `useQuery` for data, props for callbacks

---

### ArticleList.tsx

**Current Props**:
```typescript
interface ArticleListProps {
  articles: Article[];
  activeArticleId: string | null;
  onSelectArticle: (article: Article) => void;
  viewTitle: string;
  layout: LayoutMode;
  onToggleLayout: () => void;
}
```

**GraphQL Operations Needed**:

#### Queries
```graphql
query GetArticlesList($filters: ArticleFilters, $cursor: String, $limit: Int) {
  articles(filters: $filters, cursor: $cursor, limit: $limit) {
    edges {
      node {
        id
        title
        author
        content
        publishedAt
        read
        saved
        tags
        type
        imageUrl
        imageWidth
        imageHeight
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

**Component Changes**:
- Replace `articles` prop with GraphQL query
- Use `useQuery` with filters derived from parent component state
- Implement infinite scroll with `fetchMore` for pagination
- Keep `onSelectArticle` callback (no changes)
- Keep `layout` and `onToggleLayout` (frontend-only state)

**Pagination Strategy**:
- Use cursor-based pagination
- Load more on scroll or "Load More" button
- Use `fetchMore` from Apollo Client

---

### ArticleReader.tsx

**Current Props**:
```typescript
interface ArticleReaderProps {
  article: Article | null;
  boards: Board[];
  onBack?: () => void;
  onToggleSave: (id: string) => void;
  onArchive: (id: string) => void;
  onPinToBoard: (articleId: string, boardId: string) => void;
  onUpdateArticle: (articleId: string, updates: Partial<Article>) => void;
}
```

**GraphQL Operations Needed**:

#### Queries
```graphql
query GetArticleDetail($articleId: ID!) {
  article(id: $articleId) {
    id
    title
    author
    content
    summary
    keyTakeaways
    publishedAt
    read
    saved
    archived
    tags
    type
    url
    imageUrl
    imageWidth
    imageHeight
    sauce {
      similarity
      sourceUrl
      artistName
      extUrl
    }
    source {
      id
      name
      type
    }
  }
  
  boards {
    id
    name
    articleIds
  }
}
```

#### Mutations
```graphql
mutation ToggleArticleSaved($articleId: ID!) {
  toggleArticleSaved(articleId: $articleId) {
    id
    saved
  }
}

mutation ToggleArticleArchived($articleId: ID!) {
  toggleArticleArchived(articleId: $articleId) {
    id
    archived
  }
}

mutation PinArticleToBoard($articleId: ID!, $boardId: ID!) {
  pinArticleToBoard(articleId: $articleId, boardId: $boardId) {
    id
    articleIds
  }
}

mutation GenerateArticleSummary($articleId: ID!) {
  generateArticleSummary(articleId: $articleId) {
    id
    summary
    keyTakeaways
  }
}

mutation FindImageSauce($articleId: ID!) {
  findImageSauce(articleId: $articleId) {
    id
    sauce {
      similarity
      sourceUrl
      artistName
      extUrl
    }
  }
}

mutation ChatWithArticle($articleId: ID!, $question: String!) {
  chatWithArticle(articleId: $articleId, question: $question) {
    response
  }
}
```

**Component Changes**:
- Replace `article` prop with GraphQL query (`useQuery` with `articleId`)
- Replace `boards` prop with GraphQL query
- Replace action callbacks with GraphQL mutations (`useMutation`)
- Use optimistic updates for better UX
- Keep `onBack` callback (no changes, navigation logic)

**State Management**:
- Local state for chat history (not persisted)
- Local state for UI state (activeTab, showBoardMenu, etc.)
- GraphQL for persistent data

---

### InsightsView.tsx

**Current Props**:
```typescript
interface InsightsViewProps {
  articles: Article[];
}
```

**GraphQL Operations Needed**:

#### Queries
```graphql
query GetInsightsData {
  insights {
    totalCount
    readCount
    savedCount
    readRatio
    sourceDistribution {
      type
      count
    }
    topTags(limit: 7) {
      name
      count
    }
  }
}
```

**Component Changes**:
- Replace `articles` prop with GraphQL query
- Use `useQuery` to fetch aggregated insights data
- Backend calculates aggregations (more efficient than client-side)
- Keep Recharts components (no changes)

**Alternative Approach** (if aggregations are complex):
- Fetch all articles and calculate client-side (current approach)
- Use GraphQL query with all articles
- Calculate aggregations in component (useMemo)

**Recommendation**: Backend aggregations for better performance

---

## GraphQL Schema Extensions Required

### Types

```graphql
type Article {
  id: ID!
  title: String!
  author: String!
  content: String!
  summary: String
  keyTakeaways: [String!]
  publishedAt: DateTime!
  read: Boolean!
  saved: Boolean!
  archived: Boolean!
  tags: [String!]!
  type: SourceType!
  url: String!
  imageUrl: String
  imageWidth: Int
  imageHeight: Int
  sauce: SauceResult
  source: FeedSource!
}

type FeedSource {
  id: ID!
  name: String!
  type: SourceType!
  icon: String
  unreadCount: Int!
}

type Board {
  id: ID!
  name: String!
  articleIds: [ID!]!
  articleCount: Int!
  articles: [Article!]!
}

type Tag {
  name: String!
  count: Int!
}

type SauceResult {
  similarity: Float!
  sourceUrl: String!
  artistName: String!
  extUrl: String
}

type Insights {
  totalCount: Int!
  readCount: Int!
  savedCount: Int!
  readRatio: Float!
  sourceDistribution: [SourceDistribution!]!
  topTags: [Tag!]!
}

type SourceDistribution {
  type: SourceType!
  count: Int!
}

enum SourceType {
  RSS
  TWITTER
  NEWSLETTER
  YOUTUBE
  REDDIT
  BOORU
  MONITOR
}

enum ViewMode {
  INBOX
  LATER
  ARCHIVE
  FEED
  TAG
  BOARD
}

input ArticleFilters {
  viewMode: ViewMode
  sourceId: ID
  tag: String
  boardId: ID
  saved: Boolean
  archived: Boolean
  read: Boolean
}

type ArticleConnection {
  edges: [ArticleEdge!]!
  pageInfo: PageInfo!
}

type ArticleEdge {
  node: Article!
  cursor: String!
}
```

### Queries

```graphql
type Query {
  article(id: ID!): Article
  articles(filters: ArticleFilters, cursor: String, limit: Int): ArticleConnection!
  articlesCount(filters: ArticleFilters): Int!
  sources: [FeedSource!]!
  boards: [Board!]!
  board(id: ID!): Board
  tags: [Tag!]!
  insights: Insights!
}
```

### Mutations

```graphql
type Mutation {
  # Article state mutations
  toggleArticleRead(articleId: ID!): Article!
  toggleArticleSaved(articleId: ID!): Article!
  toggleArticleArchived(articleId: ID!): Article!
  
  # Board mutations
  createBoard(name: String!): Board!
  updateBoard(boardId: ID!, name: String): Board!
  deleteBoard(boardId: ID!): Boolean!
  pinArticleToBoard(articleId: ID!, boardId: ID!): Board!
  unpinArticleFromBoard(articleId: ID!, boardId: ID!): Board!
  
  # AI mutations
  generateArticleSummary(articleId: ID!): ArticleSummary!
  chatWithArticle(articleId: ID!, question: String!): ChatResponse!
  
  # SauceNAO mutation
  findImageSauce(articleId: ID!): Article!
}

type ArticleSummary {
  summary: String!
  keyTakeaways: [String!]!
}

type ChatResponse {
  response: String!
}
```

## Data Flow Patterns

### Reading an Article

1. User clicks article in ArticleList
2. ArticleList calls `onSelectArticle(article)`
3. App.tsx updates `activeArticleId` state
4. ArticleReader receives `articleId` prop
5. ArticleReader uses `useQuery(GetArticleDetail, { variables: { articleId } })`
6. Article displays with data from GraphQL
7. User marks as read → `useMutation(ToggleArticleRead)`
8. Optimistic update updates UI immediately
9. Apollo cache updated when mutation completes

### Filtering Articles

1. User selects view mode (inbox, feed, tag, etc.)
2. App.tsx updates filter state
3. ArticleList receives filters via props
4. ArticleList uses `useQuery(GetArticlesList, { variables: { filters } })`
5. Articles filtered on backend
6. Results displayed in list/grid

### Board Management

1. User clicks "Pin to Board" in ArticleReader
2. Board menu displays (fetched via `useQuery(GetBoards)`)
3. User selects board
4. `useMutation(PinArticleToBoard)` called
5. Optimistic update adds article to board
6. Apollo cache updated when mutation completes

### AI Features

1. User clicks "Generate Summary" in ArticleReader
2. `useMutation(GenerateArticleSummary)` called
3. Loading state displayed
4. Backend calls Gemini API
5. Summary returned and stored in database
6. Article updated with summary
7. UI displays summary

## Optimization Strategies

### Caching

- Use Apollo Client cache for articles
- Cache boards, sources, tags (rarely change)
- Invalidate cache on mutations
- Use cache-first policy for reads

### Pagination

- Use cursor-based pagination
- Implement infinite scroll
- Prefetch next page on scroll
- Use `fetchMore` for additional pages

### Optimistic Updates

- Use optimistic updates for all mutations
- Update cache immediately
- Rollback on error
- Better UX than waiting for server response

### Query Batching

- Batch related queries where possible
- Use GraphQL fragments for shared fields
- Minimize over-fetching with precise field selection

## Migration Checklist

- [ ] Define GraphQL schema extensions
- [ ] Implement backend resolvers
- [ ] Port App.tsx to use Apollo Client
- [ ] Port Sidebar.tsx to use GraphQL queries
- [ ] Port ArticleList.tsx to use GraphQL queries with pagination
- [ ] Port ArticleReader.tsx to use GraphQL queries and mutations
- [ ] Port InsightsView.tsx to use GraphQL queries
- [ ] Implement optimistic updates
- [ ] Implement error handling
- [ ] Implement loading states
- [ ] Test all operations
- [ ] Performance testing and optimization

