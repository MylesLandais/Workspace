"use client";

import React, { useState, useEffect } from "react";
import { LayoutGrid, RefreshCw } from "lucide-react";
import { FeedItem, MediaType } from "@/lib/types/feed";

interface MasonryWallWidgetProps {
  content: string;
  config?: {
    subreddit?: string;
    limit?: number;
  };
}

const MasonryWallWidget: React.FC<MasonryWallWidgetProps> = ({
  content,
  config,
}) => {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const limit = config?.limit || 100;

  const loadFeed = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const subreddit = config?.subreddit || "unixporn";
      const params = new URLSearchParams({
        subreddit,
        limit: limit.toString(),
      });

      const response = await fetch(`/api/reddit/posts?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.error) {
        throw new Error(result.error);
      }

      const posts = result.posts || [];

      // Filter to only posts with images (use media_url or fallback to image_url from Reddit)
      const imagePosts = posts.filter(
        (post: {
          is_image: boolean;
          image_url: string | null;
          media_url: string | null;
        }) => post.is_image && (post.media_url || post.image_url),
      );

      const feedItems: FeedItem[] = imagePosts.map(
        (post: {
          id: string;
          title: string;
          author: string | null;
          subreddit: string;
          score: number;
          num_comments: number;
          created_utc: string;
          url: string;
          is_image: boolean;
          image_url: string | null;
          media_url: string | null;
          image_width: number | null;
          image_height: number | null;
        }) => ({
          id: post.id,
          type: MediaType.IMAGE,
          caption: post.title,
          author: {
            name: post.author || "Unknown",
            handle: post.author ? `u/${post.author}` : undefined,
          },
          source: post.subreddit,
          timestamp: post.created_utc,
          aspectRatio: "aspect-[3/4]",
          width: post.image_width || undefined,
          height: post.image_height || undefined,
          likes: post.score,
          mediaUrl: post.media_url || post.image_url || "",
          redditData: {
            id: post.id,
            title: post.title,
            author: post.author || "",
            subreddit: post.subreddit,
            score: post.score,
            num_comments: post.num_comments,
            created_utc: post.created_utc,
            url: post.url,
            is_image: post.is_image,
            image_url: post.image_url,
          },
        }),
      );

      setItems(feedItems);
    } catch (err) {
      console.error("[MasonryWall] Failed to load feed:", err);
      setError(err instanceof Error ? err.message : "Failed to load feed");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadFeed();
  }, [config?.subreddit, limit]);

  const refresh = () => {
    loadFeed();
  };

  if (isLoading && items.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4">
        <RefreshCw className="w-8 h-8 text-amber-500 animate-spin mb-2" />
        <p className="text-sm text-neutral-400 font-mono">Loading feed...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4">
        <LayoutGrid className="w-8 h-8 text-red-500 mb-2" />
        <p className="text-sm text-red-400 font-mono">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-neutral-700 shrink-0">
        <div className="flex items-center gap-2">
          <LayoutGrid className="w-4 h-4 text-amber-500" />
          <span className="text-xs font-mono text-neutral-300">
            {config?.subreddit ? `r/${config.subreddit}` : "All Feeds"}
          </span>
          <span className="text-xs text-neutral-500">({items.length})</span>
        </div>
        <button
          onClick={refresh}
          disabled={isLoading}
          className="p-1 text-neutral-400 hover:text-amber-500 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Masonry Grid */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="columns-2 md:columns-3 gap-2 space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="break-inside-avoid group relative rounded-lg overflow-hidden bg-neutral-800 border border-neutral-700 hover:border-amber-500/50 transition-all cursor-pointer"
            >
              {item.mediaUrl && (
                <img
                  src={item.mediaUrl}
                  alt={item.caption}
                  className="w-full h-auto object-cover"
                  loading="lazy"
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute bottom-0 left-0 right-0 p-2">
                  <p className="text-xs text-white font-medium line-clamp-2">
                    {item.caption}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-amber-400">
                      r/{item.source}
                    </span>
                    <span className="text-xs text-neutral-400">
                      {item.likes} pts
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {items.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-32">
            <LayoutGrid className="w-8 h-8 text-neutral-600 mb-2" />
            <p className="text-sm text-neutral-500 font-mono">No items found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MasonryWallWidget;
