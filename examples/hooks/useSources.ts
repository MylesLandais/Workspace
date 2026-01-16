/**
 * useSources - Source management hook with CRUD operations
 *
 * Manages content sources (subreddits, YouTube channels, RSS feeds, etc.)
 * that determine what content appears in your feed.
 */

import useSWR from 'swr';

const GRAPHQL_API =
  import.meta.env.VITE_GRAPHQL_API || 'http://localhost:4002/api/graphql';

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

export type ActivityFilter = 'ALL' | 'ACTIVE' | 'INACTIVE' | 'PAUSED';

export interface SourceFiltersInput {
  groupId?: string;
  sourceType?: Platform;
  activity?: ActivityFilter;
  searchQuery?: string;
}

export interface Source {
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

export interface CreateSourceInput {
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

export interface UpdateSourceInput {
  name?: string;
  description?: string;
  groupId?: string;
  isPaused?: boolean;
  isEnabled?: boolean;
}

export interface ImportResult {
  imported: number;
  skipped: number;
  failed: number;
  sources: Source[];
  errors: string[];
}

export interface SubredditResult {
  name: string;
  displayName: string;
  subscriberCount: number;
  description: string;
  iconUrl?: string;
  isSubscribed: boolean;
}

// GraphQL Queries
const SOURCES_QUERY = `
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
`;

const CREATE_SOURCE_MUTATION = `
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
`;

const UPDATE_SOURCE_MUTATION = `
  mutation UpdateSource($id: ID!, $input: UpdateSourceInput!) {
    updateSource(id: $id, input: $input) {
      id
      name
      isPaused
      isEnabled
    }
  }
`;

const DELETE_SOURCE_MUTATION = `
  mutation DeleteSource($id: ID!) {
    deleteSource(id: $id)
  }
`;

const BULK_DELETE_MUTATION = `
  mutation BulkDeleteSources($ids: [ID!]!) {
    bulkDeleteSources(ids: $ids)
  }
`;

const TOGGLE_PAUSE_MUTATION = `
  mutation ToggleSourcePause($id: ID!) {
    toggleSourcePause(id: $id) {
      id
      isPaused
    }
  }
`;

const IMPORT_OPML_MUTATION = `
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
`;

const SUBSCRIBE_SUBREDDIT_MUTATION = `
  mutation SubscribeToSource($subredditName: String!, $groupId: String) {
    subscribeToSource(subredditName: $subredditName, groupId: $groupId) {
      id
      name
      subredditName
    }
  }
`;

const SEARCH_SUBREDDITS_QUERY = `
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
`;

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

interface SourcesResponse {
  getUserSources: Source[];
}

export interface UseSourcesOptions {
  filters?: SourceFiltersInput;
  enabled?: boolean;
}

export interface UseSourcesReturn {
  sources: Source[];
  error: Error | undefined;
  isLoading: boolean;
  createSource: (input: CreateSourceInput) => Promise<Source>;
  updateSource: (id: string, input: UpdateSourceInput) => Promise<Source>;
  deleteSource: (id: string) => Promise<boolean>;
  bulkDelete: (ids: string[]) => Promise<number>;
  togglePause: (id: string) => Promise<Source>;
  importOPML: (feedUrls: string[], groupId?: string) => Promise<ImportResult>;
  subscribeSubreddit: (name: string, groupId?: string) => Promise<Source>;
  refresh: () => Promise<void>;
}

/**
 * Hook for managing content sources
 *
 * @example
 * ```tsx
 * const { sources, createSource, deleteSource, togglePause } = useSources();
 *
 * // Add a subreddit
 * await createSource({
 *   name: 'r/unixporn',
 *   sourceType: 'REDDIT',
 *   subredditName: 'unixporn'
 * });
 *
 * // Pause a source
 * await togglePause(source.id);
 *
 * // Delete a source
 * await deleteSource(source.id);
 * ```
 */
export function useSources({
  filters,
  enabled = true,
}: UseSourcesOptions = {}): UseSourcesReturn {
  const { data, error, isLoading, mutate } = useSWR<SourcesResponse>(
    enabled ? ['sources', JSON.stringify(filters)] : null,
    async ([, filtersJson]) => {
      const parsedFilters = filtersJson
        ? (JSON.parse(filtersJson as string) as SourceFiltersInput)
        : undefined;
      return gqlFetcher<SourcesResponse>(SOURCES_QUERY, { filters: parsedFilters });
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  const createSource = async (input: CreateSourceInput): Promise<Source> => {
    const result = await gqlFetcher<{ createSource: Source }>(
      CREATE_SOURCE_MUTATION,
      { input }
    );
    await mutate();
    return result.createSource;
  };

  const updateSource = async (
    id: string,
    input: UpdateSourceInput
  ): Promise<Source> => {
    const result = await gqlFetcher<{ updateSource: Source }>(
      UPDATE_SOURCE_MUTATION,
      { id, input }
    );
    await mutate();
    return result.updateSource;
  };

  const deleteSource = async (id: string): Promise<boolean> => {
    const result = await gqlFetcher<{ deleteSource: boolean }>(
      DELETE_SOURCE_MUTATION,
      { id }
    );
    await mutate();
    return result.deleteSource;
  };

  const bulkDelete = async (ids: string[]): Promise<number> => {
    const result = await gqlFetcher<{ bulkDeleteSources: number }>(
      BULK_DELETE_MUTATION,
      { ids }
    );
    await mutate();
    return result.bulkDeleteSources;
  };

  const togglePause = async (id: string): Promise<Source> => {
    const result = await gqlFetcher<{ toggleSourcePause: Source }>(
      TOGGLE_PAUSE_MUTATION,
      { id }
    );
    await mutate();
    return result.toggleSourcePause;
  };

  const importOPML = async (
    feedUrls: string[],
    groupId?: string
  ): Promise<ImportResult> => {
    const result = await gqlFetcher<{ importOPML: ImportResult }>(
      IMPORT_OPML_MUTATION,
      { feedUrls, groupId }
    );
    await mutate();
    return result.importOPML;
  };

  const subscribeSubreddit = async (
    subredditName: string,
    groupId?: string
  ): Promise<Source> => {
    const result = await gqlFetcher<{ subscribeToSource: Source }>(
      SUBSCRIBE_SUBREDDIT_MUTATION,
      { subredditName, groupId }
    );
    await mutate();
    return result.subscribeToSource;
  };

  return {
    sources: data?.getUserSources || [],
    error,
    isLoading,
    createSource,
    updateSource,
    deleteSource,
    bulkDelete,
    togglePause,
    importOPML,
    subscribeSubreddit,
    refresh: async () => {
      await mutate();
    },
  };
}

/**
 * Hook for searching subreddits
 */
export function useSubredditSearch(query: string) {
  const { data, error, isLoading } = useSWR<{ searchSubreddits: SubredditResult[] }>(
    query.length >= 2 ? ['searchSubreddits', query] : null,
    async ([, q]) => gqlFetcher(SEARCH_SUBREDDITS_QUERY, { query: q }),
    {
      revalidateOnFocus: false,
      dedupingInterval: 1000,
    }
  );

  return {
    results: data?.searchSubreddits || [],
    error,
    isLoading,
  };
}

/**
 * Get platform display name
 */
export function getPlatformLabel(platform: Platform): string {
  const labels: Record<Platform, string> = {
    RSS: 'RSS Feed',
    REDDIT: 'Reddit',
    YOUTUBE: 'YouTube',
    TWITTER: 'Twitter/X',
    INSTAGRAM: 'Instagram',
    TIKTOK: 'TikTok',
    VSCO: 'VSCO',
    IMAGEBOARD: 'Imageboard',
  };
  return labels[platform] || platform;
}

/**
 * Get source handle display string
 */
export function getSourceHandle(source: Source): string {
  switch (source.sourceType) {
    case 'REDDIT':
      return source.subredditName ? `r/${source.subredditName}` : source.name;
    case 'YOUTUBE':
      return source.youtubeHandle || source.name;
    case 'TWITTER':
      return source.twitterHandle ? `@${source.twitterHandle}` : source.name;
    case 'INSTAGRAM':
      return source.instagramHandle ? `@${source.instagramHandle}` : source.name;
    case 'TIKTOK':
      return source.tiktokHandle ? `@${source.tiktokHandle}` : source.name;
    case 'RSS':
      return source.rssUrl || source.name;
    default:
      return source.name;
  }
}

/**
 * Get health status color class
 */
export function getHealthColor(health: string): string {
  switch (health.toLowerCase()) {
    case 'healthy':
    case 'good':
      return 'text-green-500';
    case 'warning':
    case 'degraded':
      return 'text-yellow-500';
    case 'error':
    case 'unhealthy':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}
