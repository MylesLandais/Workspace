"use client";

import { useState, useCallback, useEffect } from "react";
import { FeedItem, InfiniteFeedState } from "../types/feed";
import { generateFeedPage } from "../mock-data/factory";

const INITIAL_STATE: InfiniteFeedState = {
  items: [],
  isLoading: true,
  hasNextPage: true,
  endCursor: null,
  error: null,
};

export function useInfiniteFeed(pageSize: number = 20) {
  const [state, setState] = useState<InfiniteFeedState>(INITIAL_STATE);

  const loadMore = useCallback(async () => {
    if (state.isLoading || !state.hasNextPage) return;

    setState((prev) => ({ ...prev, isLoading: true }));

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    try {
      const page = generateFeedPage(state.endCursor, pageSize);

      setState((prev) => ({
        ...prev,
        items: [...prev.items, ...page.items],
        hasNextPage: page.hasNextPage,
        endCursor: page.endCursor,
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
      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 300));

      try {
        const page = generateFeedPage(null, pageSize);

        setState({
          items: page.items,
          hasNextPage: page.hasNextPage,
          endCursor: page.endCursor,
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
