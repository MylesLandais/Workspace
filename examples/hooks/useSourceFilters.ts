/**
 * useSourceFilters - Filter state management for sources and feed
 *
 * Manages filter state that can be shared between source list and feed views.
 * Supports URL persistence for shareable filtered views.
 */

import { useState, useCallback, useMemo } from 'react';

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

export interface FeedFilters {
  persons: string[];
  sources: string[];
  tags: string[];
  searchQuery: string;
  categories: string[];
}

// Default empty filters
const DEFAULT_SOURCE_FILTERS: SourceFiltersInput = {
  groupId: undefined,
  sourceType: undefined,
  activity: 'ALL',
  searchQuery: '',
};

const DEFAULT_FEED_FILTERS: FeedFilters = {
  persons: [],
  sources: [],
  tags: [],
  searchQuery: '',
  categories: [],
};

export interface UseSourceFiltersReturn {
  filters: SourceFiltersInput;
  setGroupId: (groupId: string | undefined) => void;
  setSourceType: (sourceType: Platform | undefined) => void;
  setActivity: (activity: ActivityFilter) => void;
  setSearchQuery: (searchQuery: string) => void;
  reset: () => void;
  hasActiveFilters: boolean;
}

/**
 * Hook for managing source list filters
 *
 * @example
 * ```tsx
 * const { filters, setSourceType, setActivity, reset } = useSourceFilters();
 *
 * return (
 *   <div>
 *     <select onChange={e => setSourceType(e.target.value as Platform)}>
 *       <option value="">All Types</option>
 *       <option value="REDDIT">Reddit</option>
 *       <option value="YOUTUBE">YouTube</option>
 *     </select>
 *     <button onClick={reset}>Clear Filters</button>
 *   </div>
 * );
 * ```
 */
export function useSourceFilters(
  initialFilters?: Partial<SourceFiltersInput>
): UseSourceFiltersReturn {
  const [filters, setFilters] = useState<SourceFiltersInput>({
    ...DEFAULT_SOURCE_FILTERS,
    ...initialFilters,
  });

  const setGroupId = useCallback((groupId: string | undefined) => {
    setFilters((prev) => ({ ...prev, groupId }));
  }, []);

  const setSourceType = useCallback((sourceType: Platform | undefined) => {
    setFilters((prev) => ({ ...prev, sourceType }));
  }, []);

  const setActivity = useCallback((activity: ActivityFilter) => {
    setFilters((prev) => ({ ...prev, activity }));
  }, []);

  const setSearchQuery = useCallback((searchQuery: string) => {
    setFilters((prev) => ({ ...prev, searchQuery }));
  }, []);

  const reset = useCallback(() => {
    setFilters(DEFAULT_SOURCE_FILTERS);
  }, []);

  const hasActiveFilters = useMemo(() => {
    return (
      filters.groupId !== undefined ||
      filters.sourceType !== undefined ||
      filters.activity !== 'ALL' ||
      (filters.searchQuery?.length ?? 0) > 0
    );
  }, [filters]);

  return {
    filters,
    setGroupId,
    setSourceType,
    setActivity,
    setSearchQuery,
    reset,
    hasActiveFilters,
  };
}

export interface UseFeedFiltersReturn {
  filters: FeedFilters;
  setPersons: (persons: string[]) => void;
  addPerson: (person: string) => void;
  removePerson: (person: string) => void;
  setSources: (sources: string[]) => void;
  addSource: (source: string) => void;
  removeSource: (source: string) => void;
  setTags: (tags: string[]) => void;
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
  setSearchQuery: (searchQuery: string) => void;
  setCategories: (categories: string[]) => void;
  toggleCategory: (category: string) => void;
  reset: () => void;
  hasActiveFilters: boolean;
  activeFilterCount: number;
}

/**
 * Hook for managing feed filters
 *
 * @example
 * ```tsx
 * const {
 *   filters,
 *   addSource,
 *   removeSource,
 *   setSearchQuery,
 *   toggleCategory
 * } = useFeedFilters();
 *
 * return (
 *   <div>
 *     <input
 *       type="text"
 *       placeholder="Search..."
 *       onChange={e => setSearchQuery(e.target.value)}
 *     />
 *     <button onClick={() => toggleCategory('VIDEO')}>
 *       {filters.categories.includes('VIDEO') ? 'Show All' : 'Videos Only'}
 *     </button>
 *   </div>
 * );
 * ```
 */
export function useFeedFilters(
  initialFilters?: Partial<FeedFilters>
): UseFeedFiltersReturn {
  const [filters, setFilters] = useState<FeedFilters>({
    ...DEFAULT_FEED_FILTERS,
    ...initialFilters,
  });

  // Persons
  const setPersons = useCallback((persons: string[]) => {
    setFilters((prev) => ({ ...prev, persons }));
  }, []);

  const addPerson = useCallback((person: string) => {
    setFilters((prev) => ({
      ...prev,
      persons: prev.persons.includes(person)
        ? prev.persons
        : [...prev.persons, person],
    }));
  }, []);

  const removePerson = useCallback((person: string) => {
    setFilters((prev) => ({
      ...prev,
      persons: prev.persons.filter((p) => p !== person),
    }));
  }, []);

  // Sources
  const setSources = useCallback((sources: string[]) => {
    setFilters((prev) => ({ ...prev, sources }));
  }, []);

  const addSource = useCallback((source: string) => {
    setFilters((prev) => ({
      ...prev,
      sources: prev.sources.includes(source)
        ? prev.sources
        : [...prev.sources, source],
    }));
  }, []);

  const removeSource = useCallback((source: string) => {
    setFilters((prev) => ({
      ...prev,
      sources: prev.sources.filter((s) => s !== source),
    }));
  }, []);

  // Tags
  const setTags = useCallback((tags: string[]) => {
    setFilters((prev) => ({ ...prev, tags }));
  }, []);

  const addTag = useCallback((tag: string) => {
    setFilters((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag) ? prev.tags : [...prev.tags, tag],
    }));
  }, []);

  const removeTag = useCallback((tag: string) => {
    setFilters((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tag),
    }));
  }, []);

  // Search
  const setSearchQuery = useCallback((searchQuery: string) => {
    setFilters((prev) => ({ ...prev, searchQuery }));
  }, []);

  // Categories
  const setCategories = useCallback((categories: string[]) => {
    setFilters((prev) => ({ ...prev, categories }));
  }, []);

  const toggleCategory = useCallback((category: string) => {
    setFilters((prev) => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter((c) => c !== category)
        : [...prev.categories, category],
    }));
  }, []);

  // Reset
  const reset = useCallback(() => {
    setFilters(DEFAULT_FEED_FILTERS);
  }, []);

  // Computed
  const hasActiveFilters = useMemo(() => {
    return (
      filters.persons.length > 0 ||
      filters.sources.length > 0 ||
      filters.tags.length > 0 ||
      filters.searchQuery.length > 0 ||
      filters.categories.length > 0
    );
  }, [filters]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.persons.length > 0) count += filters.persons.length;
    if (filters.sources.length > 0) count += filters.sources.length;
    if (filters.tags.length > 0) count += filters.tags.length;
    if (filters.searchQuery.length > 0) count += 1;
    if (filters.categories.length > 0) count += filters.categories.length;
    return count;
  }, [filters]);

  return {
    filters,
    setPersons,
    addPerson,
    removePerson,
    setSources,
    addSource,
    removeSource,
    setTags,
    addTag,
    removeTag,
    setSearchQuery,
    setCategories,
    toggleCategory,
    reset,
    hasActiveFilters,
    activeFilterCount,
  };
}

/**
 * Serialize filters to URL search params
 */
export function filtersToSearchParams(filters: FeedFilters): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.persons.length > 0) {
    params.set('persons', filters.persons.join(','));
  }
  if (filters.sources.length > 0) {
    params.set('sources', filters.sources.join(','));
  }
  if (filters.tags.length > 0) {
    params.set('tags', filters.tags.join(','));
  }
  if (filters.searchQuery) {
    params.set('q', filters.searchQuery);
  }
  if (filters.categories.length > 0) {
    params.set('categories', filters.categories.join(','));
  }

  return params;
}

/**
 * Parse filters from URL search params
 */
export function searchParamsToFilters(params: URLSearchParams): FeedFilters {
  return {
    persons: params.get('persons')?.split(',').filter(Boolean) || [],
    sources: params.get('sources')?.split(',').filter(Boolean) || [],
    tags: params.get('tags')?.split(',').filter(Boolean) || [],
    searchQuery: params.get('q') || '',
    categories: params.get('categories')?.split(',').filter(Boolean) || [],
  };
}
