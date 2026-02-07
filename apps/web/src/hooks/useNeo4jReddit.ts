"use client";

import { useState, useEffect, useCallback } from "react";
import type { RedditPost } from "@/lib/types/reddit";

interface UseNeo4jRedditPostsOptions {
  immediate?: boolean;
  retryCount?: number;
}

interface UseNeo4jRedditPostsResult {
  posts: RedditPost[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch Reddit posts from Neo4j via GraphQL
 * This queries our internal database, not the external Reddit API
 */
export function useNeo4jRedditPosts(
  subreddit: string = "unixporn",
  limit: number = 20,
  options: UseNeo4jRedditPostsOptions = {},
): UseNeo4jRedditPostsResult {
  const { immediate = true, retryCount = 2 } = options;
  const [posts, setPosts] = useState<RedditPost[]>([]);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);
  const [offset, setOffset] = useState(0);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retryCount; attempt++) {
      try {
        const params = new URLSearchParams({
          subreddit,
          limit: limit.toString(),
          offset: offset.toString(),
        });

        const response = await fetch(`/api/reddit/posts?${params.toString()}`);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.message || `Failed to fetch: ${response.statusText}`,
          );
        }

        const data = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        const newPosts = data.posts || [];

        // Append new posts instead of replacing
        setPosts((prev) => {
          const existingIds = new Set(prev.map((p) => p.id));
          const filtered = newPosts.filter(
            (p: RedditPost) => !existingIds.has(p.id),
          );
          return [...prev, ...filtered];
        });

        // Increment offset for next fetch
        if (newPosts.length > 0) {
          setOffset((prev) => prev + newPosts.length);
        }

        setLoading(false);
        return;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));

        if (attempt < retryCount) {
          await new Promise((resolve) =>
            setTimeout(resolve, 500 * (attempt + 1)),
          );
        }
      }
    }

    setError(lastError);
    setLoading(false);
  }, [subreddit, limit, offset, retryCount]);

  useEffect(() => {
    if (immediate) {
      refetch();
    }
  }, [immediate, refetch]);

  return { posts, loading, error, refetch };
}

/**
 * Hook to fetch posts from multiple subreddits
 */
export function useNeo4jMultiReddit(
  subreddits: string[],
  limitPerSubreddit: number = 10,
  options: UseNeo4jRedditPostsOptions = {},
): UseNeo4jRedditPostsResult & { bySubreddit: Record<string, RedditPost[]> } {
  const { immediate = true } = options;
  const [posts, setPosts] = useState<RedditPost[]>([]);
  const [bySubreddit, setBySubreddit] = useState<Record<string, RedditPost[]>>(
    {},
  );
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const results = await Promise.all(
        subreddits.map(async (sub) => {
          const params = new URLSearchParams({
            subreddit: sub,
            limit: limitPerSubreddit.toString(),
          });

          const response = await fetch(
            `/api/reddit/posts?${params.toString()}`,
          );

          if (!response.ok) {
            console.warn(`Failed to fetch ${sub}`);
            return { subreddit: sub, posts: [] };
          }

          const data = await response.json();
          return { subreddit: sub, posts: data.posts || [] };
        }),
      );

      const grouped: Record<string, RedditPost[]> = {};
      const allPosts: RedditPost[] = [];

      for (const result of results) {
        grouped[result.subreddit] = result.posts;
        allPosts.push(...result.posts);
      }

      // Sort all posts by score descending
      allPosts.sort((a, b) => b.score - a.score);

      setBySubreddit(grouped);
      setPosts(allPosts);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [subreddits, limitPerSubreddit]);

  useEffect(() => {
    if (immediate && subreddits.length > 0) {
      refetch();
    }
  }, [immediate, refetch, subreddits.length]);

  return { posts, bySubreddit, loading, error, refetch };
}
