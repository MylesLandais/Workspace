"use client";

import { useRef } from "react";
import { Tag, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { TagChip } from "./tag-chip";
import type { TagCount } from "@/lib/hooks/use-sources";

interface TagFilterBarProps {
  allTags: TagCount[];
  activeTags: string[];
  onToggleTag: (tag: string) => void;
  onClearTags: () => void;
}

export function TagFilterBar({
  allTags,
  activeTags,
  onToggleTag,
  onClearTags,
}: TagFilterBarProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  if (allTags.length === 0) return null;

  return (
    <div className="flex items-center gap-3 px-6 py-3 border-b border-white/5">
      <div className="flex items-center gap-1.5 text-white/40 flex-shrink-0">
        <Tag className="w-3.5 h-3.5" />
        <span className="text-xs font-medium">Tags</span>
      </div>

      <div
        ref={scrollRef}
        className="flex items-center gap-1.5 overflow-x-auto scrollbar-none flex-1 min-w-0"
      >
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

      {activeTags.length > 0 && (
        <button
          onClick={onClearTags}
          className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-white/40 hover:text-white/60 hover:bg-white/10 transition-colors flex-shrink-0"
        >
          <X className="w-3 h-3" />
          Clear
        </button>
      )}
    </div>
  );
}
