"use client";

import { useInfiniteFeed } from "@/lib/hooks/use-infinite-feed";
import { MasonryGrid, MediaLightbox, FeedHeader, FeedLoading } from "@/components/feed";
import { FeedItem } from "@/lib/types/feed";
import { useLightboxStore } from "@/lib/store/lightbox-store";
import { generateMockPostDetails } from "@/lib/mock-data/factory";
import { useSearchStore } from "@/lib/store/search-store";
import { useEffect } from "react";
import { useSession } from "@/lib/auth-client";
import { useRouter } from "next/navigation";

export default function FeedPage() {
  const { filters } = useSearchStore();
  const { items, isLoading, hasNextPage, loadMore } = useInfiniteFeed(20, filters);
  const lightboxStore = useLightboxStore();
  const { data: session, isPending, error } = useSession();
  const router = useRouter();

  // Client-side protection
  useEffect(() => {
    if (!isPending && (!session || error)) {
      console.warn("FeedPage: Auth session missing or error, forcing redirect...");
      router.push("/");
    }
  }, [session, isPending, error, router]);

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
        setTimeout(() => {
          const threadData = generateMockPostDetails(item.redditData!.id, item.redditData!);
          lightboxStore.setRedditThreadData(item.redditData!.id, threadData);
          lightboxStore.setLoadingThread(item.redditData!.id, false);
        }, 500);
      }
    }
  };

  if (isLoading && items.length === 0) {
    return <FeedLoading />;
  }

  return (
    <main className="min-h-screen bg-app-bg">
      <FeedHeader itemCount={items.length} />

      <div className="max-w-[2400px] mx-auto">
        <MasonryGrid
          items={items}
          isLoading={isLoading}
          hasNextPage={hasNextPage}
          onLoadMore={loadMore}
          onItemClick={handleItemClick}
        />
      </div>

      <MediaLightbox />
    </main>
  );
}
