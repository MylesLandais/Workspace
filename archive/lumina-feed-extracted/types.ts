export enum MediaType {
  IMAGE = 'image',
  SHORT = 'short',
  GIF = 'gif'
}

export interface Author {
  name: string;
  handle: string;
  avatarUrl?: string; // Placeholder ID
}

export interface FeedItem {
  id: string;
  type: MediaType;
  caption: string;
  author: Author;
  source: string; // e.g., "Instagram", "Reddit", "RSS"
  timestamp: string;
  aspectRatio: string; // Tailwind class e.g., "aspect-[3/4]"
  width: number; // For picsum
  height: number; // For picsum
  likes: number;
  mediaUrl?: string; // Optional override for the actual media content
}

export interface FilterState {
  persons: string[];
  sources: string[];
  searchQuery: string;
}

export interface SavedBoard {
  id: string;
  name: string;
  filters: FilterState;
  createdAt: number;
}

export interface Relationship {
  targetId: string;
  type: string; // e.g. "Best Friend", "Dating", "Co-star"
}

export type PlatformType = 'reddit' | 'instagram' | 'twitter' | 'tiktok' | 'youtube' | 'web';

export interface SourceLink {
  platform: PlatformType;
  id: string; // handle, subreddit name, or url
  label?: string; // e.g. "Main", "Spam", "Fan Page"
  hidden?: boolean; // Toggles visibility in feed
}

export interface IdentityProfile {
  id: string;
  name: string;
  bio: string;
  avatarUrl: string;
  aliases: string[];
  // Replaced fixed socials with dynamic sources array
  sources: SourceLink[];
  contextKeywords: string[]; // Helps AI generate relevant captions
  imagePool: string[]; // Mock images that vibe with this person
  relationships: Relationship[];
}

export const INITIAL_FILTERS: FilterState = {
  persons: [],
  sources: [],
  searchQuery: ''
};

export type Theme = 'default' | 'kanagawa';

export type AppView = 'feed' | 'admin';