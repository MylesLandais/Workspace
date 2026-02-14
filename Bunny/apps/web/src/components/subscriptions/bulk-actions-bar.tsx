"use client";

import { Tag, Pause, Trash2, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface BulkActionsBarProps {
  selectedCount: number;
  onTag: () => void;
  onPause: () => void;
  onDelete: () => void;
  onClear: () => void;
}

export function BulkActionsBar({
  selectedCount,
  onTag,
  onPause,
  onDelete,
  onClear,
}: BulkActionsBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-2 px-4 py-3 rounded-2xl bg-zinc-900/95 border border-white/10 shadow-2xl backdrop-blur-sm">
      <span className="text-xs text-white/60 mr-2">
        {selectedCount} selected
      </span>

      <button
        onClick={onTag}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-app-accent/20 text-app-accent hover:bg-app-accent/30 transition-colors"
      >
        <Tag className="w-3.5 h-3.5" />
        Tag
      </button>

      <button
        onClick={onPause}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-white/60 hover:bg-white/10 transition-colors"
      >
        <Pause className="w-3.5 h-3.5" />
        Pause
      </button>

      <button
        onClick={onDelete}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
      >
        <Trash2 className="w-3.5 h-3.5" />
        Delete
      </button>

      <div className="w-px h-5 bg-white/10 mx-1" />

      <button
        onClick={onClear}
        className="p-1.5 rounded-lg text-white/40 hover:text-white/60 hover:bg-white/10 transition-colors"
        title="Clear selection"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
