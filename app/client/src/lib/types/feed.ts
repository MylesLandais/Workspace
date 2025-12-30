export enum MediaType {
  IMAGE = "image",
  SHORT = "short",
  GIF = "gif",
  VIDEO = "video",
  TEXT = "text",
}

export interface Author {
  name: string;
  handle: string;
  avatarUrl?: string;
}

export interface FeedItem {
  id: string;
  type: MediaType;
  caption: string;
  author: Author;
  source: string;
  timestamp: string;
  aspectRatio: string;
  width: number;
  height: number;
  likes: number;
  mediaUrl?: string;
  thumbnailUrl?: string;
  tags?: string[];
}

export interface FeedPage {
  items: FeedItem[];
  hasNextPage: boolean;
  endCursor: string | null;
}

export interface InfiniteFeedState {
  items: FeedItem[];
  isLoading: boolean;
  hasNextPage: boolean;
  endCursor: string | null;
  error: Error | null;
}
