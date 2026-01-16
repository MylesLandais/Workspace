/**
 * SourceList - Source management table
 *
 * Displays and manages content sources with:
 * - Filtering by type, status, and search
 * - Pause/resume controls
 * - Delete functionality
 * - Health status indicators
 */

import React, { useState } from 'react';
import {
  useSources,
  useSourceFilters,
  Source,
  Platform,
  ActivityFilter,
  getPlatformLabel,
  getSourceHandle,
  getHealthColor,
} from '../hooks/useSources';
import { useSourceFilters as useFilters } from '../hooks/useSourceFilters';

interface SourceListProps {
  onSourceClick?: (source: Source) => void;
  className?: string;
}

/**
 * Source management table
 *
 * @example
 * ```tsx
 * <SourceList
 *   onSourceClick={(source) => console.log('Selected:', source.name)}
 * />
 * ```
 */
export function SourceList({ onSourceClick, className = '' }: SourceListProps) {
  const { filters, setSourceType, setActivity, setSearchQuery, reset, hasActiveFilters } =
    useFilters();
  const { sources, isLoading, error, togglePause, deleteSource, refresh } =
    useSources({ filters });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === sources.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(sources.map((s) => s.id)));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteSource(id);
    setDeleteConfirm(null);
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  };

  if (error) {
    return (
      <div className={`bg-red-900/20 border border-red-500 rounded-lg p-4 ${className}`}>
        <h3 className="text-red-400 font-medium">Failed to load sources</h3>
        <p className="text-red-300 text-sm mt-1">{error.message}</p>
        <button
          onClick={refresh}
          className="mt-2 text-sm text-red-400 hover:text-red-300"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-4 items-center">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search sources..."
            value={filters.searchQuery || ''}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-400"
          />
        </div>

        {/* Type filter */}
        <select
          value={filters.sourceType || ''}
          onChange={(e) =>
            setSourceType((e.target.value as Platform) || undefined)
          }
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-400"
        >
          <option value="">All Types</option>
          <option value="REDDIT">Reddit</option>
          <option value="YOUTUBE">YouTube</option>
          <option value="RSS">RSS</option>
          <option value="TWITTER">Twitter</option>
          <option value="INSTAGRAM">Instagram</option>
          <option value="TIKTOK">TikTok</option>
          <option value="IMAGEBOARD">Imageboard</option>
        </select>

        {/* Activity filter */}
        <select
          value={filters.activity || 'ALL'}
          onChange={(e) => setActivity(e.target.value as ActivityFilter)}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-400"
        >
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="PAUSED">Paused</option>
          <option value="INACTIVE">Inactive</option>
        </select>

        {/* Clear filters */}
        {hasActiveFilters && (
          <button
            onClick={reset}
            className="px-3 py-2 text-sm text-gray-400 hover:text-white"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse flex items-center gap-4 p-4 bg-gray-800 rounded-lg">
              <div className="w-8 h-8 bg-gray-700 rounded" />
              <div className="flex-1">
                <div className="h-4 bg-gray-700 rounded w-1/4 mb-2" />
                <div className="h-3 bg-gray-700 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : sources.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>No sources found</p>
          {hasActiveFilters && (
            <button onClick={reset} className="mt-2 text-teal-400 hover:text-teal-300">
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Header */}
          <div className="flex items-center gap-4 px-4 py-2 text-xs text-gray-400 uppercase border-b border-gray-700">
            <div className="w-8">
              <input
                type="checkbox"
                checked={selectedIds.size === sources.length && sources.length > 0}
                onChange={handleSelectAll}
                className="rounded bg-gray-700 border-gray-600"
              />
            </div>
            <div className="flex-1">Source</div>
            <div className="w-24">Type</div>
            <div className="w-20 text-right">Media</div>
            <div className="w-24 text-center">Status</div>
            <div className="w-24 text-center">Health</div>
            <div className="w-32">Actions</div>
          </div>

          {/* Rows */}
          <div className="divide-y divide-gray-700">
            {sources.map((source) => (
              <SourceRow
                key={source.id}
                source={source}
                selected={selectedIds.has(source.id)}
                onSelect={() => handleToggleSelect(source.id)}
                onClick={() => onSourceClick?.(source)}
                onTogglePause={() => togglePause(source.id)}
                onDelete={() => setDeleteConfirm(source.id)}
                showDeleteConfirm={deleteConfirm === source.id}
                onConfirmDelete={() => handleDelete(source.id)}
                onCancelDelete={() => setDeleteConfirm(null)}
              />
            ))}
          </div>
        </>
      )}

      {/* Summary */}
      {sources.length > 0 && (
        <div className="mt-4 flex justify-between text-sm text-gray-400">
          <span>
            {sources.length} source{sources.length !== 1 ? 's' : ''}
            {selectedIds.size > 0 && ` (${selectedIds.size} selected)`}
          </span>
          <span>
            {sources.reduce((acc, s) => acc + s.mediaCount, 0).toLocaleString()} total media
          </span>
        </div>
      )}
    </div>
  );
}

interface SourceRowProps {
  source: Source;
  selected: boolean;
  onSelect: () => void;
  onClick?: () => void;
  onTogglePause: () => void;
  onDelete: () => void;
  showDeleteConfirm: boolean;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
}

function SourceRow({
  source,
  selected,
  onSelect,
  onClick,
  onTogglePause,
  onDelete,
  showDeleteConfirm,
  onConfirmDelete,
  onCancelDelete,
}: SourceRowProps) {
  return (
    <div
      className={`flex items-center gap-4 px-4 py-3 hover:bg-gray-800/50 transition-colors ${
        selected ? 'bg-gray-800/30' : ''
      }`}
    >
      {/* Checkbox */}
      <div className="w-8">
        <input
          type="checkbox"
          checked={selected}
          onChange={onSelect}
          className="rounded bg-gray-700 border-gray-600"
        />
      </div>

      {/* Name/Icon */}
      <div
        className="flex-1 flex items-center gap-3 cursor-pointer"
        onClick={onClick}
      >
        {source.iconUrl ? (
          <img
            src={source.iconUrl}
            alt=""
            className="w-8 h-8 rounded object-cover bg-gray-700"
          />
        ) : (
          <div className="w-8 h-8 rounded bg-gray-700 flex items-center justify-center text-gray-500 text-xs">
            {source.sourceType.charAt(0)}
          </div>
        )}
        <div>
          <div className="text-white font-medium">{source.name}</div>
          <div className="text-xs text-gray-400">{getSourceHandle(source)}</div>
        </div>
      </div>

      {/* Type */}
      <div className="w-24">
        <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
          {getPlatformLabel(source.sourceType)}
        </span>
      </div>

      {/* Media count */}
      <div className="w-20 text-right text-gray-300">
        {source.mediaCount.toLocaleString()}
      </div>

      {/* Status */}
      <div className="w-24 text-center">
        <span
          className={`text-sm ${
            source.isPaused
              ? 'text-yellow-500'
              : source.isActive
              ? 'text-green-500'
              : 'text-gray-500'
          }`}
        >
          {source.isPaused ? 'Paused' : source.isActive ? 'Active' : 'Inactive'}
        </span>
      </div>

      {/* Health */}
      <div className="w-24 text-center">
        <span className={`text-sm ${getHealthColor(source.health)}`}>
          {source.health}
        </span>
      </div>

      {/* Actions */}
      <div className="w-32 flex gap-2">
        {showDeleteConfirm ? (
          <>
            <button
              onClick={onConfirmDelete}
              className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
            >
              Confirm
            </button>
            <button
              onClick={onCancelDelete}
              className="px-2 py-1 text-xs text-gray-400 hover:text-white"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={onTogglePause}
              className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600"
            >
              {source.isPaused ? 'Resume' : 'Pause'}
            </button>
            <button
              onClick={onDelete}
              className="px-2 py-1 text-xs text-red-400 hover:text-red-300"
            >
              Delete
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default SourceList;
