"use client";

import { useState, useRef, useEffect } from "react";
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
  MoreHorizontal,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";

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

interface SourceListItemProps {
  source: Source;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onPause: (id: string) => void;
  onEdit: (source: Source) => void;
  onDelete: (id: string) => void;
  onViewFeed: (id: string) => void;
  onFilterByTag?: (tag: string) => void;
}

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
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;
  return date.toLocaleDateString();
}

function getSourceHandle(source: Source): string | null {
  if (source.subredditName) return `r/${source.subredditName}`;
  if (source.youtubeHandle) return `@${source.youtubeHandle}`;
  if (source.twitterHandle) return `@${source.twitterHandle}`;
  if (source.instagramHandle) return `@${source.instagramHandle}`;
  if (source.tiktokHandle) return `@${source.tiktokHandle}`;
  return null;
}

export function SourceListItem({
  source,
  isSelected,
  onSelect,
  onPause,
  onEdit,
  onDelete,
  onViewFeed,
  onFilterByTag,
}: SourceListItemProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    if (!menuOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  const handle = getSourceHandle(source);

  return (
    <div
      className={cn(
        "flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-150",
        "border",
        isSelected
          ? "bg-app-accent/10 border-app-accent/30"
          : "bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10",
        source.isPaused && "opacity-60",
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Checkbox */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onSelect(source.id);
        }}
        className={cn(
          "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors flex-shrink-0",
          isSelected
            ? "bg-app-accent border-app-accent"
            : "border-white/20 hover:border-white/40",
        )}
      >
        {isSelected && <Check className="w-3 h-3 text-black" />}
      </button>

      {/* Type icon */}
      <div
        className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
          getSourceTypeColor(source.sourceType),
        )}
      >
        {getSourceIcon(source.sourceType)}
      </div>

      {/* Name and handle */}
      <div
        className="flex-1 min-w-0 cursor-pointer"
        onClick={() => onViewFeed(source.id)}
      >
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
        <div className="flex items-center gap-1.5">
          {handle && (
            <span className="text-xs text-white/40 truncate">{handle}</span>
          )}
          {source.tags && source.tags.length > 0 && (
            <div className="hidden sm:flex items-center gap-1">
              {source.tags.slice(0, 2).map((tag) => (
                <button
                  key={tag}
                  onClick={(e) => {
                    e.stopPropagation();
                    onFilterByTag?.(tag);
                  }}
                  className="px-1.5 py-0.5 rounded-full text-[10px] bg-white/5 border border-white/10 text-white/40 hover:text-white/60 transition-colors"
                >
                  {tag}
                </button>
              ))}
              {source.tags.length > 2 && (
                <span className="text-[10px] text-white/30">
                  +{source.tags.length - 2}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Group */}
      <div className="hidden md:block w-28 flex-shrink-0">
        <span className="text-xs text-white/40 truncate">
          {source.group || "—"}
        </span>
      </div>

      {/* Stats */}
      <div className="hidden lg:flex items-center gap-4 flex-shrink-0">
        <div className="w-16 text-right">
          <span className="text-xs text-white/40">
            {source.storiesPerMonth}/mo
          </span>
        </div>
        <div className="w-16 text-right">
          <span className="text-xs text-white/40">
            {formatLastSynced(source.lastSynced)}
          </span>
        </div>
      </div>

      {/* Health */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <div
          className={cn("w-2 h-2 rounded-full", getHealthColor(source.health))}
        />
      </div>

      {/* Actions */}
      <div className="relative flex-shrink-0" ref={menuRef}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpen(!menuOpen);
          }}
          className={cn(
            "p-1.5 rounded-lg transition-colors",
            menuOpen || isHovered
              ? "bg-white/10 text-white/60"
              : "text-white/30 hover:text-white/60",
          )}
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-full mt-1 w-40 py-1 bg-zinc-900 border border-white/10 rounded-lg shadow-xl z-50">
            <button
              onClick={() => {
                onViewFeed(source.id);
                setMenuOpen(false);
              }}
              className="w-full px-3 py-2 text-sm text-left text-white/80 hover:bg-white/10 flex items-center gap-2"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View in Feed
            </button>
            <button
              onClick={() => {
                onEdit(source);
                setMenuOpen(false);
              }}
              className="w-full px-3 py-2 text-sm text-left text-white/80 hover:bg-white/10 flex items-center gap-2"
            >
              <Pencil className="w-3.5 h-3.5" />
              Edit
            </button>
            <button
              onClick={() => {
                onPause(source.id);
                setMenuOpen(false);
              }}
              className="w-full px-3 py-2 text-sm text-left text-white/80 hover:bg-white/10 flex items-center gap-2"
            >
              {source.isPaused ? (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="w-3.5 h-3.5" />
                  Pause
                </>
              )}
            </button>
            <div className="h-px bg-white/10 my-1" />
            <button
              onClick={() => {
                onDelete(source.id);
                setMenuOpen(false);
              }}
              className="w-full px-3 py-2 text-sm text-left text-red-400 hover:bg-white/10 flex items-center gap-2"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
