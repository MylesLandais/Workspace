"use client";

import { Upload } from "lucide-react";

interface SourceManagementHeaderProps {
  totalCount: number;
  inactiveCount: number;
  onImportClick: () => void;
}

export function SourceManagementHeader({
  totalCount,
  inactiveCount,
  onImportClick,
}: SourceManagementHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-app-text">Source Management</h1>
        <p className="text-sm text-app-muted mt-1">
          Following {totalCount} feeds
          {inactiveCount > 0 && (
            <span className="text-yellow-500">
              {" "}
              with {inactiveCount} inactive
            </span>
          )}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={onImportClick}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-900/50 border border-white/10 rounded-xl text-sm font-medium text-app-text hover:bg-zinc-800 transition-colors"
        >
          <Upload className="w-4 h-4" />
          Import OPML
        </button>
      </div>
    </div>
  );
}
