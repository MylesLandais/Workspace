"use client";

import { FeedItem as FeedItemType } from "@/lib/types/feed";
import { FeedItem } from "./FeedItem";
import { InfiniteScrollSentinel } from "./InfiniteScrollSentinel";
import { Loader2 } from "lucide-react";

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
  return (
    <div className="p-6">
      <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-6 mx-auto max-w-7xl">
        {items.map((item) => (
          <FeedItem key={item.id} item={item} onClick={onItemClick} />
        ))}
      </div>

      {/* Infinite Scroll Sentinel */}
      <InfiniteScrollSentinel
        onIntersect={onLoadMore}
        enabled={hasNextPage && !isLoading}
      />

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="w-8 h-8 animate-spin text-app-accent" />
        </div>
      )}

      {/* End of Feed */}
      {!hasNextPage && items.length > 0 && (
        <div className="text-center py-8 text-app-muted text-sm">
          You&apos;ve reached the end of the feed
        </div>
      )}
    </div>
  );
}
