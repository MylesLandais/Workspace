/**
 * FeedGrid - Responsive masonry grid for feed items
 *
 * Displays media items in a responsive grid layout with:
 * - Proper aspect ratio handling
 * - Lazy loading images
 * - Infinite scroll support
 * - Filter integration
 */

import React, { useRef, useEffect, useCallback } from 'react';
import { useFeed, FeedFilters, Media, getImageUrl, getAspectRatio } from '../hooks/useFeed';
import { FeedItem } from './FeedItem';

interface FeedGridProps {
  filters?: Partial<FeedFilters>;
  limit?: number;
  columns?: number;
  gap?: number;
  className?: string;
  onItemClick?: (item: Media) => void;
}

/**
 * Responsive feed grid with infinite scroll
 *
 * @example
 * ```tsx
 * <FeedGrid
 *   filters={{ sources: ['r/unixporn'] }}
 *   limit={20}
 *   onItemClick={(item) => console.log('Clicked:', item.title)}
 * />
 * ```
 */
export function FeedGrid({
  filters,
  limit = 20,
  columns = 4,
  gap = 16,
  className = '',
  onItemClick,
}: FeedGridProps) {
  const { items, isLoading, isLoadingMore, hasMore, loadMore, isEmpty, error } =
    useFeed({ filters, limit });

  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Intersection observer for infinite scroll
  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && hasMore && !isLoadingMore) {
        loadMore();
      }
    },
    [hasMore, isLoadingMore, loadMore]
  );

  useEffect(() => {
    const observer = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: '200px',
      threshold: 0,
    });

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [handleObserver]);

  // Loading state
  if (isLoading) {
    return (
      <div className={`grid gap-4 ${className}`} style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: limit }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-gray-700 rounded-lg" style={{ aspectRatio: '1' }} />
            <div className="mt-2 h-4 bg-gray-700 rounded w-3/4" />
            <div className="mt-1 h-3 bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`bg-red-900/20 border border-red-500 rounded-lg p-4 ${className}`}>
        <h3 className="text-red-400 font-medium">Failed to load feed</h3>
        <p className="text-red-300 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  // Empty state
  if (isEmpty) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="text-gray-500 text-lg">No items found</div>
        <p className="text-gray-600 text-sm mt-2">
          Try adjusting your filters or adding more sources
        </p>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Grid */}
      <div
        className="grid"
        style={{
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap: `${gap}px`,
        }}
      >
        {items.map((item) => (
          <FeedItem
            key={item.id}
            item={item}
            onClick={onItemClick ? () => onItemClick(item) : undefined}
          />
        ))}
      </div>

      {/* Infinite scroll trigger */}
      <div ref={loadMoreRef} className="h-4" />

      {/* Loading more indicator */}
      {isLoadingMore && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-600 border-t-teal-400" />
        </div>
      )}

      {/* End of feed */}
      {!hasMore && items.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          End of feed
        </div>
      )}
    </div>
  );
}

/**
 * Masonry variant using CSS columns
 */
export function FeedMasonry({
  filters,
  limit = 20,
  columns = 4,
  gap = 16,
  className = '',
  onItemClick,
}: FeedGridProps) {
  const { items, isLoading, isLoadingMore, hasMore, loadMore, isEmpty, error } =
    useFeed({ filters, limit });

  const loadMoreRef = useRef<HTMLDivElement>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && hasMore && !isLoadingMore) {
        loadMore();
      }
    },
    [hasMore, isLoadingMore, loadMore]
  );

  useEffect(() => {
    const observer = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: '200px',
      threshold: 0,
    });

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [handleObserver]);

  if (isLoading) {
    return (
      <div className={`columns-${columns} gap-4 ${className}`}>
        {Array.from({ length: limit }).map((_, i) => (
          <div key={i} className="animate-pulse mb-4 break-inside-avoid">
            <div
              className="bg-gray-700 rounded-lg"
              style={{ aspectRatio: Math.random() > 0.5 ? '3/4' : '4/3' }}
            />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-900/20 border border-red-500 rounded-lg p-4 ${className}`}>
        <h3 className="text-red-400 font-medium">Failed to load feed</h3>
        <p className="text-red-300 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="text-gray-500 text-lg">No items found</div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div
        style={{
          columnCount: columns,
          columnGap: `${gap}px`,
        }}
      >
        {items.map((item) => (
          <div key={item.id} className="mb-4 break-inside-avoid">
            <FeedItem
              item={item}
              onClick={onItemClick ? () => onItemClick(item) : undefined}
              showAspectRatio
            />
          </div>
        ))}
      </div>

      <div ref={loadMoreRef} className="h-4" />

      {isLoadingMore && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-600 border-t-teal-400" />
        </div>
      )}

      {!hasMore && items.length > 0 && (
        <div className="text-center py-8 text-gray-500">End of feed</div>
      )}
    </div>
  );
}

export default FeedGrid;
