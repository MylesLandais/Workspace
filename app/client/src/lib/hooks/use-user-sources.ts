import { useMemo, useCallback, useEffect } from "react";
import { useSession } from "@/lib/auth-client";
import { useSources, useSourceMutations } from "./use-sources";
import type { Source, CreateSourceInput } from "@/lib/types/sources";

export function useUserSources() {
  const { data: session } = useSession();
  const userId = session?.user?.id;

  const {
    sources,
    feedGroups,
    filters,
    isLoading,
    error,
    totalCount,
    setFilters,
    refresh,
    ...rest
  } = useSources();

  const { createSource: baseCreateSource, ...mutations } = useSourceMutations();

  // Automatically apply userId filter when session is available
  useEffect(() => {
    if (userId && filters.userId !== userId) {
      setFilters({ ...filters, userId });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, filters.userId, setFilters]);

  // Extract active sources for feed filtering
  const activeSources = useMemo(
    () => sources.filter((s) => s.isActive && !s.isPaused),
    [sources],
  );

  const feedFilters = useMemo(
    () => ({
      sources: activeSources.map((s) => s.subredditName || s.name),
      persons: [],
      tags: [],
      searchQuery: "",
      categories: [],
    }),
    [activeSources],
  );

  const createSource = useCallback(
    async (input: Omit<CreateSourceInput, "userId">) => {
      if (!userId) throw new Error("User session required to create source");
      return await baseCreateSource({ ...input, userId });
    },
    [baseCreateSource, userId],
  );

  return {
    sources,
    activeSources,
    feedFilters,
    feedGroups,
    isLoading: isLoading || !userId,
    error,
    totalCount,
    refresh,
    createSource,
    ...mutations,
    ...rest,
  };
}
