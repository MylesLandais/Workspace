export type SourceType = 'rss' | 'twitter' | 'newsletter' | 'youtube' | 'reddit' | 'booru' | 'monitor';

export interface FeedSource {
  id: string;
  name: string;
  icon?: string;
  type: SourceType;
  unreadCount: number;
}

export interface SauceResult {
  similarity: number;
  sourceUrl: string;
  artistName: string;
  extUrl?: string;
}

export interface Article {
  id: string;
  sourceId: string;
  title: string;
  author: string;
  content: string; // HTML or Text content
  summary?: string; // AI Generated summary
  publishedAt: string;
  read: boolean;
  saved: boolean; // "Read Later"
  archived: boolean;
  tags: string[]; // e.g. "rem_(re:zero)", "width:1080"
  type: SourceType;
  url: string;
  imageUrl?: string;
  imageWidth?: number;
  imageHeight?: number;
  sauce?: SauceResult; // Enriched data from SauceNAO
}

export interface Board {
  id: string;
  name: string;
  articleIds: string[];
}

export interface AIResponse {
  summary?: string;
  keyTakeaways?: string[];
  chatResponse?: string;
}

export type ViewMode = 'inbox' | 'later' | 'archive' | 'feed' | 'tag' | 'analytics' | 'board';
export type LayoutMode = 'list' | 'grid';