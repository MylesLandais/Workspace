import { create } from "zustand";

interface SearchFilters {
  query: string;
  categories: string[];
  tags: string[];
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  sortBy: "relevance" | "newest" | "oldest";
}

interface SearchState {
  filters: SearchFilters;
  isFiltersOpen: boolean;
  setQuery: (query: string) => void;
  toggleFilters: () => void;
  setCategories: (categories: string[]) => void;
  setTags: (tags: string[]) => void;
  resetFilters: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  filters: {
    query: "",
    categories: [],
    tags: [],
    dateRange: { start: null, end: null },
    sortBy: "newest",
  },
  isFiltersOpen: false,
  setQuery: (query) =>
    set((state) => ({
      filters: { ...state.filters, query },
    })),
  toggleFilters: () =>
    set((state) => ({ isFiltersOpen: !state.isFiltersOpen })),
  setCategories: (categories) =>
    set((state) => ({
      filters: { ...state.filters, categories },
    })),
  setTags: (tags) =>
    set((state) => ({
      filters: { ...state.filters, tags },
    })),
  resetFilters: () =>
    set({
      filters: {
        query: "",
        categories: [],
        tags: [],
        dateRange: { start: null, end: null },
        sortBy: "newest",
      },
    }),
}));
