"use client";

import { useState, useCallback, useEffect } from "react";
import { Plus, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  SourceManagementHeader,
  SourceTabs,
  SourceFilters,
  SourceTable,
  OPMLImportDialog,
  AddSourceDialog,
} from "@/components/sources";
import { useUserSources } from "@/lib/hooks/use-user-sources";
import { useSession } from "@/lib/auth-client";
import type { CreateSourceInput } from "@/lib/types/sources";

export default function ManageSourcesPage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
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
    setFilters,
    setViewMode,
    selectAll,
    selectOne,
    refresh,
    createSource,
    togglePause,
    deleteSource,
    importOPML,
  } = useUserSources();

  // Protect page
  useEffect(() => {
    if (!isPending && !session) {
      router.push("/auth");
    }
  }, [session, isPending, router]);

  const handleImport = useCallback(
    async (feedUrls: string[]) => {
      // Find the user's default group
      const defaultGroup =
        feedGroups.find((g) => g.name === "My Subreddits") || feedGroups[0];
      await importOPML(feedUrls, defaultGroup?.id);
      await refresh();
    },
    [importOPML, refresh, feedGroups],
  );

  const handleAddSource = useCallback(
    async (input: Omit<CreateSourceInput, "userId">) => {
      const defaultGroup =
        feedGroups.find((g) => g.name === "My Subreddits") || feedGroups[0];
      await createSource({
        ...input,
        groupId: input.groupId || defaultGroup?.id,
      });
      await refresh();
    },
    [createSource, refresh, feedGroups],
  );

  const handlePause = useCallback(
    async (id: string) => {
      await togglePause(id);
      await refresh();
    },
    [togglePause, refresh],
  );

  const handleMove = useCallback((id: string) => {
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

  if (isPending || (isLoading && !sources.length)) {
    return (
      <div className="min-h-screen bg-app-bg flex items-center justify-center">
        <div className="text-app-muted animate-pulse">Loading sources...</div>
      </div>
    );
  }

  if (!session) return null;

  const inactiveCount = sources.filter((s) => !s.isActive).length;

  return (
    <div className="min-h-screen bg-app-bg">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-6">
          <Link
            href="/profile/edit"
            className="text-app-muted hover:text-app-text transition-colors flex items-center gap-2 text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Profile
          </Link>
        </div>

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
