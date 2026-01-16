/**
 * useFeed - Infinite scroll feed hook with cursor pagination
 *
 * Fetches media items from the Bunny GraphQL API with support for:
 * - Cursor-based pagination for infinite scroll
 * - Filtering by sources, persons, tags, search, and media categories
 * - Automatic deduplication via SWR
 */

import useSWRInfinite from 'swr/infinite';

const GRAPHQL_API =
  import.meta.env.VITE_GRAPHQL_API || 'http://localhost:4002/api/graphql';

// GraphQL query for paginated feed
const FEED_QUERY = `
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
`;

// Types
export type Platform =
  | 'RSS'
  | 'REDDIT'
  | 'YOUTUBE'
  | 'TWITTER'
  | 'INSTAGRAM'
  | 'TIKTOK'
  | 'VSCO'
  | 'IMAGEBOARD';

export type MediaType = 'IMAGE' | 'VIDEO' | 'TEXT';

export interface FeedFilters {
  persons: string[];
  sources: string[];
  tags: string[];
  searchQuery: string;
  categories: string[];
}

export interface HandleInfo {
  name: string;
  handle: string;
  creatorName?: string;
}

export interface Media {
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

export interface FeedEdge {
  cursor: string;
  node: Media;
}

export interface PageInfo {
  hasNextPage: boolean;
  endCursor?: string;
}

export interface FeedConnection {
  edges: FeedEdge[];
  pageInfo: PageInfo;
}

interface FeedResponse {
  feed: FeedConnection;
}

// GraphQL fetcher
async function gqlFetcher<T>(
  query: string,
  variables?: Record<string, unknown>
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

// Default empty filters
const DEFAULT_FILTERS: FeedFilters = {
  persons: [],
  sources: [],
  tags: [],
  searchQuery: '',
  categories: [],
};

export interface UseFeedOptions {
  filters?: Partial<FeedFilters>;
  limit?: number;
  enabled?: boolean;
}

export interface UseFeedReturn {
  items: Media[];
  error: Error | undefined;
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  loadMore: () => void;
  refresh: () => Promise<void>;
  isEmpty: boolean;
}

/**
 * Hook for fetching paginated feed with infinite scroll
 *
 * @example
 * ```tsx
 * const { items, loadMore, hasMore, isLoading } = useFeed({
 *   filters: { sources: ['r/unixporn'] },
 *   limit: 20
 * });
 *
 * return (
 *   <div>
 *     {items.map(item => <FeedItem key={item.id} item={item} />)}
 *     {hasMore && <button onClick={loadMore}>Load More</button>}
 *   </div>
 * );
 * ```
 */
export function useFeed({
  filters,
  limit = 20,
  enabled = true,
}: UseFeedOptions = {}): UseFeedReturn {
  // Merge with default filters
  const mergedFilters: FeedFilters = {
    ...DEFAULT_FILTERS,
    ...filters,
  };

  // Key generator for SWR infinite
  const getKey = (pageIndex: number, previousPageData: FeedResponse | null) => {
    // Return null if disabled
    if (!enabled) return null;

    // End of data
    if (previousPageData && !previousPageData.feed.pageInfo.hasNextPage) {
      return null;
    }

    // Get cursor from previous page
    const cursor = previousPageData?.feed.pageInfo.endCursor || null;

    // Return key array for SWR
    return ['feed', cursor, limit, JSON.stringify(mergedFilters)] as const;
  };

  const { data, error, isLoading, isValidating, size, setSize, mutate } =
    useSWRInfinite<FeedResponse>(
      getKey,
      async ([, cursor, lim, filtersJson]) => {
        const parsedFilters = JSON.parse(filtersJson as string) as FeedFilters;
        return gqlFetcher<FeedResponse>(FEED_QUERY, {
          cursor,
          limit: lim,
          filters: parsedFilters,
        });
      },
      {
        revalidateFirstPage: false,
        revalidateOnFocus: false,
        dedupingInterval: 5000,
      }
    );

  // Flatten all pages into single items array
  const items = data?.flatMap((page) => page.feed.edges.map((e) => e.node)) || [];

  // Check if more pages available
  const hasMore = data?.[data.length - 1]?.feed.pageInfo.hasNextPage ?? true;

  // Is loading more (not initial load)
  const isLoadingMore = isValidating && size > 1;

  // Is empty (finished loading but no items)
  const isEmpty = !isLoading && items.length === 0;

  return {
    items,
    error,
    isLoading,
    isLoadingMore,
    hasMore,
    loadMore: () => setSize(size + 1),
    refresh: async () => {
      await mutate();
    },
    isEmpty,
  };
}

/**
 * Helper to check if presigned URL is expired
 */
export function isUrlExpired(urlExpiresAt: string | null | undefined): boolean {
  if (!urlExpiresAt) return false;
  return new Date(urlExpiresAt) < new Date();
}

/**
 * Get best image URL (presigned if valid, fallback to original)
 */
export function getImageUrl(item: Media): string {
  if (item.presignedUrl && !isUrlExpired(item.urlExpiresAt)) {
    return item.presignedUrl;
  }
  return item.imageUrl;
}

/**
 * Calculate aspect ratio for layout
 */
export function getAspectRatio(item: Media, fallback = 1): number {
  if (item.width && item.height && item.height > 0) {
    return item.width / item.height;
  }
  return fallback;
}
