"use client";

import { Tag } from "lucide-react";
import { cn } from "@/lib/utils";
import { TagChip } from "./tag-chip";
import type { TagCount } from "@/lib/hooks/use-sources";

interface TagManagementPanelProps {
  allTags: TagCount[];
  activeTags: string[];
  onToggleTag: (tag: string) => void;
  onClearTags: () => void;
}

export function TagManagementPanel({
  allTags,
  activeTags,
  onToggleTag,
  onClearTags,
}: TagManagementPanelProps) {
  if (allTags.length === 0) return null;

  const totalSources = allTags.reduce((sum, t) => sum + t.count, 0);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-white/40" />
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">
            Tags
          </h3>
          <span className="text-[10px] text-white/30">
            {allTags.length} tags
          </span>
        </div>
        {activeTags.length > 0 && (
          <button
            onClick={onClearTags}
            className="text-[10px] text-white/40 hover:text-white/60 transition-colors"
          >
            Clear filter
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {allTags.map(({ tag, count }) => (
          <TagChip
            key={tag}
            tag={tag}
            count={count}
            isActive={activeTags.includes(tag)}
            onClick={() => onToggleTag(tag)}
            size="sm"
          />
        ))}
      </div>
    </div>
  );
}
