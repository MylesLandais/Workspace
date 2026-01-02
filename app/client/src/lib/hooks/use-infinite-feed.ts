"use client";

import { useState, useCallback, useEffect } from "react";
import { FeedItem, InfiniteFeedState, MediaType } from "../types/feed";
import { generateFeedPage } from "../mock-data/factory";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_DATA !== "false"; // Default to true

const INITIAL_STATE: InfiniteFeedState = {
  items: [],
  isLoading: true,
  hasNextPage: true,
  endCursor: null,
  error: null,
};

function calculateAspectRatio(width: number, height: number): string {
  const ratio = width / height;
  if (ratio >= 1.7) return "aspect-[16/9]";
  if (ratio >= 1.2) return "aspect-[4/3]";
  if (ratio >= 0.9) return "aspect-square";
  if (ratio >= 0.6) return "aspect-[3/4]";
  return "aspect-[9/16]";
}

function mapMediaType(type: string): MediaType {
  switch (type.toUpperCase()) {
    case "VIDEO":
      return MediaType.VIDEO;
    case "IMAGE":
      return MediaType.IMAGE;
    default:
      return MediaType.IMAGE;
  }
}

export interface FeedFilters {
  query: string;
  categories: string[];
  tags: string[];
}

export function useInfiniteFeed(pageSize: number = 20, filters?: FeedFilters) {
  const [state, setState] = useState<InfiniteFeedState>(INITIAL_STATE);

  const loadPage = useCallback(async (cursor: string | null = null, isInitial: boolean = false) => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      if (USE_MOCK) {
        // Reduced simulated network delay for faster response
        await new Promise((resolve) => setTimeout(resolve, isInitial ? 50 : 150));

        const page = await generateFeedPage(cursor, pageSize);
        let items = page.items;

        // Apply filters
        if (filters) {
          if (filters.query) {
            const q = filters.query.toLowerCase();
            items = items.filter(item =>
              item.caption?.toLowerCase().includes(q) ||
              item.author.handle?.toLowerCase().includes(q) ||
              item.source?.toLowerCase().includes(q)
            );
          }
          if (filters.categories.length > 0) {
            items = items.filter(item => {
              const type = item.type.toLowerCase();
              return filters.categories.some(c => type.includes(c.toLowerCase()));
            });
          }
        }

        setState(prev => ({
          items: isInitial ? items : [...prev.items, ...items],
          hasNextPage: page.hasNextPage,
          endCursor: page.endCursor,
          isLoading: false,
          error: null,
        }));
        return;
      }

      const params = new URLSearchParams({
        limit: pageSize.toString(),
      });
      if (cursor) params.append("cursor", cursor);
      if (filters?.query) params.append("query", filters.query);
      if (filters?.categories.length) params.append("categories", filters.categories.join(","));

      const response = await fetch(`/api/feed?${params.toString()}`);
      if (!response.ok) throw new Error(`Failed to fetch feed: ${response.statusText}`);

      const page = await response.json();
      const items: FeedItem[] = page.edges.map((edge: { node: {
        id: string;
        imageUrl?: string;
        sha256?: string;
        storagePath?: string;
        mediaType: string;
        title?: string;
        handle?: { name: string; handle: string };
        platform?: string;
        publishDate: string;
        width?: number;
        height?: number;
        urlExpiresAt?: string;
      } }) => {
        const node = edge.node;
        let mediaUrl = node.imageUrl;
        if (node.sha256 && node.storagePath) {
          const encodedPath = encodeURIComponent(node.storagePath);
          mediaUrl = `/api/image/${node.sha256}?path=${encodedPath}`;
        }
        return {
          id: node.id,
          type: mapMediaType(node.mediaType),
          caption: node.title || "",
          author: {
            name: node.handle?.name || "Unknown",
            handle: node.handle?.handle || "unknown",
          },
          source: node.platform || "UNKNOWN",
          timestamp: node.publishDate,
          aspectRatio: calculateAspectRatio(node.width || 1, node.height || 1),
          width: node.width || 800,
          height: node.height || 600,
          likes: 0,
          mediaUrl,
          urlExpiresAt: node.urlExpiresAt,
        };
      });

      setState(prev => ({
        items: isInitial ? items : [...prev.items, ...items],
        hasNextPage: page.pageInfo.hasNextPage,
        endCursor: page.pageInfo.endCursor,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error : new Error("Failed to load feed"),
      }));
    }
  }, [pageSize, filters]);

  // Initial load or on filter change
  useEffect(() => {
    loadPage(null, true);
  }, [loadPage]);

  const loadMore = useCallback(async () => {
    if (state.isLoading || !state.hasNextPage) return;
    loadPage(state.endCursor);
  }, [state.isLoading, state.hasNextPage, state.endCursor, loadPage]);

  return {
    items: state.items,
    isLoading: state.isLoading,
    hasNextPage: state.hasNextPage,
    error: state.error,
    loadMore,
  };
}
