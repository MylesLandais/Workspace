"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useNeo4jRedditPosts } from "@/hooks/useNeo4jReddit";
import { RedditPostCard } from "@/components/reddit/RedditPostCard";
import { Loader2 } from "lucide-react";

interface ReadStatus {
  [postId: string]: boolean;
}

export default function UnixpornFeedPage() {
  const [readStatus, setReadStatus] = useState<ReadStatus>({});
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const { posts, loading, error, refetch } = useNeo4jRedditPosts(
    "unixporn",
    20,
    { immediate: true },
  );

  // Load read status from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("unixporn_read_status");
    if (stored) {
      try {
        setReadStatus(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse read status:", e);
      }
    }
  }, []);

  // Save read status to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("unixporn_read_status", JSON.stringify(readStatus));
  }, [readStatus]);

  // Mark post as read
  const markAsRead = useCallback((postId: string) => {
    setReadStatus((prev) => ({ ...prev, [postId]: true }));
  }, []);

  // Mark post as unread
  const markAsUnread = useCallback((postId: string) => {
    setReadStatus((prev) => {
      const next = { ...prev };
      delete next[postId];
      return next;
    });
  }, []);

  // Intersection observer for infinite scroll
  useEffect(() => {
    if (!sentinelRef.current) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && posts.length > 0) {
          // Load more posts
          refetch();
        }
      },
      { rootMargin: "200px" },
    );

    observerRef.current.observe(sentinelRef.current);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [loading, posts.length, refetch]);

  // Mark post as read when it comes into view
  const handlePostView = useCallback(
    (postId: string) => {
      if (!readStatus[postId]) {
        markAsRead(postId);
      }
    },
    [readStatus, markAsRead],
  );

  const unreadCount = posts.filter((p) => !readStatus[p.id]).length;

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">r/unixporn</h1>
          <p className="text-gray-400 text-sm">
            {posts.length} posts • {unreadCount} unread
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-400">Error loading posts: {error.message}</p>
            <button
              onClick={() => refetch()}
              className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* Posts Grid */}
        <div className="space-y-6">
          {posts.map((post) => {
            const isRead = readStatus[post.id] || false;
            return (
              <div
                key={post.id}
                className={`relative ${
                  !isRead ? "ring-2 ring-blue-500/50" : ""
                }`}
                onMouseEnter={() => handlePostView(post.id)}
              >
                <RedditPostCard
                  post={{
                    ...post,
                    image_url: post.media_url || post.image_url,
                  }}
                  variant="expanded"
                />
                {!isRead && (
                  <div className="absolute top-2 right-2">
                    <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                      New
                    </span>
                  </div>
                )}
                <div className="absolute top-2 left-2 flex gap-2">
                  <button
                    onClick={() =>
                      isRead ? markAsUnread(post.id) : markAsRead(post.id)
                    }
                    className="bg-black/60 hover:bg-black/80 text-white text-xs px-2 py-1 rounded backdrop-blur-sm"
                    title={isRead ? "Mark as unread" : "Mark as read"}
                  >
                    {isRead ? "✓ Read" : "Mark read"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Loading Indicator */}
        {loading && (
          <div className="flex justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        )}

        {/* Infinite Scroll Sentinel */}
        <div ref={sentinelRef} className="h-1" />

        {/* Empty State */}
        {!loading && posts.length === 0 && !error && (
          <div className="text-center py-12 text-gray-500">
            <p>No posts found. Try syncing posts from Jupyter.</p>
          </div>
        )}
      </div>
    </div>
  );
}
