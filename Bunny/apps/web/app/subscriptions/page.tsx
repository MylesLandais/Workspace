"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  useSources,
  useSourceMutations,
  useAllTags,
} from "@/lib/hooks/use-sources";
import { useSubscriptionsStore } from "@/lib/store/subscriptions-store";
import {
  SubscriptionsHeader,
  SourceCard,
  SourceListItem,
  SourceTable,
  TagFilterBar,
  BulkActionsBar,
  BulkTagDialog,
} from "@/components/subscriptions";
import { useMasonryLayout } from "@/hooks/feed/useMasonryLayout";
import { useMediaQuery } from "@/hooks/feed/useMediaQuery";
import type { Source } from "@/lib/types/sources";
import { Loader2, Inbox } from "lucide-react";

export default function SubscriptionsPage() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [measuredHeights, setMeasuredHeights] = useState<
    Record<string, number>
  >({});

  // Store state
  const {
    viewMode,
    selectedIds,
    toggleSelection,
    selectAll,
    clearSelection,
    searchQuery,
    activeGroupId,
    activeSourceType,
    showPausedOnly,
    activeTags,
    toggleTag,
    clearTags,
    setAddDialogOpen,
    setEditingSource,
    setImportDialogOpen,
    setExportDialogOpen,
    bulkTagDialogOpen,
    setBulkTagDialogOpen,
  } = useSubscriptionsStore();

  // Data fetching
  const {
    sources,
    feedGroups,
    isLoading,
    error,
    totalCount,
    refresh,
    setFilters,
  } = useSources();

  const { togglePause, deleteSource, bulkDelete, bulkAddTags, bulkRemoveTags } =
    useSourceMutations();

  const { tags: allTagCounts, refresh: refreshTags } = useAllTags();
  const allTagNames = useMemo(
    () => allTagCounts.map((t) => t.tag),
    [allTagCounts],
  );

  // Update filters when store changes
  useEffect(() => {
    setFilters({
      groupId: activeGroupId || undefined,
      sourceType: activeSourceType || undefined,
      searchQuery: searchQuery || undefined,
      activity: showPausedOnly ? "paused" : undefined,
    });
  }, [
    activeGroupId,
    activeSourceType,
    searchQuery,
    showPausedOnly,
    setFilters,
  ]);

  // Filter sources client-side for immediate feedback
  const filteredSources = useMemo(() => {
    let result = sources;

    // Search filter (additional client-side filtering for responsiveness)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(query) ||
          s.subredditName?.toLowerCase().includes(query) ||
          s.youtubeHandle?.toLowerCase().includes(query) ||
          s.twitterHandle?.toLowerCase().includes(query) ||
          s.instagramHandle?.toLowerCase().includes(query) ||
          s.tiktokHandle?.toLowerCase().includes(query) ||
          s.description?.toLowerCase().includes(query),
      );
    }

    // Paused filter
    if (showPausedOnly) {
      result = result.filter((s) => s.isPaused);
    }

    // Tag filter (AND logic: source must have ALL active tags)
    if (activeTags.length > 0) {
      result = result.filter((s) =>
        activeTags.every((tag) => s.tags?.includes(tag)),
      );
    }

    return result;
  }, [sources, searchQuery, showPausedOnly, activeTags]);

  // Responsive column count for masonry
  const isTablet = useMediaQuery("(min-width: 640px)");
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const isWide = useMediaQuery("(min-width: 1440px)");
  const isUltra = useMediaQuery("(min-width: 1920px)");

  let columnCount = 1;
  let gap = 16;

  if (isUltra) {
    columnCount = 5;
    gap = 24;
  } else if (isWide) {
    columnCount = 4;
    gap = 24;
  } else if (isDesktop) {
    columnCount = 3;
    gap = 20;
  } else if (isTablet) {
    columnCount = 2;
    gap = 16;
  }

  // Container width tracking
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    resizeObserver.observe(containerRef.current);
    setContainerWidth(containerRef.current.clientWidth);

    return () => resizeObserver.disconnect();
  }, []);

  const handleHeightMeasured = useCallback((id: string, height: number) => {
    setMeasuredHeights((prev) => {
      if (prev[id] === height) return prev;
      return { ...prev, [id]: height };
    });
  }, []);

  const columnWidth =
    containerWidth > 0
      ? (containerWidth - (columnCount - 1) * gap) / columnCount
      : 300;

  // Convert sources to items for masonry layout
  const sourceItems = useMemo(
    () => filteredSources.map((s) => ({ id: s.id, width: 1, height: 1 })),
    [filteredSources],
  );

  const { itemPositions, containerHeight } = useMasonryLayout(
    sourceItems,
    columnCount,
    columnWidth,
    gap,
    measuredHeights,
  );

  // Handlers
  const handleViewFeed = useCallback(
    (sourceId: string) => {
      router.push(`/dashboard?source=${sourceId}`);
    },
    [router],
  );

  const handlePause = useCallback(
    async (sourceId: string) => {
      try {
        await togglePause(sourceId);
        refresh();
      } catch (err) {
        console.error("Failed to toggle pause:", err);
      }
    },
    [togglePause, refresh],
  );

  const handleEdit = useCallback(
    (source: Source) => {
      setEditingSource(source);
    },
    [setEditingSource],
  );

  const handleDelete = useCallback(
    async (sourceId: string) => {
      if (!confirm("Are you sure you want to delete this source?")) return;
      try {
        await deleteSource(sourceId);
        refresh();
      } catch (err) {
        console.error("Failed to delete source:", err);
      }
    },
    [deleteSource, refresh],
  );

  const handleFilterByTag = useCallback(
    (tag: string) => {
      toggleTag(tag);
    },
    [toggleTag],
  );

  const handleBulkPause = useCallback(async () => {
    const ids = Array.from(selectedIds);
    for (const id of ids) {
      try {
        await togglePause(id);
      } catch (err) {
        console.error("Failed to pause source:", err);
      }
    }
    clearSelection();
    refresh();
  }, [selectedIds, togglePause, clearSelection, refresh]);

  const handleBulkDelete = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (!confirm(`Are you sure you want to delete ${ids.length} sources?`))
      return;
    try {
      await bulkDelete(ids);
      clearSelection();
      refresh();
    } catch (err) {
      console.error("Failed to bulk delete:", err);
    }
  }, [selectedIds, bulkDelete, clearSelection, refresh]);

  const handleBulkTagComplete = useCallback(() => {
    clearSelection();
    refresh();
    refreshTags();
  }, [clearSelection, refresh, refreshTags]);

  // Empty state
  if (!isLoading && filteredSources.length === 0) {
    return (
      <div className="min-h-screen bg-app-bg">
        <SubscriptionsHeader
          sourceCount={totalCount}
          onAddSource={() => setAddDialogOpen(true)}
          onImportOPML={() => setImportDialogOpen(true)}
          onExportOPML={() => setExportDialogOpen(true)}
        />
        <TagFilterBar
          allTags={allTagCounts}
          activeTags={activeTags}
          onToggleTag={toggleTag}
          onClearTags={clearTags}
        />
        <div className="flex flex-col items-center justify-center py-32 px-6">
          <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6">
            <Inbox className="w-8 h-8 text-white/40" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            No sources found
          </h2>
          <p className="text-sm text-white/50 text-center max-w-md mb-6">
            {searchQuery
              ? `No sources match "${searchQuery}". Try a different search term.`
              : activeTags.length > 0
                ? "No sources match the selected tags. Try removing some tag filters."
                : "You haven't added any subscriptions yet. Add sources to start building your feed."}
          </p>
          {!searchQuery && activeTags.length === 0 && (
            <button
              onClick={() => setAddDialogOpen(true)}
              className="px-6 py-3 rounded-xl bg-app-accent text-black font-medium hover:bg-app-accent-hover transition-colors"
            >
              Add your first source
            </button>
          )}
          {activeTags.length > 0 && (
            <button
              onClick={clearTags}
              className="px-4 py-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors"
            >
              Clear tag filters
            </button>
          )}
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading && sources.length === 0) {
    return (
      <div className="min-h-screen bg-app-bg">
        <SubscriptionsHeader
          sourceCount={0}
          onAddSource={() => setAddDialogOpen(true)}
          onImportOPML={() => setImportDialogOpen(true)}
          onExportOPML={() => setExportDialogOpen(true)}
        />
        <div className="flex items-center justify-center py-32">
          <Loader2 className="w-8 h-8 animate-spin text-app-accent" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-app-bg">
        <SubscriptionsHeader
          sourceCount={0}
          onAddSource={() => setAddDialogOpen(true)}
          onImportOPML={() => setImportDialogOpen(true)}
          onExportOPML={() => setExportDialogOpen(true)}
        />
        <div className="flex flex-col items-center justify-center py-32 px-6">
          <div className="text-red-400 mb-4">Error loading sources</div>
          <p className="text-sm text-white/50 mb-4">{error}</p>
          <button
            onClick={refresh}
            className="px-4 py-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-app-bg">
      <SubscriptionsHeader
        sourceCount={filteredSources.length}
        onAddSource={() => setAddDialogOpen(true)}
        onImportOPML={() => setImportDialogOpen(true)}
        onExportOPML={() => setExportDialogOpen(true)}
      />

      <TagFilterBar
        allTags={allTagCounts}
        activeTags={activeTags}
        onToggleTag={toggleTag}
        onClearTags={clearTags}
      />

      {/* Main content */}
      <main className="p-6">
        {viewMode === "masonry" && (
          <div
            ref={containerRef}
            className="relative w-full mx-auto max-w-[2400px]"
            style={{ height: containerHeight }}
          >
            {filteredSources.map((source) => {
              const pos = itemPositions[source.id] || { x: 0, y: 0 };
              return (
                <SourceCard
                  key={source.id}
                  source={source}
                  columnWidth={columnWidth}
                  x={pos.x}
                  y={pos.y}
                  onHeightMeasured={handleHeightMeasured}
                  isSelected={selectedIds.has(source.id)}
                  onSelect={toggleSelection}
                  onPause={handlePause}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onViewFeed={handleViewFeed}
                  onFilterByTag={handleFilterByTag}
                />
              );
            })}
          </div>
        )}

        {viewMode === "list" && (
          <div className="max-w-4xl mx-auto space-y-2">
            {filteredSources.map((source) => (
              <SourceListItem
                key={source.id}
                source={source}
                isSelected={selectedIds.has(source.id)}
                onSelect={toggleSelection}
                onPause={handlePause}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onViewFeed={handleViewFeed}
                onFilterByTag={handleFilterByTag}
              />
            ))}
          </div>
        )}

        {viewMode === "table" && (
          <div className="max-w-7xl mx-auto">
            <SourceTable
              sources={filteredSources}
              selectedIds={selectedIds}
              onSelect={toggleSelection}
              onSelectAll={selectAll}
              onClearSelection={clearSelection}
              onPause={handlePause}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onViewFeed={handleViewFeed}
              onFilterByTag={handleFilterByTag}
            />
          </div>
        )}
      </main>

      {/* Bulk actions bar */}
      <BulkActionsBar
        selectedCount={selectedIds.size}
        onTag={() => setBulkTagDialogOpen(true)}
        onPause={handleBulkPause}
        onDelete={handleBulkDelete}
        onClear={clearSelection}
      />

      {/* Bulk tag dialog */}
      <BulkTagDialog
        open={bulkTagDialogOpen}
        onClose={() => setBulkTagDialogOpen(false)}
        selectedCount={selectedIds.size}
        selectedIds={Array.from(selectedIds)}
        allTags={allTagNames}
        onBulkAddTags={bulkAddTags}
        onBulkRemoveTags={bulkRemoveTags}
        onComplete={handleBulkTagComplete}
      />

      {/* Loading overlay for refreshes */}
      {isLoading && sources.length > 0 && (
        <div className="fixed bottom-6 right-6 px-4 py-2 rounded-xl bg-zinc-900 border border-white/10 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-app-accent" />
          <span className="text-sm text-white/60">Refreshing...</span>
        </div>
      )}
    </div>
  );
}
