"use client";

import {
  useState,
  useRef,
  useEffect,
  useCallback,
  useMemo,
  useId,
} from "react";
import { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { FeedItem } from "./FeedItem";
import { InfiniteScrollSentinel } from "./InfiniteScrollSentinel";
import { Loader2 } from "lucide-react";
import { useMasonryLayout } from "@/hooks/feed/useMasonryLayout";
import { useMediaQuery } from "@/hooks/feed/useMediaQuery";
import { startSpan, endSpan, addSpanEvent } from "@/lib/tracing/tracer";

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
  const [measuredHeights, setMeasuredHeights] = useState<
    Record<string, number>
  >({});
  const componentId = useId();

  // Breakpoints mapping
  const isTablet = useMediaQuery("(min-width: 640px)");
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const isWide = useMediaQuery("(min-width: 1440px)");
  const isUltra = useMediaQuery("(min-width: 1920px)");

  let columnCount = 1;
  let gap = 12;
  let breakpoint = "mobile";

  if (isUltra) {
    columnCount = 5;
    gap = 24;
    breakpoint = "ultra";
  } else if (isWide) {
    columnCount = 4;
    gap = 24;
    breakpoint = "wide";
  } else if (isDesktop) {
    columnCount = 3;
    gap = 20;
    breakpoint = "desktop";
  } else if (isTablet) {
    columnCount = 2;
    gap = 16;
    breakpoint = "tablet";
  }

  // Handle container resizing for width calculations
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeSpan = startSpan(`feed.masonry.${componentId}.containerResize`);
    let resizeCount = 0;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        resizeCount++;
        setContainerWidth(entry.contentRect.width);

        if (resizeCount <= 5) {
          addSpanEvent(resizeSpan, "container_resize", {
            resizeNumber: resizeCount,
            width: entry.contentRect.width,
            height: entry.contentRect.height,
          });
        }
      }
    });

    resizeObserver.observe(containerRef.current);

    const initialWidth = containerRef.current.clientWidth;
    setContainerWidth(initialWidth);

    addSpanEvent(resizeSpan, "container_initial_size", {
      width: initialWidth,
    });

    return () => {
      addSpanEvent(resizeSpan, "container_resize_cleanup", {
        totalResizes: resizeCount,
        finalWidth: containerWidth,
      });
      endSpan(resizeSpan);
      resizeObserver.disconnect();
    };
  }, [componentId, containerWidth]);

  const handleHeightMeasured = useCallback(
    (id: string, height: number) => {
      setMeasuredHeights((prev) => {
        if (prev[id] === height) return prev;

        const measureSpan = startSpan(
          `feed.masonry.${componentId}.heightMeasured`,
        );
        addSpanEvent(measureSpan, "height_measured", {
          itemId: id,
          height,
          previousHeight: prev[id] || 0,
          hasChanged: prev[id] !== height ? 1 : 0,
        });
        endSpan(measureSpan);

        return { ...prev, [id]: height };
      });
    },
    [componentId],
  );

  const columnWidth =
    containerWidth > 0
      ? (containerWidth - (columnCount - 1) * gap) / columnCount
      : 300;

  const layoutCalcStart = performance.now();
  const { itemPositions, containerHeight } = useMasonryLayout(
    items,
    columnCount,
    columnWidth,
    gap,
    measuredHeights,
  );
  const layoutCalcDuration = performance.now() - layoutCalcStart;

  useEffect(() => {
    const layoutSpan = startSpan(
      `feed.masonry.${componentId}.layoutCalculated`,
    );
    addSpanEvent(layoutSpan, "layout_calculation", {
      itemCount: items.length,
      columnCount,
      columnWidth,
      gap,
      containerHeight,
      calcDurationMs: Math.round(layoutCalcDuration),
      measuredHeightCount: Object.keys(measuredHeights).length,
      breakpoint,
    });

    const measuredCount = Object.keys(measuredHeights).length;
    if (items.length > 0) {
      const coveragePercent = Math.round((measuredCount / items.length) * 100);
      addSpanEvent(layoutSpan, "height_measurement_coverage", {
        measured: measuredCount,
        total: items.length,
        coveragePercent,
      });
    }

    endSpan(layoutSpan);
  }, [
    itemPositions,
    containerHeight,
    items.length,
    columnCount,
    columnWidth,
    gap,
    measuredHeights,
    breakpoint,
    componentId,
    layoutCalcDuration,
  ]);

  // Handle empty state during initial load
  const displayItems = useMemo(() => {
    if (items.length === 0 && isLoading) {
      // Return 12 placeholder items to fill initial view
      return Array.from({ length: 12 }).map(
        (_, i) =>
          ({
            id: `placeholder-${i}`,
            type: MediaType.IMAGE,
            caption: "",
            author: { name: "", handle: "" },
            source: "",
            timestamp: new Date().toISOString(),
            aspectRatio: i % 2 === 0 ? "aspect-[3/4]" : "aspect-[16/9]",
            width: 800,
            height: i % 2 === 0 ? 1066 : 450,
            likes: 0,
            mediaUrl: "",
            isPlaceholder: true,
          }) as FeedItemType,
      );
    }
    return items;
  }, [items, isLoading]);

  const handleItemClick = useCallback(
    (item: FeedItemType) => {
      onItemClick?.(item);
    },
    [onItemClick],
  );

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
