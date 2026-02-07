"use client";

import { LayoutGrid, List, Table } from "lucide-react";
import type { ViewMode } from "@/lib/types/sources";

interface SourceViewToggleProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

export function SourceViewToggle({
  viewMode,
  onViewModeChange,
}: SourceViewToggleProps) {
  return (
    <div className="flex items-center gap-1 bg-zinc-900/50 border border-white/5 rounded-lg p-1">
      <button
        onClick={() => onViewModeChange("grid")}
        className={`p-1.5 rounded transition-colors ${
          viewMode === "grid"
            ? "bg-white/10 text-app-text"
            : "text-app-muted hover:text-app-text"
        }`}
        title="Grid view"
      >
        <LayoutGrid className="w-4 h-4" />
      </button>
      <button
        onClick={() => onViewModeChange("list")}
        className={`p-1.5 rounded transition-colors ${
          viewMode === "list"
            ? "bg-white/10 text-app-text"
            : "text-app-muted hover:text-app-text"
        }`}
        title="List view"
      >
        <List className="w-4 h-4" />
      </button>
      <button
        onClick={() => onViewModeChange("table")}
        className={`p-1.5 rounded transition-colors ${
          viewMode === "table"
            ? "bg-white/10 text-app-text"
            : "text-app-muted hover:text-app-text"
        }`}
        title="Table view"
      >
        <Table className="w-4 h-4" />
      </button>
    </div>
  );
}
