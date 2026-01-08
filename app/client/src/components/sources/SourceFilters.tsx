"use client";

import { Search, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import type { FeedGroup, SourceFilters as Filters, ActivityFilter } from "@/lib/types/sources";

interface SourceFiltersProps {
  filters: Filters;
  feedGroups: FeedGroup[];
  onFiltersChange: (filters: Filters) => void;
}

export function SourceFilters({
  filters,
  feedGroups,
  onFiltersChange,
}: SourceFiltersProps) {
  const [folderOpen, setFolderOpen] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);
  const folderRef = useRef<HTMLDivElement>(null);
  const activityRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (folderRef.current && !folderRef.current.contains(event.target as Node)) {
        setFolderOpen(false);
      }
      if (activityRef.current && !activityRef.current.contains(event.target as Node)) {
        setActivityOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedGroup = feedGroups.find((g) => g.id === filters.groupId);
  const activityOptions: { value: ActivityFilter | undefined; label: string }[] = [
    { value: undefined, label: "Any" },
    { value: "active", label: "Active" },
    { value: "inactive", label: "Inactive" },
    { value: "paused", label: "Paused" },
  ];
  const selectedActivity = activityOptions.find((a) => a.value === filters.activity);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {/* Folder Dropdown */}
      <div className="relative" ref={folderRef}>
        <label className="block text-xs font-medium text-app-muted uppercase tracking-wider mb-2">
          Folder
        </label>
        <button
          onClick={() => setFolderOpen(!folderOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-sm text-app-text hover:bg-zinc-800 transition-colors"
        >
          <span>{selectedGroup?.name || "All Your Feeds"}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${folderOpen ? "rotate-180" : ""}`} />
        </button>
        {folderOpen && (
          <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-zinc-900 border border-white/10 rounded-xl shadow-xl overflow-hidden">
            <button
              onClick={() => {
                onFiltersChange({ ...filters, groupId: undefined });
                setFolderOpen(false);
              }}
              className={`w-full px-4 py-2 text-sm text-left hover:bg-white/5 ${
                !filters.groupId ? "bg-white/10 text-app-text" : "text-app-muted"
              }`}
            >
              All Your Feeds
            </button>
            {feedGroups.map((group) => (
              <button
                key={group.id}
                onClick={() => {
                  onFiltersChange({ ...filters, groupId: group.id });
                  setFolderOpen(false);
                }}
                className={`w-full px-4 py-2 text-sm text-left hover:bg-white/5 ${
                  filters.groupId === group.id ? "bg-white/10 text-app-text" : "text-app-muted"
                }`}
              >
                {group.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Activity Dropdown */}
      <div className="relative" ref={activityRef}>
        <label className="block text-xs font-medium text-app-muted uppercase tracking-wider mb-2">
          Activity
        </label>
        <button
          onClick={() => setActivityOpen(!activityOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-sm text-app-text hover:bg-zinc-800 transition-colors"
        >
          <span>{selectedActivity?.label || "Any"}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${activityOpen ? "rotate-180" : ""}`} />
        </button>
        {activityOpen && (
          <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-zinc-900 border border-white/10 rounded-xl shadow-xl overflow-hidden">
            {activityOptions.map((option) => (
              <button
                key={option.label}
                onClick={() => {
                  onFiltersChange({ ...filters, activity: option.value });
                  setActivityOpen(false);
                }}
                className={`w-full px-4 py-2 text-sm text-left hover:bg-white/5 ${
                  filters.activity === option.value ? "bg-white/10 text-app-text" : "text-app-muted"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Search Input */}
      <div>
        <label className="block text-xs font-medium text-app-muted uppercase tracking-wider mb-2">
          Feed Name
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted" />
          <input
            type="text"
            placeholder="Filter feeds..."
            value={filters.searchQuery || ""}
            onChange={(e) => onFiltersChange({ ...filters, searchQuery: e.target.value })}
            className="w-full pl-10 pr-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-sm text-app-text placeholder:text-app-muted focus:outline-none focus:ring-2 focus:ring-white/10"
          />
        </div>
      </div>
    </div>
  );
}
