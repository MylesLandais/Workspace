"use client";

import { useState, useCallback, useEffect } from "react";
import { FeedItem, InfiniteFeedState, MediaType } from "../types/feed";

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

export function useInfiniteFeed(pageSize: number = 20) {
  const [state, setState] = useState<InfiniteFeedState>(INITIAL_STATE);

  const loadMore = useCallback(async () => {
    if (state.isLoading || !state.hasNextPage) return;

    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      const params = new URLSearchParams({
        limit: pageSize.toString(),
      });
      if (state.endCursor) {
        params.append("cursor", state.endCursor);
      }

      const response = await fetch(`/api/feed?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch feed: ${response.statusText}`);
      }

      const page = await response.json();

      const items: FeedItem[] = page.edges.map((edge: any) => {
        const node = edge.node;

        // Build proxy URL from SHA256 with storagePath
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

      setState((prev) => ({
        ...prev,
        items: [...prev.items, ...items],
        hasNextPage: page.pageInfo.hasNextPage,
        endCursor: page.pageInfo.endCursor,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error : new Error("Failed to load feed"),
      }));
    }
  }, [state.isLoading, state.hasNextPage, state.endCursor, pageSize]);

  // Initial load
  useEffect(() => {
    const loadInitial = async () => {
      try {
        const params = new URLSearchParams({
          limit: pageSize.toString(),
        });

        const response = await fetch(`/api/feed?${params.toString()}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch feed: ${response.statusText}`);
        }

        const page = await response.json();

        const items: FeedItem[] = page.edges.map((edge: any) => {
          const node = edge.node;

          // Build proxy URL from SHA256 with storagePath
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

        setState({
          items,
          hasNextPage: page.pageInfo.hasNextPage,
          endCursor: page.pageInfo.endCursor,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error : new Error("Failed to load feed"),
        }));
      }
    };

    loadInitial();
  }, [pageSize]);

  return {
    items: state.items,
    isLoading: state.isLoading,
    hasNextPage: state.hasNextPage,
    error: state.error,
    loadMore,
  };
}
