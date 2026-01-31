"use client";

import { useState, useRef, useEffect } from "react";
import {
  Search,
  Plus,
  Upload,
  Download,
  LayoutGrid,
  List,
  Table2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useSubscriptionsStore,
  type SubscriptionsViewMode,
} from "@/lib/store/subscriptions-store";

interface SubscriptionsHeaderProps {
  sourceCount: number;
  onAddSource: () => void;
  onImportOPML: () => void;
  onExportOPML: () => void;
}

const viewModes: {
  mode: SubscriptionsViewMode;
  icon: typeof LayoutGrid;
  label: string;
}[] = [
  { mode: "masonry", icon: LayoutGrid, label: "Grid" },
  { mode: "list", icon: List, label: "List" },
  { mode: "table", icon: Table2, label: "Table" },
];

export function SubscriptionsHeader({
  sourceCount,
  onAddSource,
  onImportOPML,
  onExportOPML,
}: SubscriptionsHeaderProps) {
  const { viewMode, setViewMode, searchQuery, setSearchQuery } =
    useSubscriptionsStore();
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Handle keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-app-bg/60 backdrop-blur-2xl border-b border-white/5">
      <div className="px-6 py-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          {/* Title and count */}
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-tight text-white">
              Subscriptions
            </h1>
            <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-white/5 text-white/60 border border-white/5">
              {sourceCount} sources
            </span>
          </div>

          {/* Search and actions */}
          <div className="flex items-center gap-3">
            {/* Search bar */}
            <div
              className={cn(
                "relative flex items-center rounded-xl border transition-all duration-200",
                isSearchFocused
                  ? "bg-white/10 border-white/20 ring-2 ring-app-accent/20"
                  : "bg-white/5 border-white/5 hover:border-white/10",
              )}
            >
              <Search className="w-4 h-4 text-white/40 ml-3" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search sources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                className="w-48 md:w-64 bg-transparent px-3 py-2 text-sm text-white placeholder:text-white/40 focus:outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="p-1 mr-2 rounded-md hover:bg-white/10 text-white/40 hover:text-white/60"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
              <kbd className="hidden md:flex items-center gap-0.5 px-1.5 py-0.5 mr-2 text-[10px] font-medium text-white/30 bg-white/5 rounded border border-white/10">
                <span className="text-xs">⌘</span>K
              </kbd>
            </div>

            {/* View mode toggle */}
            <div className="flex items-center rounded-xl bg-white/5 border border-white/5 p-1">
              {viewModes.map(({ mode, icon: Icon, label }) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  title={label}
                  className={cn(
                    "p-2 rounded-lg transition-colors",
                    viewMode === mode
                      ? "bg-white/10 text-white"
                      : "text-white/40 hover:text-white/60 hover:bg-white/5",
                  )}
                >
                  <Icon className="w-4 h-4" />
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className="h-6 w-px bg-white/10 hidden md:block" />

            {/* Action buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={onImportOPML}
                title="Import OPML"
                className="p-2 rounded-xl bg-white/5 border border-white/5 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              >
                <Upload className="w-4 h-4" />
              </button>
              <button
                onClick={onExportOPML}
                title="Export OPML"
                className="p-2 rounded-xl bg-white/5 border border-white/5 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              >
                <Download className="w-4 h-4" />
              </button>
              <button
                onClick={onAddSource}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-app-accent text-black font-medium text-sm hover:bg-app-accent-hover transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden md:inline">Add Source</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
