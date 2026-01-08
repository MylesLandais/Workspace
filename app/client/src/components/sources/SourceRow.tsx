"use client";

import type { Source, SourceType as ST } from "@/lib/types/sources";
import { SourceIcon } from "./SourceIcon";
import { SourceActions } from "./SourceActions";

interface SourceRowProps {
  source: Source;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  onPause: (id: string) => void;
  onMove: (id: string) => void;
  onDelete: (id: string) => void;
}

function getSourceDisplayName(source: Source): string {
  if (source.subredditName) {
    return `r/${source.subredditName}`;
  }
  if (source.twitterHandle) {
    return `@${source.twitterHandle}`;
  }
  if (source.youtubeHandle) {
    return source.youtubeHandle.startsWith("@")
      ? source.youtubeHandle
      : `@${source.youtubeHandle}`;
  }
  if (source.instagramHandle) {
    return `@${source.instagramHandle}`;
  }
  if (source.tiktokHandle) {
    return `@${source.tiktokHandle}`;
  }
  return source.name;
}

export function SourceRow({
  source,
  isSelected,
  onSelect,
  onPause,
  onMove,
  onDelete,
}: SourceRowProps) {
  return (
    <tr className={`border-b border-white/5 hover:bg-white/[0.02] transition-colors ${source.isPaused ? "opacity-50" : ""}`}>
      <td className="py-3 px-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => onSelect(source.id, e.target.checked)}
          className="w-4 h-4 rounded border-white/20 bg-zinc-900 text-app-accent focus:ring-app-accent/50"
        />
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <SourceIcon
            sourceType={source.sourceType as ST}
            iconUrl={source.iconUrl}
            size="md"
          />
          <div>
            <div className="text-sm font-medium text-app-text">
              {getSourceDisplayName(source)}
            </div>
            {source.description && (
              <div className="text-xs text-app-muted truncate max-w-xs">
                {source.description}
              </div>
            )}
          </div>
        </div>
      </td>
      <td className="py-3 px-4 text-center">
        <span className="text-sm text-app-muted">{source.storiesPerMonth}</span>
      </td>
      <td className="py-3 px-4 text-center">
        <span className="text-sm text-app-muted">{source.readsPerMonth}</span>
      </td>
      <td className="py-3 px-4">
        <SourceActions
          source={source}
          onPause={onPause}
          onMove={onMove}
          onDelete={onDelete}
        />
      </td>
    </tr>
  );
}
