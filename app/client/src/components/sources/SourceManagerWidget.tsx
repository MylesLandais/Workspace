"use client";

import React, { useState, useMemo } from "react";
import { Search, Settings2, Filter, Loader2, RefreshCw } from "lucide-react";
import { useUserSources } from "@/lib/hooks/use-user-sources";
import { SourceChecklistItem } from "./SourceChecklistItem";
import { SourceType } from "@/lib/types/sources";

interface SourceManagerWidgetProps {
  className?: string;
  compact?: boolean;
  title?: string;
}

export function SourceManagerWidget({
  className = "",
  compact = false,
  title = "Source Manager",
}: SourceManagerWidgetProps) {
  const {
    sources,
    isLoading,
    refresh,
    togglePause,
    totalCount,
    activeSources,
  } = useUserSources();

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<SourceType | "ALL">("ALL");

  const filteredSources = useMemo(() => {
    return sources.filter((source) => {
      const matchesSearch =
        source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        source.subredditName?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType =
        filterType === "ALL" || source.sourceType === filterType;

      return matchesSearch && matchesType;
    });
  }, [sources, searchQuery, filterType]);

  const handleToggle = async (id: string, enabled: boolean) => {
    // Note: enabled=true means we want it active, so we toggle pause OFF
    // enabled=false means we want it hidden, so we toggle pause ON
    await togglePause(id);
  };

  if (isLoading && sources.length === 0) {
    return (
      <div
        className={`flex flex-col items-center justify-center p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl ${className}`}
      >
        <Loader2 className="w-6 h-6 animate-spin text-app-accent mb-2" />
        <p className="text-xs text-app-muted uppercase tracking-widest">
          Loading Sources...
        </p>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Settings2 className="w-4 h-4 text-app-muted" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-app-text">
            {title}
          </h3>
          <span className="bg-app-accent/10 text-app-accent text-[10px] px-1.5 py-0.5 rounded-full font-bold">
            {activeSources.length}/{totalCount}
          </span>
        </div>
        <button
          onClick={() => refresh()}
          className="p-1.5 rounded-lg hover:bg-white/5 text-app-muted hover:text-app-text transition-colors"
          title="Refresh Sources"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {/* Search & Filter */}
      {!compact && (
        <div className="p-3 border-b border-white/5 space-y-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-app-muted" />
            <input
              type="text"
              placeholder="Search sources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/5 rounded-lg py-1.5 pl-8 pr-3 text-xs text-app-text placeholder:text-app-muted focus:outline-none focus:ring-1 focus:ring-app-accent/50 transition-all"
            />
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
            <button
              onClick={() => setFilterType("ALL")}
              className={`text-[10px] font-bold uppercase tracking-tighter px-2 py-1 rounded-md transition-colors whitespace-nowrap ${
                filterType === "ALL"
                  ? "bg-app-accent text-black"
                  : "bg-white/5 text-app-muted hover:text-app-text"
              }`}
            >
              All
            </button>
            {Object.values(SourceType).map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type as SourceType)}
                className={`text-[10px] font-bold uppercase tracking-tighter px-2 py-1 rounded-md transition-colors whitespace-nowrap ${
                  filterType === type
                    ? "bg-app-accent text-black"
                    : "bg-white/5 text-app-muted hover:text-app-text"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Source List */}
      <div className="flex-1 overflow-y-auto p-2 min-h-[120px] max-h-[400px] custom-scrollbar">
        {filteredSources.length > 0 ? (
          <div className="space-y-0.5">
            {filteredSources.map((source) => (
              <SourceChecklistItem
                key={source.id}
                source={source}
                isSelected={!source.isPaused}
                onToggle={handleToggle}
                compact={compact}
              />
            ))}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center">
            <Filter className="w-8 h-8 text-white/5 mb-2" />
            <p className="text-xs text-app-muted">
              No sources match your criteria
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-white/5 bg-white/[0.02] flex justify-between items-center">
        <span className="text-[10px] font-bold text-app-muted uppercase tracking-tight">
          {activeSources.length} Active Feeds
        </span>
        <a
          href="/sources/manage"
          className="text-[10px] font-bold text-app-accent hover:underline uppercase tracking-tight"
        >
          Manage All →
        </a>
      </div>
    </div>
  );
}
