"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { FeedItem } from "./FeedItem";
import { InfiniteScrollSentinel } from "./InfiniteScrollSentinel";
import { Loader2 } from "lucide-react";
import { useMasonryLayout } from "@/hooks/feed/useMasonryLayout";
import { useMediaQuery } from "@/hooks/feed/useMediaQuery";

interface MasonryGridProps {
  items: FeedItemType[];
  isLoading: boolean;
  hasNextPage: boolean;
  onLoadMore: () => void;
  onItemClick?: (item: FeedItemType) => void;
}

export function MasonryGrid({
  items,
  isLoading,
  hasNextPage,
  onLoadMore,
  onItemClick,
}: MasonryGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [measuredHeights, setMeasuredHeights] = useState<Record<string, number>>({});

  // Breakpoints mapping
  const isTablet = useMediaQuery('(min-width: 640px)');
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const isWide = useMediaQuery('(min-width: 1440px)');
  const isUltra = useMediaQuery('(min-width: 1920px)');

  let columnCount = 1;
  let gap = 12;

  if (isUltra) {
    columnCount = 5;
    gap = 24;
  } else if (isWide) {
    columnCount = 4;
    gap = 24;
  } else if (isDesktop) {
    columnCount = 3;
    gap = 20;
  } else if (isTablet) {
    columnCount = 2;
    gap = 16;
  }

  // Handle container resizing for width calculations
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    resizeObserver.observe(containerRef.current);
    setContainerWidth(containerRef.current.clientWidth);

    return () => resizeObserver.disconnect();
  }, []);

  const handleHeightMeasured = useCallback((id: string, height: number) => {
    setMeasuredHeights((prev) => {
      if (prev[id] === height) return prev;
      return { ...prev, [id]: height };
    });
  }, []);

  const columnWidth = containerWidth > 0
    ? (containerWidth - (columnCount - 1) * gap) / columnCount
    : 300;

  const { itemPositions, containerHeight } = useMasonryLayout(
    items,
    columnCount,
    columnWidth,
    gap,
    measuredHeights
  );

  // Handle empty state during initial load
  const displayItems = useMemo(() => {
    if (items.length === 0 && isLoading) {
      // Return 12 placeholder items to fill initial view
      return Array.from({ length: 12 }).map((_, i) => ({
        id: `placeholder-${i}`,
        type: MediaType.IMAGE,
        caption: '',
        author: { name: '', handle: '' },
        source: '',
        timestamp: new Date().toISOString(),
        aspectRatio: i % 2 === 0 ? "aspect-[3/4]" : "aspect-[16/9]",
        width: 800,
        height: i % 2 === 0 ? 1066 : 450,
        likes: 0,
        mediaUrl: '',
        isPlaceholder: true,
      } as FeedItemType));
    }
    return items;
  }, [items, isLoading]);

  const handleItemClick = useCallback((item: FeedItemType) => {
    onItemClick?.(item);
  }, [onItemClick]);

  return (
    <div className="p-6">
      <div
        ref={containerRef}
        className="relative w-full mx-auto"
        style={{ height: containerHeight }}
      >
        {displayItems.map((item, index) => {
          const pos = itemPositions[item.id] || { x: 0, y: 0 };
          return (
            <FeedItem
              key={item.id}
              item={item}
              columnWidth={columnWidth}
              x={pos.x}
              y={pos.y}
              onHeightMeasured={handleHeightMeasured}
              onClick={handleItemClick}
              isNew={!item.isPlaceholder && index >= items.length - 20}
              index={index}
              isPlaceholder={item.isPlaceholder}
            />
          );
        })}
      </div>

      {/* Infinite Scroll Sentinel */}
      <div className="relative mt-8">
        <InfiniteScrollSentinel
          onIntersect={onLoadMore}
          enabled={hasNextPage && !isLoading}
        />
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="w-8 h-8 animate-spin text-app-accent" />
        </div>
      )}

      {/* End of Feed */}
      {!hasNextPage && items.length > 0 && (
        <div className="text-center py-12 text-app-muted text-sm font-medium tracking-wide">
          You&apos;ve reached the bottom of the feed
        </div>
      )}
    </div>
  );
}
