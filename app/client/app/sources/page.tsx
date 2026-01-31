"use client";

import { useState, useCallback } from "react";
import { Plus } from "lucide-react";
import {
  SourceManagementHeader,
  SourceTabs,
  SourceFilters,
  SourceTable,
  OPMLImportDialog,
  AddSourceDialog,
} from "@/components/sources";
import { useSources, useSourceMutations } from "@/lib/hooks/use-sources";
import type { CreateSourceInput } from "@/lib/types/sources";

export default function SourcesPage() {
  const [activeTab, setActiveTab] = useState<"organize" | "discover">(
    "organize",
  );
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);

  const {
    sources,
    feedGroups,
    filters,
    viewMode,
    selectedIds,
    isLoading,
    totalCount,
    inactiveCount,
    setFilters,
    setViewMode,
    selectAll,
    selectOne,
    refresh,
  } = useSources();

  const { createSource, togglePause, deleteSource, importOPML } =
    useSourceMutations();

  const handleImport = useCallback(
    async (feedUrls: string[]) => {
      await importOPML(feedUrls);
      await refresh();
    },
    [importOPML, refresh],
  );

  const handleAddSource = useCallback(
    async (input: CreateSourceInput) => {
      await createSource(input);
      await refresh();
    },
    [createSource, refresh],
  );

  const handlePause = useCallback(
    async (id: string) => {
      await togglePause(id);
      await refresh();
    },
    [togglePause, refresh],
  );

  const handleMove = useCallback((id: string) => {
    // TODO: Implement move to folder dialog
    console.log("Move source:", id);
  }, []);

  const handleDelete = useCallback(
    async (id: string) => {
      if (confirm("Are you sure you want to unsubscribe from this source?")) {
        await deleteSource(id);
        await refresh();
      }
    },
    [deleteSource, refresh],
  );

  return (
    <div className="min-h-screen bg-app-bg">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <SourceManagementHeader
          totalCount={totalCount}
          inactiveCount={inactiveCount}
          onImportClick={() => setShowImportDialog(true)}
        />

        <SourceTabs activeTab={activeTab} onTabChange={setActiveTab} />

        {activeTab === "organize" && (
          <>
            <SourceFilters
              filters={filters}
              feedGroups={feedGroups}
              onFiltersChange={setFilters}
            />

            <SourceTable
              sources={sources}
              selectedIds={selectedIds}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              onSelectAll={selectAll}
              onSelect={selectOne}
              onPause={handlePause}
              onMove={handleMove}
              onDelete={handleDelete}
              onRefresh={refresh}
              isLoading={isLoading}
            />

            {/* Floating Add Button */}
            <button
              onClick={() => setShowAddDialog(true)}
              className="fixed bottom-6 right-6 p-4 bg-white text-black rounded-full shadow-lg hover:bg-zinc-200 transition-colors"
              title="Add Source"
            >
              <Plus className="w-6 h-6" />
            </button>
          </>
        )}

        {activeTab === "discover" && (
          <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-8 text-center">
            <p className="text-app-muted">
              Discover new sources coming soon...
            </p>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <OPMLImportDialog
        isOpen={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        onImport={handleImport}
      />

      <AddSourceDialog
        isOpen={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        onAdd={handleAddSource}
      />
    </div>
  );
}
