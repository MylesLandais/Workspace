import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Source, SourceType } from "@/lib/types/sources";

export type SubscriptionsViewMode = "masonry" | "list" | "table";

interface SubscriptionsState {
  // View state
  viewMode: SubscriptionsViewMode;
  setViewMode: (mode: SubscriptionsViewMode) => void;

  // Selection state
  selectedIds: Set<string>;
  toggleSelection: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelection: () => void;
  isSelected: (id: string) => boolean;

  // Filter state
  activeGroupId: string | null;
  setActiveGroupId: (id: string | null) => void;
  activeSourceType: SourceType | null;
  setActiveSourceType: (type: SourceType | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  showPausedOnly: boolean;
  setShowPausedOnly: (show: boolean) => void;
  activeTags: string[];
  toggleTag: (tag: string) => void;
  clearTags: () => void;

  // Table state
  sortColumn: string;
  sortDirection: "asc" | "desc";
  setSorting: (column: string, direction: "asc" | "desc") => void;

  // Dialog states
  addDialogOpen: boolean;
  setAddDialogOpen: (open: boolean) => void;
  editingSource: Source | null;
  setEditingSource: (source: Source | null) => void;
  importDialogOpen: boolean;
  setImportDialogOpen: (open: boolean) => void;
  exportDialogOpen: boolean;
  setExportDialogOpen: (open: boolean) => void;
  bulkTagDialogOpen: boolean;
  setBulkTagDialogOpen: (open: boolean) => void;

  // Reset
  resetFilters: () => void;
}

export const useSubscriptionsStore = create<SubscriptionsState>()(
  persist(
    (set, get) => ({
      // View state
      viewMode: "masonry",
      setViewMode: (mode) => set({ viewMode: mode }),

      // Selection state (not persisted)
      selectedIds: new Set(),
      toggleSelection: (id) =>
        set((state) => {
          const next = new Set(state.selectedIds);
          if (next.has(id)) {
            next.delete(id);
          } else {
            next.add(id);
          }
          return { selectedIds: next };
        }),
      selectAll: (ids) => set({ selectedIds: new Set(ids) }),
      clearSelection: () => set({ selectedIds: new Set() }),
      isSelected: (id) => get().selectedIds.has(id),

      // Filter state
      activeGroupId: null,
      setActiveGroupId: (id) => set({ activeGroupId: id }),
      activeSourceType: null,
      setActiveSourceType: (type) => set({ activeSourceType: type }),
      searchQuery: "",
      setSearchQuery: (query) => set({ searchQuery: query }),
      showPausedOnly: false,
      setShowPausedOnly: (show) => set({ showPausedOnly: show }),
      activeTags: [],
      toggleTag: (tag) =>
        set((state) => {
          const tags = state.activeTags.includes(tag)
            ? state.activeTags.filter((t) => t !== tag)
            : [...state.activeTags, tag];
          return { activeTags: tags };
        }),
      clearTags: () => set({ activeTags: [] }),

      // Table state
      sortColumn: "name",
      sortDirection: "asc",
      setSorting: (column, direction) =>
        set({ sortColumn: column, sortDirection: direction }),

      // Dialog states
      addDialogOpen: false,
      setAddDialogOpen: (open) => set({ addDialogOpen: open }),
      editingSource: null,
      setEditingSource: (source) => set({ editingSource: source }),
      importDialogOpen: false,
      setImportDialogOpen: (open) => set({ importDialogOpen: open }),
      exportDialogOpen: false,
      setExportDialogOpen: (open) => set({ exportDialogOpen: open }),
      bulkTagDialogOpen: false,
      setBulkTagDialogOpen: (open) => set({ bulkTagDialogOpen: open }),

      // Reset
      resetFilters: () =>
        set({
          activeGroupId: null,
          activeSourceType: null,
          searchQuery: "",
          showPausedOnly: false,
          activeTags: [],
        }),
    }),
    {
      name: "subscriptions-store",
      partialize: (state) => ({
        viewMode: state.viewMode,
        sortColumn: state.sortColumn,
        sortDirection: state.sortDirection,
      }),
    },
  ),
);
