"use client";

import { RefreshCw } from "lucide-react";
import type { Source } from "@/lib/types/sources";
import { SourceRow } from "./SourceRow";
import { SourceViewToggle } from "./SourceViewToggle";
import { SourceIcon } from "./SourceIcon";
import { SourceActions } from "./SourceActions";
import type { ViewMode } from "@/lib/types/sources";

interface SourceTableProps {
  sources: Source[];
  selectedIds: Set<string>;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onSelectAll: (selected: boolean) => void;
  onSelect: (id: string, selected: boolean) => void;
  onPause: (id: string) => void;
  onMove: (id: string) => void;
  onDelete: (id: string) => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

export function SourceTable({
  sources,
  selectedIds,
  viewMode,
  onViewModeChange,
  onSelectAll,
  onSelect,
  onPause,
  onMove,
  onDelete,
  onRefresh,
  isLoading,
}: SourceTableProps) {
  const allSelected = sources.length > 0 && selectedIds.size === sources.length;
  const someSelected =
    selectedIds.size > 0 && selectedIds.size < sources.length;

  return (
    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
      {/* Table Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => {
              if (el) el.indeterminate = someSelected;
            }}
            onChange={(e) => onSelectAll(e.target.checked)}
            className="w-4 h-4 rounded border-white/20 bg-zinc-900 text-app-accent focus:ring-app-accent/50"
          />
          <span className="text-sm text-app-muted">Select All</span>
        </div>
        <div className="flex items-center gap-3">
          <SourceViewToggle
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
          />
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 rounded-lg hover:bg-white/5 text-app-muted hover:text-app-text transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>

      {/* Table Content */}
      {viewMode === "table" ? (
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="py-3 px-4 w-12"></th>
              <th className="py-3 px-4 text-left text-xs font-medium text-app-muted uppercase tracking-wider">
                Feed Name
              </th>
              <th className="py-3 px-4 text-center text-xs font-medium text-app-muted uppercase tracking-wider">
                Stories / Month
              </th>
              <th className="py-3 px-4 text-center text-xs font-medium text-app-muted uppercase tracking-wider">
                Reads / Month
              </th>
              <th className="py-3 px-4 w-16 text-xs font-medium text-app-muted uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <SourceRow
                key={source.id}
                source={source}
                isSelected={selectedIds.has(source.id)}
                onSelect={onSelect}
                onPause={onPause}
                onMove={onMove}
                onDelete={onDelete}
              />
            ))}
          </tbody>
        </table>
      ) : (
        <div
          className={`p-4 ${viewMode === "grid" ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" : "space-y-2"}`}
        >
          {sources.map((source) => (
            <SourceCard
              key={source.id}
              source={source}
              isSelected={selectedIds.has(source.id)}
              onSelect={onSelect}
              onPause={onPause}
              onMove={onMove}
              onDelete={onDelete}
              viewMode={viewMode}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {sources.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-app-muted">No sources found</p>
        </div>
      )}
    </div>
  );
}

// Card component for grid and list views
function SourceCard({
  source,
  isSelected,
  onSelect,
  onPause,
  onMove,
  onDelete,
  viewMode,
}: {
  source: Source;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  onPause: (id: string) => void;
  onMove: (id: string) => void;
  onDelete: (id: string) => void;
  viewMode: "grid" | "list";
}) {
  const getDisplayName = () => {
    if (source.subredditName) return `r/${source.subredditName}`;
    if (source.twitterHandle) return `@${source.twitterHandle}`;
    if (source.youtubeHandle)
      return source.youtubeHandle.startsWith("@")
        ? source.youtubeHandle
        : `@${source.youtubeHandle}`;
    if (source.instagramHandle) return `@${source.instagramHandle}`;
    if (source.tiktokHandle) return `@${source.tiktokHandle}`;
    return source.name;
  };

  if (viewMode === "grid") {
    return (
      <div
        className={`p-4 bg-zinc-900/50 border border-white/5 rounded-xl ${source.isPaused ? "opacity-50" : ""}`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onSelect(source.id, e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-zinc-900 text-app-accent focus:ring-app-accent/50"
            />
            <SourceIcon
              sourceType={source.sourceType}
              iconUrl={source.iconUrl}
              size="md"
            />
          </div>
          <SourceActions
            source={source}
            onPause={onPause}
            onMove={onMove}
            onDelete={onDelete}
          />
        </div>
        <div className="text-sm font-medium text-app-text truncate">
          {getDisplayName()}
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs text-app-muted">
          <span>{source.storiesPerMonth} stories</span>
          <span>{source.readsPerMonth} reads</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex items-center gap-4 p-3 bg-zinc-900/50 border border-white/5 rounded-xl ${source.isPaused ? "opacity-50" : ""}`}
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={(e) => onSelect(source.id, e.target.checked)}
        className="w-4 h-4 rounded border-white/20 bg-zinc-900 text-app-accent focus:ring-app-accent/50"
      />
      <SourceIcon
        sourceType={source.sourceType}
        iconUrl={source.iconUrl}
        size="md"
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-app-text truncate">
          {getDisplayName()}
        </div>
        {source.description && (
          <div className="text-xs text-app-muted truncate">
            {source.description}
          </div>
        )}
      </div>
      <div className="flex items-center gap-4 text-xs text-app-muted">
        <span>{source.storiesPerMonth}</span>
        <span>{source.readsPerMonth}</span>
      </div>
      <SourceActions
        source={source}
        onPause={onPause}
        onMove={onMove}
        onDelete={onDelete}
      />
    </div>
  );
}
