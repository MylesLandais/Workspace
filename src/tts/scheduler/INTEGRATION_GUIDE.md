# Bunny Data Integration Guide

This guide explains how to integrate your client application with the Bunny backend to power dynamic web app views with scraped content from Reddit, YouTube, RSS, and other platforms.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [GraphQL API](#graphql-api)
- [Feed Queries](#feed-queries)
- [Source Management](#source-management)
- [Image Handling](#image-handling)
- [SavedBoards (Filter Presets)](#savedboards-filter-presets)
- [TypeScript Types](#typescript-types)
- [React Integration](#react-integration)

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Web Client     │────▶│  Bunny GraphQL   │────▶│   Neo4j     │
│  (React/Vite)   │     │  API (4002)      │     │  (Graph DB) │
└─────────────────┘     └──────────────────┘     └─────────────┘
                               │                       │
                               ▼                       ▼
                        ┌──────────────┐        ┌─────────────┐
                        │ Valkey/Redis │        │  MinIO/S3   │
                        │ (Cache)      │        │  (Images)   │
                        └──────────────┘        └─────────────┘
```

**Data Flow:**
1. **Sources** define what content to track (subreddits, YouTube channels, RSS feeds)
2. **Crawlers** fetch content and store in Neo4j as Media nodes with relationships
3. **Feed API** returns paginated media with presigned image URLs
4. **Client** displays content in gallery/feed views

**Supported Platforms:**
- Reddit (subreddits)
- YouTube (channels)
- Twitter/X
- Instagram
- TikTok
- VSCO
- Imageboard (4chan-style)
- RSS/Atom feeds

## Quick Start

### 1. Environment Setup

```bash
# .env or .env.local
VITE_GRAPHQL_API=http://localhost:4002/api/graphql
```

### 2. Install Dependencies

```bash
bun add swr graphql-request
```

### 3. Basic Feed Fetch

```typescript
import useSWR from 'swr';

const GRAPHQL_API = import.meta.env.VITE_GRAPHQL_API;

const fetcher = (query: string, variables?: Record<string, any>) =>
  fetch(GRAPHQL_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
  }).then(res => res.json()).then(json => json.data);

// Usage in component
const { data } = useSWR([FEED_QUERY, { limit: 20 }], ([q, v]) => fetcher(q, v));
```

## GraphQL API

### Endpoint

```
POST http://localhost:4002/api/graphql
Content-Type: application/json
```

### Playground

Visit `http://localhost:4002/api/graphql` in browser for GraphQL Playground with schema docs.

## Feed Queries

The feed is the primary view - a paginated stream of media items from your subscribed sources.

### Basic Feed Query

```graphql
query Feed($cursor: String, $limit: Int, $filters: FeedFilters) {
  feed(cursor: $cursor, limit: $limit, filters: $filters) {
    edges {
      cursor
      node {
        id
        title
        sourceUrl
        publishDate
        imageUrl
        presignedUrl
        urlExpiresAt
        mediaType
        platform
        width
        height
        score
        handle {
          name
          handle
          creatorName
        }
        subreddit {
          name
        }
        author {
          username
        }
        sha256
        mimeType
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### Filter Types

```graphql
input FeedFilters {
  persons: [String!]!    # Filter by creator/entity names
  sources: [String!]!    # Filter by source names (e.g., "r/unixporn", "reddit")
  tags: [String!]!       # Filter by content tags
  searchQuery: String!   # Full-text search in titles
  categories: [String!]! # Filter by media type: "IMAGE", "VIDEO", "GIF"
}
```

### Filter Examples

**By Subreddit:**
```typescript
const filters = {
  persons: [],
  sources: ['r/unixporn', 'r/mechanicalkeyboards'],
  tags: [],
  searchQuery: '',
  categories: []
};
```

**By Media Type:**
```typescript
const filters = {
  persons: [],
  sources: [],
  tags: [],
  searchQuery: '',
  categories: ['VIDEO'] // Only videos
};
```

**Search:**
```typescript
const filters = {
  persons: [],
  sources: [],
  tags: [],
  searchQuery: 'hyprland',
  categories: []
};
```

### Cursor Pagination

The feed uses cursor-based pagination for infinite scroll:

```typescript
// Initial load
const { data: page1 } = await fetcher(FEED_QUERY, { limit: 20, filters });

// Load more
const { data: page2 } = await fetcher(FEED_QUERY, {
  cursor: page1.feed.pageInfo.endCursor,
  limit: 20,
  filters
});
```

### Media Node Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID | Unique media identifier |
| `title` | String | Post/video title |
| `sourceUrl` | String | Original URL (Reddit post, YouTube video) |
| `publishDate` | DateTime | When content was published |
| `imageUrl` | String | Original image URL |
| `presignedUrl` | String | Cached image with signed URL |
| `urlExpiresAt` | DateTime | When presigned URL expires |
| `mediaType` | MediaType | IMAGE, VIDEO, or TEXT |
| `platform` | Platform | REDDIT, YOUTUBE, RSS, etc. |
| `width` | Int | Image width in pixels |
| `height` | Int | Image height in pixels |
| `score` | Int | Upvotes/likes |
| `handle` | HandleInfo | Source handle info |
| `subreddit` | Subreddit | Reddit subreddit (if applicable) |
| `author` | User | Content author |
| `sha256` | String | Image hash for deduplication |
| `mimeType` | String | MIME type (image/jpeg, video/mp4) |

## Source Management

Sources are the foundation of your feed - they define what content gets crawled and displayed.

### List Sources

```graphql
query GetUserSources($filters: SourceFiltersInput) {
  getUserSources(filters: $filters) {
    id
    name
    sourceType
    subredditName
    youtubeHandle
    twitterHandle
    instagramHandle
    tiktokHandle
    url
    rssUrl
    iconUrl
    description
    entityId
    entityName
    group
    groupId
    tags
    isPaused
    isEnabled
    isActive
    lastSynced
    mediaCount
    storiesPerMonth
    readsPerMonth
    health
  }
}
```

### Source Filters

```graphql
input SourceFiltersInput {
  groupId: String        # Filter by feed group
  sourceType: Platform   # REDDIT, YOUTUBE, RSS, etc.
  activity: ActivityFilter # ALL, ACTIVE, INACTIVE, PAUSED
  searchQuery: String    # Search source names
}

enum ActivityFilter {
  ALL
  ACTIVE
  INACTIVE
  PAUSED
}
```

### Create Source

```graphql
mutation CreateSource($input: CreateSourceInput!) {
  createSource(input: $input) {
    id
    name
    sourceType
    subredditName
    youtubeHandle
    isPaused
    isEnabled
  }
}
```

**Variables:**
```json
{
  "input": {
    "name": "r/unixporn",
    "sourceType": "REDDIT",
    "subredditName": "unixporn",
    "groupId": "default"
  }
}
```

### Update Source

```graphql
mutation UpdateSource($id: ID!, $input: UpdateSourceInput!) {
  updateSource(id: $id, input: $input) {
    id
    name
    isPaused
    isEnabled
  }
}
```

### Delete Source

```graphql
mutation DeleteSource($id: ID!) {
  deleteSource(id: $id)
}
```

### Bulk Delete

```graphql
mutation BulkDeleteSources($ids: [ID!]!) {
  bulkDeleteSources(ids: $ids)
}
```

### Toggle Pause

```graphql
mutation ToggleSourcePause($id: ID!) {
  toggleSourcePause(id: $id) {
    id
    isPaused
  }
}
```

### Import OPML (Bulk RSS)

```graphql
mutation ImportOPML($feedUrls: [String!]!, $groupId: String) {
  importOPML(feedUrls: $feedUrls, groupId: $groupId) {
    imported
    skipped
    failed
    sources {
      id
      name
      rssUrl
    }
    errors
  }
}
```

### Subscribe to Subreddit

```graphql
mutation SubscribeToSource($subredditName: String!, $groupId: String) {
  subscribeToSource(subredditName: $subredditName, groupId: $groupId) {
    id
    name
    subredditName
  }
}
```

### Search Subreddits

```graphql
query SearchSubreddits($query: String!) {
  searchSubreddits(query: $query) {
    name
    displayName
    subscriberCount
    description
    iconUrl
    isSubscribed
  }
}
```

### Feed Groups

```graphql
query GetFeedGroups {
  getFeedGroups {
    id
    name
    createdAt
  }
}

mutation CreateFeedGroup($name: String!) {
  createFeedGroup(name: $name) {
    id
    name
  }
}
```

## Image Handling

### Presigned URLs

Images are cached in MinIO/S3 with presigned URLs that expire after 4 hours. The backend caches URLs in Valkey for 3.5 hours.

**Using presignedUrl:**
```tsx
function FeedItem({ item }) {
  // Prefer presignedUrl (cached), fall back to imageUrl (original)
  const imgSrc = item.presignedUrl || item.imageUrl;

  return <img src={imgSrc} alt={item.title} />;
}
```

**Handling Expiration:**
```typescript
function isUrlExpired(urlExpiresAt: string | null): boolean {
  if (!urlExpiresAt) return false;
  return new Date(urlExpiresAt) < new Date();
}

// In component
const imgSrc = isUrlExpired(item.urlExpiresAt)
  ? item.imageUrl  // Fallback to original
  : item.presignedUrl;
```

### Image Dimensions

Use `width` and `height` for proper aspect ratio in layouts:

```tsx
function FeedItem({ item }) {
  const aspectRatio = item.width && item.height
    ? item.width / item.height
    : 16/9; // default

  return (
    <div style={{ aspectRatio }}>
      <img src={item.presignedUrl || item.imageUrl} />
    </div>
  );
}
```

### Media Types

```typescript
enum MediaType {
  IMAGE = 'IMAGE',
  VIDEO = 'VIDEO',
  TEXT = 'TEXT'
}

// Filter by type
const isVideo = item.mediaType === 'VIDEO' || item.mimeType?.startsWith('video/');
const isGif = item.mimeType === 'image/gif';
```

### Duplicate Detection

Media includes hash fields for duplicate awareness:

```typescript
interface Media {
  sha256: string;  // Exact duplicate detection
  // phash, dhash available via cluster queries
}
```

## SavedBoards (Filter Presets)

SavedBoards let users save filter configurations for quick access.

### Get SavedBoards

```graphql
query GetSavedBoards($userId: ID!) {
  getSavedBoards(userId: $userId) {
    id
    name
    filters {
      persons
      sources
      tags
      searchQuery
    }
    createdAt
    userId
  }
}
```

### Create SavedBoard

```graphql
mutation CreateSavedBoard($userId: ID!, $input: SavedBoardInput!) {
  createSavedBoard(userId: $userId, input: $input) {
    id
    name
    filters {
      persons
      sources
      tags
      searchQuery
    }
  }
}
```

**Variables:**
```json
{
  "userId": "user-123",
  "input": {
    "name": "Linux Ricing",
    "filters": {
      "persons": [],
      "sources": ["r/unixporn", "r/archlinux"],
      "tags": [],
      "searchQuery": "",
      "categories": ["IMAGE"]
    }
  }
}
```

### Update SavedBoard

```graphql
mutation UpdateSavedBoard($id: ID!, $input: SavedBoardInput!) {
  updateSavedBoard(id: $id, input: $input) {
    id
    name
    filters { ... }
  }
}
```

### Delete SavedBoard

```graphql
mutation DeleteSavedBoard($id: ID!) {
  deleteSavedBoard(id: $id)
}
```

## TypeScript Types

```typescript
// Platform types
type Platform =
  | 'RSS'
  | 'REDDIT'
  | 'YOUTUBE'
  | 'TWITTER'
  | 'INSTAGRAM'
  | 'TIKTOK'
  | 'VSCO'
  | 'IMAGEBOARD';

type MediaType = 'IMAGE' | 'VIDEO' | 'TEXT';

type ActivityFilter = 'ALL' | 'ACTIVE' | 'INACTIVE' | 'PAUSED';

// Feed types
interface FeedFilters {
  persons: string[];
  sources: string[];
  tags: string[];
  searchQuery: string;
  categories: string[];
}

interface HandleInfo {
  name: string;
  handle: string;
  creatorName?: string;
}

interface Media {
  id: string;
  title: string;
  sourceUrl: string;
  publishDate: string;
  imageUrl: string;
  presignedUrl?: string;
  urlExpiresAt?: string;
  mediaType: MediaType;
  platform: Platform;
  width?: number;
  height?: number;
  score?: number;
  handle: HandleInfo;
  subreddit?: { name: string };
  author?: { username: string };
  sha256?: string;
  mimeType?: string;
}

interface FeedEdge {
  cursor: string;
  node: Media;
}

interface PageInfo {
  hasNextPage: boolean;
  endCursor?: string;
}

interface FeedConnection {
  edges: FeedEdge[];
  pageInfo: PageInfo;
}

// Source types
interface SourceFiltersInput {
  groupId?: string;
  sourceType?: Platform;
  activity?: ActivityFilter;
  searchQuery?: string;
}

interface Source {
  id: string;
  name: string;
  sourceType: Platform;
  subredditName?: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  url?: string;
  rssUrl?: string;
  iconUrl?: string;
  description?: string;
  entityId?: string;
  entityName?: string;
  group: string;
  groupId?: string;
  tags: string[];
  isPaused: boolean;
  isEnabled: boolean;
  isActive: boolean;
  lastSynced?: string;
  mediaCount: number;
  storiesPerMonth: number;
  readsPerMonth: number;
  health: string;
}

interface CreateSourceInput {
  name: string;
  sourceType: Platform;
  url?: string;
  subredditName?: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  groupId?: string;
  description?: string;
}

interface UpdateSourceInput {
  name?: string;
  description?: string;
  groupId?: string;
  isPaused?: boolean;
  isEnabled?: boolean;
}

// SavedBoard types
interface FilterState {
  persons: string[];
  sources: string[];
  tags: string[];
  searchQuery: string;
}

interface SavedBoard {
  id: string;
  name: string;
  filters: FilterState;
  createdAt: string;
  userId: string;
}

interface SavedBoardInput {
  name: string;
  filters: FeedFilters;
}

// Feed Group types
interface FeedGroup {
  id: string;
  name: string;
  createdAt: string;
}
```

## React Integration

### SWR Setup

```typescript
// lib/graphql.ts
const GRAPHQL_API = import.meta.env.VITE_GRAPHQL_API || 'http://localhost:4002/api/graphql';

export async function gqlFetcher<T>(
  query: string,
  variables?: Record<string, any>
): Promise<T> {
  const response = await fetch(GRAPHQL_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
  });

  const json = await response.json();

  if (json.errors) {
    throw new Error(json.errors[0]?.message || 'GraphQL Error');
  }

  return json.data;
}
```

### useFeed Hook

```typescript
// hooks/useFeed.ts
import useSWRInfinite from 'swr/infinite';
import { gqlFetcher } from '../lib/graphql';

const FEED_QUERY = `
  query Feed($cursor: String, $limit: Int, $filters: FeedFilters) {
    feed(cursor: $cursor, limit: $limit, filters: $filters) {
      edges { cursor node { id title presignedUrl imageUrl width height score mediaType platform handle { name handle } } }
      pageInfo { hasNextPage endCursor }
    }
  }
`;

interface UseFeedOptions {
  filters?: FeedFilters;
  limit?: number;
}

export function useFeed({ filters, limit = 20 }: UseFeedOptions = {}) {
  const getKey = (pageIndex: number, previousPageData: any) => {
    if (previousPageData && !previousPageData.feed.pageInfo.hasNextPage) {
      return null; // End reached
    }

    const cursor = previousPageData?.feed.pageInfo.endCursor || null;
    return [FEED_QUERY, { cursor, limit, filters }];
  };

  const { data, error, isLoading, isValidating, size, setSize, mutate } =
    useSWRInfinite(
      getKey,
      ([query, variables]) => gqlFetcher(query, variables),
      { revalidateFirstPage: false }
    );

  const items = data?.flatMap(page => page.feed.edges.map(e => e.node)) || [];
  const hasMore = data?.[data.length - 1]?.feed.pageInfo.hasNextPage ?? true;

  return {
    items,
    error,
    isLoading,
    isLoadingMore: isValidating && size > 1,
    hasMore,
    loadMore: () => setSize(size + 1),
    refresh: () => mutate(),
  };
}
```

### useSources Hook

```typescript
// hooks/useSources.ts
import useSWR from 'swr';
import { gqlFetcher } from '../lib/graphql';

const SOURCES_QUERY = `
  query GetUserSources($filters: SourceFiltersInput) {
    getUserSources(filters: $filters) {
      id name sourceType subredditName youtubeHandle iconUrl
      isPaused isActive mediaCount lastSynced health
    }
  }
`;

const CREATE_SOURCE = `
  mutation CreateSource($input: CreateSourceInput!) {
    createSource(input: $input) { id name sourceType }
  }
`;

const DELETE_SOURCE = `
  mutation DeleteSource($id: ID!) { deleteSource(id: $id) }
`;

const TOGGLE_PAUSE = `
  mutation ToggleSourcePause($id: ID!) {
    toggleSourcePause(id: $id) { id isPaused }
  }
`;

export function useSources(filters?: SourceFiltersInput) {
  const { data, error, isLoading, mutate } = useSWR(
    [SOURCES_QUERY, { filters }],
    ([query, variables]) => gqlFetcher(query, variables)
  );

  const createSource = async (input: CreateSourceInput) => {
    const result = await gqlFetcher(CREATE_SOURCE, { input });
    mutate(); // Refresh list
    return result;
  };

  const deleteSource = async (id: string) => {
    await gqlFetcher(DELETE_SOURCE, { id });
    mutate();
  };

  const togglePause = async (id: string) => {
    const result = await gqlFetcher(TOGGLE_PAUSE, { id });
    mutate();
    return result;
  };

  return {
    sources: data?.getUserSources || [],
    error,
    isLoading,
    createSource,
    deleteSource,
    togglePause,
    refresh: () => mutate(),
  };
}
```

### FeedGrid Component

```tsx
// components/FeedGrid.tsx
import { useFeed } from '../hooks/useFeed';

interface FeedGridProps {
  filters?: FeedFilters;
}

export function FeedGrid({ filters }: FeedGridProps) {
  const { items, isLoading, hasMore, loadMore, isLoadingMore } = useFeed({ filters });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {items.map(item => (
        <FeedItem key={item.id} item={item} />
      ))}

      {hasMore && (
        <button
          onClick={loadMore}
          disabled={isLoadingMore}
          className="col-span-full"
        >
          {isLoadingMore ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}

function FeedItem({ item }: { item: Media }) {
  const imgSrc = item.presignedUrl || item.imageUrl;
  const aspectRatio = item.width && item.height ? item.width / item.height : 1;

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div style={{ aspectRatio }} className="bg-gray-900">
        <img
          src={imgSrc}
          alt={item.title}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>
      <div className="p-3">
        <h3 className="text-sm font-medium text-white line-clamp-2">
          {item.title}
        </h3>
        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>{item.handle.handle}</span>
          <span>⬆️ {item.score}</span>
        </div>
      </div>
    </div>
  );
}
```

### SourceList Component

```tsx
// components/SourceList.tsx
import { useSources } from '../hooks/useSources';

export function SourceList() {
  const { sources, isLoading, togglePause, deleteSource } = useSources();

  if (isLoading) return <div>Loading sources...</div>;

  return (
    <table className="w-full">
      <thead>
        <tr className="text-left text-gray-400">
          <th>Name</th>
          <th>Type</th>
          <th>Media</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {sources.map(source => (
          <tr key={source.id} className="border-b border-gray-700">
            <td className="py-2">
              {source.iconUrl && <img src={source.iconUrl} className="w-6 h-6 inline mr-2" />}
              {source.name}
            </td>
            <td>{source.sourceType}</td>
            <td>{source.mediaCount}</td>
            <td>
              <span className={source.isPaused ? 'text-yellow-500' : 'text-green-500'}>
                {source.isPaused ? 'Paused' : 'Active'}
              </span>
            </td>
            <td className="space-x-2">
              <button onClick={() => togglePause(source.id)}>
                {source.isPaused ? 'Resume' : 'Pause'}
              </button>
              <button onClick={() => deleteSource(source.id)} className="text-red-500">
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## Troubleshooting

### CORS Issues

If you get CORS errors, ensure the Bunny server has CORS enabled for your client origin:

```typescript
// Bunny server should have
app.use(cors({ origin: 'http://localhost:5173' }));
```

### Connection Refused

Ensure Bunny server is running:
```bash
cd ~/Workspace/Bunny/app/server && bun run dev
```

### Empty Feed

1. Check if sources exist: Query `getUserSources`
2. Check if media was crawled: Look at Neo4j for Media nodes
3. Verify filters aren't too restrictive

### Presigned URL Expired

If images fail to load, the presigned URL may have expired. Refresh the feed to get new URLs:

```typescript
const { refresh } = useFeed();
// Call refresh() to get fresh presigned URLs
```

## Support

- GraphQL Playground: `http://localhost:4002/api/graphql`
- Neo4j Browser: `http://localhost:7474`
- Check logs: `docker compose logs server`
