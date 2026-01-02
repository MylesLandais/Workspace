"use client";

import { useInfiniteFeed } from "@/lib/hooks/use-infinite-feed";
import { MasonryGrid } from "@/components/feed/MasonryGrid";
import { MediaLightbox } from "@/components/feed/MediaLightbox";
import { FeedItem } from "@/lib/types/feed";
import { useLightboxStore } from "@/lib/store/lightbox-store";
import { generateMockPostDetails } from "@/lib/mock-data/factory";
import { Loader2 } from "lucide-react";
import { SearchBar } from "@/components/search/SearchBar";
import { useSearchStore } from "@/lib/store/search-store";
import { useEffect } from "react";

export default function FeedPage() {
  const { filters } = useSearchStore();
  const { items, isLoading, hasNextPage, loadMore } = useInfiniteFeed(100, filters);
  const lightboxStore = useLightboxStore();

  const handleItemClick = (item: FeedItem) => {
    const itemIndex = items.findIndex((i) => i.id === item.id);
    if (itemIndex >= 0) {
      // Calculate slide index for multi-image galleries
      let slideIndex = 0;
      for (let i = 0; i < itemIndex; i++) {
        const galleryUrls = items[i].galleryUrls;
        slideIndex += galleryUrls && galleryUrls.length > 1 ? galleryUrls.length : 1;
      }

      lightboxStore.openLightbox(items, slideIndex);

      // If Reddit post, trigger thread data fetch
      if (item.redditData) {
        lightboxStore.setLoadingThread(item.redditData.id, true);
        // Mock: generate thread data with comments
        // In production, this would call the Reddit API
        setTimeout(() => {
          const threadData = generateMockPostDetails(item.redditData!.id, item.redditData!);
          lightboxStore.setRedditThreadData(item.redditData!.id, threadData);
          lightboxStore.setLoadingThread(item.redditData!.id, false);
        }, 500);
      }
    }
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
      <header className="sticky top-0 z-50 bg-app-bg/60 backdrop-blur-2xl border-b border-white/5 py-4 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-app-accent to-app-accent-hover flex items-center justify-center shadow-lg shadow-app-accent/20">
              <span className="text-xl font-black text-black">B</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-app-text hidden sm:block">Bunny</h1>
          </div>

          <SearchBar />

          <div className="hidden lg:flex items-center gap-4 text-sm text-app-muted font-medium">
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/5">
              {items.length} items discovered
            </span>
          </div>
        </div>
      </header>

      {/* Feed Area */}
      <div className="max-w-[2400px] mx-auto">
        <MasonryGrid
          items={items}
          isLoading={isLoading}
          hasNextPage={hasNextPage}
          onLoadMore={loadMore}
          onItemClick={handleItemClick}
        />
      </div>

      {/* Lightbox */}
      <MediaLightbox />
    </main>
  );
}
