"use client";

import { useInfiniteFeed } from "@/lib/hooks/use-infinite-feed";
import { MasonryGrid } from "@/components/feed/MasonryGrid";
import { FeedItem } from "@/lib/types/feed";
import { Loader2 } from "lucide-react";

export default function FeedPage() {
  const { items, isLoading, hasNextPage, loadMore } = useInfiniteFeed(20);

  const handleItemClick = (item: FeedItem) => {
    // TODO: Open lightbox or navigate to detail view
    console.log("Clicked item:", item.id);
  };

  // Initial loading state
  if (isLoading && items.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-app-muted gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-app-accent" />
        <p className="text-sm font-medium animate-pulse">Loading your feed...</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-app-bg">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-app-bg/80 backdrop-blur-md border-b border-app-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-app-text">Bunny Feed</h1>
          <div className="flex items-center gap-2 text-sm text-app-muted">
            <span>{items.length} items</span>
          </div>
        </div>
      </header>

      {/* Feed */}
      <MasonryGrid
        items={items}
        isLoading={isLoading}
        hasNextPage={hasNextPage}
        onLoadMore={loadMore}
        onItemClick={handleItemClick}
      />
    </main>
  );
}
