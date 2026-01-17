"use client";

import React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { SourceIcon } from "./SourceIcon";
import { Source } from "@/lib/types/sources";
import { SourceType } from "@/lib/types/sources";

interface SourceChecklistItemProps {
  source: Source;
  isSelected: boolean;
  onToggle: (id: string, enabled: boolean) => void;
  compact?: boolean;
}

export function SourceChecklistItem({
  source,
  isSelected,
  onToggle,
  compact = false,
}: SourceChecklistItemProps) {
  const getDisplayName = () => {
    if (source.subredditName) return `r/${source.subredditName}`;
    if (source.twitterHandle) return `@${source.twitterHandle}`;
    if (source.youtubeHandle)
      return source.youtubeHandle.startsWith("@")
        ? source.youtubeHandle
        : `@${source.youtubeHandle}`;
    return source.name;
  };

  return (
    <div
      className={`flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors group ${
        source.isPaused ? "opacity-50" : ""
      }`}
    >
      <Checkbox
        id={`source-${source.id}`}
        checked={!source.isPaused}
        onCheckedChange={(checked) => onToggle(source.id, !!checked)}
        className="border-white/20 data-[state=checked]:bg-app-accent data-[state=checked]:border-app-accent"
      />

      <div className="flex items-center gap-2 flex-1 min-w-0">
        <SourceIcon
          sourceType={source.sourceType as SourceType}
          iconUrl={source.iconUrl}
          size={compact ? "sm" : "md"}
        />
        <label
          htmlFor={`source-${source.id}`}
          className={`text-sm font-medium truncate cursor-pointer select-none ${
            source.isPaused ? "text-app-muted line-through" : "text-app-text"
          }`}
        >
          {getDisplayName()}
        </label>
      </div>

      {!compact && source.mediaCount > 0 && (
        <span className="text-[10px] font-bold text-app-muted bg-white/5 px-1.5 py-0.5 rounded uppercase tracking-wider">
          {source.mediaCount}
        </span>
      )}
    </div>
  );
}
