"use client";

import { useState, useCallback, useEffect } from "react";
import type {
  Source,
  SourceFilters,
  FeedGroup,
  CreateSourceInput,
  ViewMode,
} from "@/lib/types/sources";

const GRAPHQL_ENDPOINT =
  process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT ||
  "http://localhost:4003/api/graphql";

interface UseSourcesReturn {
  sources: Source[];
  feedGroups: FeedGroup[];
  filters: SourceFilters;
  viewMode: ViewMode;
  selectedIds: Set<string>;
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  inactiveCount: number;
  setFilters: (filters: SourceFilters) => void;
  setViewMode: (mode: ViewMode) => void;
  setSelectedIds: (ids: Set<string>) => void;
  selectAll: (selected: boolean) => void;
  selectOne: (id: string, selected: boolean) => void;
  refresh: () => Promise<void>;
}

export function useSources(): UseSourcesReturn {
  const [sources, setSources] = useState<Source[]>([]);
  const [feedGroups, setFeedGroups] = useState<FeedGroup[]>([]);
  const [filters, setFilters] = useState<SourceFilters>({});
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const query = `
        query GetUserSources($filters: SourceFiltersInput) {
          getUserSources(filters: $filters) {
            id
            name
            subredditName
            sourceType
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
          getFeedGroups(userId: ${filters.userId ? `"${filters.userId}"` : "null"}) {
            id
            name
            userId
            createdAt
          }
        }
      `;

      const variables = {
        filters:
          filters.groupId ||
          filters.userId ||
          filters.sourceType ||
          filters.activity ||
          filters.searchQuery
            ? {
                groupId: filters.groupId,
                userId: filters.userId,
                sourceType: filters.sourceType,
                activity: filters.activity?.toUpperCase(),
                searchQuery: filters.searchQuery,
              }
            : null,
      };

      const response = await fetch(GRAPHQL_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query, variables }),
      });

      const result = await response.json();

      if (result.errors) {
        throw new Error(result.errors[0]?.message || "GraphQL error");
      }

      setSources(result.data.getUserSources || []);
      setFeedGroups(result.data.getFeedGroups || []);
    } catch (err) {
      setError((err as Error).message);
      // Return empty arrays on error to allow UI to render
      setSources([]);
      setFeedGroups([]);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const selectAll = useCallback(
    (selected: boolean) => {
      if (selected) {
        setSelectedIds(new Set(sources.map((s) => s.id)));
      } else {
        setSelectedIds(new Set());
      }
    },
    [sources],
  );

  const selectOne = useCallback((id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const totalCount = sources.length;
  const inactiveCount = sources.filter((s) => !s.isActive).length;

  return {
    sources,
    feedGroups,
    filters,
    viewMode,
    selectedIds,
    isLoading,
    error,
    totalCount,
    inactiveCount,
    setFilters,
    setViewMode,
    setSelectedIds,
    selectAll,
    selectOne,
    refresh: fetchSources,
  };
}

interface UseSourceMutationsReturn {
  createSource: (input: CreateSourceInput) => Promise<Source>;
  updateSource: (
    id: string,
    input: Partial<CreateSourceInput>,
  ) => Promise<Source>;
  deleteSource: (id: string) => Promise<boolean>;
  togglePause: (id: string) => Promise<Source>;
  bulkDelete: (ids: string[]) => Promise<number>;
  importOPML: (
    feedUrls: string[],
    groupId?: string,
  ) => Promise<{ imported: number; skipped: number }>;
  isLoading: boolean;
  error: string | null;
}

export function useSourceMutations(): UseSourceMutationsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeMutation = useCallback(
    async <T>(
      mutation: string,
      variables: Record<string, unknown>,
    ): Promise<T> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(GRAPHQL_ENDPOINT, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: mutation, variables }),
        });

        const result = await response.json();

        if (result.errors) {
          throw new Error(result.errors[0]?.message || "GraphQL error");
        }

        return result.data;
      } catch (err) {
        const errorMessage = (err as Error).message;
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const createSource = useCallback(
    async (input: CreateSourceInput & { userId?: string }): Promise<Source> => {
      const mutation = `
      mutation CreateSource($input: CreateSourceInput!) {
        createSource(input: $input) {
          id
          name
          sourceType
          isPaused
          isEnabled
          isActive
          health
        }
      }
    `;

      const result = await executeMutation<{ createSource: Source }>(mutation, {
        input,
      });
      return result.createSource;
    },
    [executeMutation],
  );

  const updateSource = useCallback(
    async (id: string, input: Partial<CreateSourceInput>): Promise<Source> => {
      const mutation = `
      mutation UpdateSource($id: ID!, $input: UpdateSourceInput!) {
        updateSource(id: $id, input: $input) {
          id
          name
          sourceType
          isPaused
          isEnabled
          isActive
          health
        }
      }
    `;

      const result = await executeMutation<{ updateSource: Source }>(mutation, {
        id,
        input,
      });
      return result.updateSource;
    },
    [executeMutation],
  );

  const deleteSource = useCallback(
    async (id: string): Promise<boolean> => {
      const mutation = `
      mutation DeleteSource($id: ID!) {
        deleteSource(id: $id)
      }
    `;

      const result = await executeMutation<{ deleteSource: boolean }>(
        mutation,
        { id },
      );
      return result.deleteSource;
    },
    [executeMutation],
  );

  const togglePause = useCallback(
    async (id: string): Promise<Source> => {
      const mutation = `
      mutation ToggleSourcePause($id: ID!) {
        toggleSourcePause(id: $id) {
          id
          name
          isPaused
          isActive
        }
      }
    `;

      const result = await executeMutation<{ toggleSourcePause: Source }>(
        mutation,
        { id },
      );
      return result.toggleSourcePause;
    },
    [executeMutation],
  );

  const bulkDelete = useCallback(
    async (ids: string[]): Promise<number> => {
      const mutation = `
      mutation BulkDeleteSources($ids: [ID!]!) {
        bulkDeleteSources(ids: $ids)
      }
    `;

      const result = await executeMutation<{ bulkDeleteSources: number }>(
        mutation,
        { ids },
      );
      return result.bulkDeleteSources;
    },
    [executeMutation],
  );

  const importOPML = useCallback(
    async (
      feedUrls: string[],
      groupId?: string,
    ): Promise<{ imported: number; skipped: number }> => {
      const mutation = `
      mutation ImportOPML($feedUrls: [String!]!, $groupId: String) {
        importOPML(feedUrls: $feedUrls, groupId: $groupId) {
          imported
          skipped
          failed
        }
      }
    `;

      const result = await executeMutation<{
        importOPML: { imported: number; skipped: number; failed: number };
      }>(mutation, { feedUrls, groupId });

      return {
        imported: result.importOPML.imported,
        skipped: result.importOPML.skipped,
      };
    },
    [executeMutation],
  );

  return {
    createSource,
    updateSource,
    deleteSource,
    togglePause,
    bulkDelete,
    importOPML,
    isLoading,
    error,
  };
}
