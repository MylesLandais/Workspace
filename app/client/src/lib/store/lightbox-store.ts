import { create } from 'zustand';
import { FeedItem } from '@/lib/types/feed';
import { RedditPostDetails } from '@/lib/types/reddit';

interface LightboxState {
  isOpen: boolean;
  slideIndex: number;
  items: FeedItem[];
  redditThreadData: Record<string, RedditPostDetails | null>;
  isLoadingThread: Record<string, boolean>;

  openLightbox: (items: FeedItem[], startSlideIndex: number) => void;
  closeLightbox: () => void;
  setSlideIndex: (index: number) => void;
  setRedditThreadData: (postId: string, data: RedditPostDetails | null) => void;
  setLoadingThread: (postId: string, isLoading: boolean) => void;
}

export const useLightboxStore = create<LightboxState>((set) => ({
  isOpen: false,
  slideIndex: 0,
  items: [],
  redditThreadData: {},
  isLoadingThread: {},

  openLightbox: (items, startSlideIndex) =>
    set({
      isOpen: true,
      items,
      slideIndex: Math.max(0, startSlideIndex),
    }),

  closeLightbox: () =>
    set({
      isOpen: false,
      slideIndex: 0,
      items: [],
    }),

  setSlideIndex: (index) =>
    set({
      slideIndex: Math.max(0, index),
    }),

  setRedditThreadData: (postId, data) =>
    set((state) => ({
      redditThreadData: {
        ...state.redditThreadData,
        [postId]: data,
      },
    })),

  setLoadingThread: (postId, isLoading) =>
    set((state) => ({
      isLoadingThread: {
        ...state.isLoadingThread,
        [postId]: isLoading,
      },
    })),
}));
