export enum SourceType {
  RSS = "RSS",
  REDDIT = "REDDIT",
  YOUTUBE = "YOUTUBE",
  TWITTER = "TWITTER",
  INSTAGRAM = "INSTAGRAM",
  TIKTOK = "TIKTOK",
  VSCO = "VSCO",
  IMAGEBOARD = "IMAGEBOARD",
}

export type SourceHealth = "green" | "yellow" | "red";

export type ActivityFilter = "all" | "active" | "inactive" | "paused";

export interface Source {
  id: string;
  name: string;
  url?: string;
  rssUrl?: string;
  description?: string;
  sourceType: SourceType;
  subredditName?: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  iconUrl?: string;
  mediaCount: number;
  storiesPerMonth: number;
  readsPerMonth: number;
  lastSynced?: string;
  isEnabled: boolean;
  isPaused: boolean;
  isActive: boolean;
  health: SourceHealth;
  group: string;
  groupId?: string;
  tags: string[];
  entityId?: string;
  entityName?: string;
}

export interface SourceStats {
  storiesPerMonth: number;
  readsPerMonth: number;
  lastFetched?: string;
}

export interface SourceFilters {
  groupId?: string;
  sourceType?: SourceType;
  activity?: ActivityFilter;
  searchQuery?: string;
}

export interface FeedGroup {
  id: string;
  name: string;
  createdAt?: string;
}

export interface OPMLFeed {
  title: string;
  xmlUrl: string;
  htmlUrl?: string;
  category?: string;
  description?: string;
}

export interface OPMLParseResult {
  feeds: OPMLFeed[];
  feedCount: number;
  categories: string[];
  errors?: string[];
}

export interface ImportResult {
  imported: number;
  skipped: number;
  failed: number;
  sources: Source[];
  errors?: string[];
}

export interface CreateSourceInput {
  name: string;
  sourceType: SourceType;
  url?: string;
  subredditName?: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  groupId?: string;
  description?: string;
}

export interface UpdateSourceInput {
  name?: string;
  description?: string;
  groupId?: string;
  isPaused?: boolean;
  isEnabled?: boolean;
}

export type ViewMode = "grid" | "list" | "table";

export interface SourcesState {
  sources: Source[];
  feedGroups: FeedGroup[];
  filters: SourceFilters;
  viewMode: ViewMode;
  selectedIds: Set<string>;
  isLoading: boolean;
  error: string | null;
}
