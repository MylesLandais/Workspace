"use client";

import { useMemo, useState } from "react";
import type { Source, SourceType } from "@/lib/types/sources";
import {
  Rss,
  Youtube,
  Twitter,
  Instagram,
  Pause,
  Play,
  Pencil,
  Trash2,
  ExternalLink,
  ChevronUp,
  ChevronDown,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSubscriptionsStore } from "@/lib/store/subscriptions-store";

function CloverIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 36 36"
      fill="currentColor"
      className={className}
    >
      <path d="M32.551 18.852c-2.093-1.848-6.686-3.264-10.178-3.84 3.492-.577 8.085-1.993 10.178-3.839 2.014-1.776 2.963-2.948 2.141-4.722-.566-1.219-2.854-1.333-4.166-2.491C29.214 2.802 29.083.783 27.7.285c-2.01-.726-3.336.114-5.347 1.889-2.094 1.847-3.698 5.899-4.353 8.98-.653-3.082-2.258-7.134-4.351-8.98C11.634.397 10.308-.441 8.297.285c-1.383.5-1.512 2.518-2.823 3.675S1.872 5.234 1.308 6.454c-.823 1.774.129 2.943 2.14 4.718 2.094 1.847 6.688 3.263 10.181 3.84-3.493.577-8.087 1.993-10.181 3.84-2.013 1.775-2.963 2.945-2.139 4.721.565 1.219 2.854 1.334 4.166 2.49 1.311 1.158 1.444 3.178 2.827 3.676 2.009.727 3.336-.115 5.348-1.889 1.651-1.457 2.997-4.288 3.814-6.933-.262 4.535.528 10.591 3.852 14.262 1.344 1.483 2.407.551 2.822.187.416-.365 1.605-1.414.186-2.822-3.91-3.883-5.266-7.917-5.628-11.14.827 2.498 2.107 5.077 3.657 6.446 2.012 1.775 3.339 2.615 5.351 1.889 1.382-.5 1.512-2.52 2.822-3.676 1.312-1.158 3.602-1.273 4.166-2.494.822-1.774-.13-2.944-2.141-4.717z" />
    </svg>
  );
}

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

interface SourceTableProps {
  sources: Source[];
  selectedIds: Set<string>;
  onSelect: (id: string) => void;
  onSelectAll: (ids: string[]) => void;
  onClearSelection: () => void;
  onPause: (id: string) => void;
  onEdit: (source: Source) => void;
  onDelete: (id: string) => void;
  onViewFeed: (id: string) => void;
}

type SortColumn = "name" | "sourceType" | "group" | "storiesPerMonth" | "health" | "lastSynced";

function getSourceIcon(sourceType: SourceType) {
  switch (sourceType) {
    case "RSS":
      return <Rss className="w-3.5 h-3.5" />;
    case "REDDIT":
      return <span className="text-[10px] font-bold">r/</span>;
    case "YOUTUBE":
      return <Youtube className="w-3.5 h-3.5" />;
    case "TWITTER":
      return <Twitter className="w-3.5 h-3.5" />;
    case "INSTAGRAM":
      return <Instagram className="w-3.5 h-3.5" />;
    case "TIKTOK":
      return <TikTokIcon className="w-3.5 h-3.5" />;
    case "VSCO":
      return <span className="text-[10px] font-bold">VS</span>;
    case "IMAGEBOARD":
      return <CloverIcon className="w-3.5 h-3.5" />;
    default:
      return <Rss className="w-3.5 h-3.5" />;
  }
}

function getSourceTypeColor(sourceType: SourceType) {
  switch (sourceType) {
    case "RSS":
      return "bg-orange-500/20 text-orange-400";
    case "REDDIT":
      return "bg-orange-600/20 text-orange-500";
    case "YOUTUBE":
      return "bg-red-500/20 text-red-400";
    case "TWITTER":
      return "bg-sky-500/20 text-sky-400";
    case "INSTAGRAM":
      return "bg-pink-500/20 text-pink-400";
    case "TIKTOK":
      return "bg-zinc-500/20 text-zinc-300";
    case "VSCO":
      return "bg-zinc-600/20 text-zinc-300";
    case "IMAGEBOARD":
      return "bg-emerald-500/20 text-emerald-400";
    default:
      return "bg-white/10 text-white/50";
  }
}

function getHealthColor(health: string) {
  switch (health) {
    case "green":
      return "bg-emerald-500";
    case "yellow":
      return "bg-amber-500";
    case "red":
      return "bg-red-500";
    default:
      return "bg-zinc-500";
  }
}

function formatLastSynced(lastSynced: string | undefined): string {
  if (!lastSynced) return "Never";
  const date = new Date(lastSynced);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

const columns: { key: SortColumn; label: string; sortable: boolean; className?: string }[] = [
  { key: "name", label: "Name", sortable: true, className: "min-w-[200px]" },
  { key: "sourceType", label: "Type", sortable: true, className: "w-28" },
  { key: "group", label: "Group", sortable: true, className: "w-36" },
  { key: "storiesPerMonth", label: "Posts/mo", sortable: true, className: "w-24 text-right" },
  { key: "health", label: "Health", sortable: true, className: "w-24" },
  { key: "lastSynced", label: "Last Synced", sortable: true, className: "w-28" },
];

export function SourceTable({
  sources,
  selectedIds,
  onSelect,
  onSelectAll,
  onClearSelection,
  onPause,
  onEdit,
  onDelete,
  onViewFeed,
}: SourceTableProps) {
  const { sortColumn, sortDirection, setSorting } = useSubscriptionsStore();

  const sortedSources = useMemo(() => {
    const sorted = [...sources].sort((a, b) => {
      let comparison = 0;

      switch (sortColumn) {
        case "name":
          comparison = a.name.localeCompare(b.name);
          break;
        case "sourceType":
          comparison = a.sourceType.localeCompare(b.sourceType);
          break;
        case "group":
          comparison = (a.group || "").localeCompare(b.group || "");
          break;
        case "storiesPerMonth":
          comparison = a.storiesPerMonth - b.storiesPerMonth;
          break;
        case "health":
          const healthOrder = { green: 0, yellow: 1, red: 2 };
          comparison =
            (healthOrder[a.health as keyof typeof healthOrder] || 3) -
            (healthOrder[b.health as keyof typeof healthOrder] || 3);
          break;
        case "lastSynced":
          const aDate = a.lastSynced ? new Date(a.lastSynced).getTime() : 0;
          const bDate = b.lastSynced ? new Date(b.lastSynced).getTime() : 0;
          comparison = bDate - aDate; // More recent first
          break;
        default:
          comparison = 0;
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });

    return sorted;
  }, [sources, sortColumn, sortDirection]);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSorting(column, sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSorting(column, "asc");
    }
  };

  const allSelected = sources.length > 0 && selectedIds.size === sources.length;
  const someSelected = selectedIds.size > 0 && selectedIds.size < sources.length;

  const handleSelectAll = () => {
    if (allSelected) {
      onClearSelection();
    } else {
      onSelectAll(sources.map((s) => s.id));
    }
  };

  return (
    <div className="overflow-x-auto rounded-xl border border-white/5 bg-white/[0.02]">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            {/* Select all checkbox */}
            <th className="px-4 py-3 w-12">
              <button
                onClick={handleSelectAll}
                className={cn(
                  "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors",
                  allSelected
                    ? "bg-app-accent border-app-accent"
                    : someSelected
                      ? "bg-app-accent/50 border-app-accent"
                      : "border-white/20 hover:border-white/40"
                )}
              >
                {(allSelected || someSelected) && <Check className="w-3 h-3 text-black" />}
              </button>
            </th>

            {/* Column headers */}
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider",
                  col.className,
                  col.sortable && "cursor-pointer hover:text-white/80 select-none"
                )}
                onClick={() => col.sortable && handleSort(col.key)}
              >
                <div className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && sortColumn === col.key && (
                    sortDirection === "asc" ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )
                  )}
                </div>
              </th>
            ))}

            {/* Actions header */}
            <th className="px-4 py-3 w-32 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-white/5">
          {sortedSources.map((source) => (
            <tr
              key={source.id}
              className={cn(
                "transition-colors",
                selectedIds.has(source.id)
                  ? "bg-app-accent/5"
                  : "hover:bg-white/5",
                source.isPaused && "opacity-60"
              )}
            >
              {/* Checkbox */}
              <td className="px-4 py-3">
                <button
                  onClick={() => onSelect(source.id)}
                  className={cn(
                    "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors",
                    selectedIds.has(source.id)
                      ? "bg-app-accent border-app-accent"
                      : "border-white/20 hover:border-white/40"
                  )}
                >
                  {selectedIds.has(source.id) && <Check className="w-3 h-3 text-black" />}
                </button>
              </td>

              {/* Name */}
              <td className="px-4 py-3">
                <button
                  onClick={() => onViewFeed(source.id)}
                  className="flex items-center gap-3 text-left hover:opacity-80"
                >
                  <div
                    className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                      getSourceTypeColor(source.sourceType)
                    )}
                  >
                    {getSourceIcon(source.sourceType)}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white truncate">
                        {source.name}
                      </span>
                      {source.isPaused && (
                        <span className="text-[9px] font-bold text-amber-400 uppercase tracking-wider px-1.5 py-0.5 bg-amber-500/20 rounded flex-shrink-0">
                          Paused
                        </span>
                      )}
                    </div>
                    {source.description && (
                      <span className="text-xs text-white/40 truncate block max-w-xs">
                        {source.description}
                      </span>
                    )}
                  </div>
                </button>
              </td>

              {/* Type */}
              <td className="px-4 py-3">
                <span className="text-xs text-white/60">{source.sourceType}</span>
              </td>

              {/* Group */}
              <td className="px-4 py-3">
                <span className="text-xs text-white/50 truncate block">
                  {source.group || "—"}
                </span>
              </td>

              {/* Posts/mo */}
              <td className="px-4 py-3 text-right">
                <span className="text-xs text-white/60 tabular-nums">
                  {source.storiesPerMonth}
                </span>
              </td>

              {/* Health */}
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className={cn("w-2 h-2 rounded-full", getHealthColor(source.health))} />
                  <span className="text-xs text-white/40 capitalize">{source.health}</span>
                </div>
              </td>

              {/* Last Synced */}
              <td className="px-4 py-3">
                <span className="text-xs text-white/40">
                  {formatLastSynced(source.lastSynced)}
                </span>
              </td>

              {/* Actions */}
              <td className="px-4 py-3">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => onViewFeed(source.id)}
                    title="View in Feed"
                    className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onPause(source.id)}
                    title={source.isPaused ? "Resume" : "Pause"}
                    className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    {source.isPaused ? (
                      <Play className="w-3.5 h-3.5" />
                    ) : (
                      <Pause className="w-3.5 h-3.5" />
                    )}
                  </button>
                  <button
                    onClick={() => onEdit(source)}
                    title="Edit"
                    className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onDelete(source.id)}
                    title="Delete"
                    className="p-1.5 rounded-lg text-white/40 hover:text-red-400 hover:bg-white/10 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Empty state */}
      {sortedSources.length === 0 && (
        <div className="py-12 text-center text-white/40 text-sm">
          No sources found
        </div>
      )}
    </div>
  );
}
