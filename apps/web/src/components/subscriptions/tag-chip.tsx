"use client";

import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface TagChipProps {
  tag: string;
  count?: number;
  isActive?: boolean;
  removable?: boolean;
  onClick?: () => void;
  onRemove?: () => void;
  size?: "sm" | "md";
}

export function TagChip({
  tag,
  count,
  isActive = false,
  removable = false,
  onClick,
  onRemove,
  size = "sm",
}: TagChipProps) {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border transition-colors",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-3 py-1 text-xs",
        isActive
          ? "bg-app-accent/20 border-app-accent/40 text-app-accent"
          : "bg-white/5 border-white/10 text-white/60 hover:bg-white/10 hover:border-white/20",
        onClick && "cursor-pointer",
        !onClick && "cursor-default",
      )}
    >
      <span className="font-medium truncate max-w-[120px]">{tag}</span>
      {count !== undefined && (
        <span
          className={cn(
            "tabular-nums",
            isActive ? "text-app-accent/70" : "text-white/30",
          )}
        >
          {count}
        </span>
      )}
      {removable && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 p-0.5 rounded-full hover:bg-white/20 transition-colors"
        >
          <X className="w-2.5 h-2.5" />
        </button>
      )}
    </button>
  );
}
