/**
 * TypeScript types for Bunny GraphQL API responses
 *
 * These types match the GraphQL schema and can be used for type-safe
 * data handling in your application.
 */

// ============================================================================
// Enums
// ============================================================================

export type Platform =
  | 'RSS'
  | 'REDDIT'
  | 'YOUTUBE'
  | 'TWITTER'
  | 'INSTAGRAM'
  | 'TIKTOK'
  | 'VSCO'
  | 'IMAGEBOARD';

export type MediaType = 'IMAGE' | 'VIDEO' | 'TEXT';

export type HandleStatus = 'ACTIVE' | 'SUSPENDED' | 'ABANDONED';

export type ActivityFilter = 'ALL' | 'ACTIVE' | 'INACTIVE' | 'PAUSED';

// ============================================================================
// Feed Types
// ============================================================================

export interface HandleInfo {
  name: string;
  handle: string;
  creatorName?: string;
}

export interface Subreddit {
  name: string;
  displayName: string;
  description?: string;
  iconUrl?: string;
  subscriberCount: number;
  createdAt: string;
}

export interface User {
  username: string;
  karma?: number;
  accountAgeDays?: number;
}

export interface ImageCluster {
  id: string;
  canonicalSha256: string;
  canonicalMedia?: Media;
  repostCount: number;
  firstSeen: string;
  lastSeen: string;
  memberImages?: Media[];
}

export interface Media {
  id: string;
  title: string;
  sourceUrl: string;
  publishDate: string;
  imageUrl: string;
  presignedUrl?: string;
  urlExpiresAt?: string;
  mediaType: MediaType;
  platform: Platform;
  handle: HandleInfo;
  score?: number;
  subreddit?: Subreddit;
  author?: User;
  viewCount?: number;
  sha256?: string;
  phash?: string;
  dhash?: string;
  width?: number;
  height?: number;
  sizeBytes?: number;
  mimeType?: string;
  storagePath?: string;
  cluster?: ImageCluster;
  isDuplicate?: boolean;
  isRepost?: boolean;
}

export interface FeedEdge {
  cursor: string;
  node: Media;
}

export interface PageInfo {
  hasNextPage: boolean;
  endCursor?: string;
}

export interface FeedConnection {
  edges: FeedEdge[];
  pageInfo: PageInfo;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface FeedFilters {
  persons: string[];
  sources: string[];
  tags: string[];
  searchQuery: string;
  categories: string[];
}

export interface SourceFiltersInput {
  groupId?: string;
  sourceType?: Platform;
  activity?: ActivityFilter;
  searchQuery?: string;
}

// ============================================================================
// Source Types
// ============================================================================

export interface Source {
  id: string;
  name: string;
  sourceType: Platform;
  subredditName?: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  url?: string;
  rssUrl?: string;
  iconUrl?: string;
  description?: string;
  entityId?: string;
  entityName?: string;
  group: string;
  groupId?: string;
  tags: string[];
  isPaused: boolean;
  isEnabled: boolean;
  isActive: boolean;
  lastSynced?: string;
  mediaCount: number;
  storiesPerMonth: number;
  readsPerMonth: number;
  health: string;
}

export interface CreateSourceInput {
  name: string;
  sourceType: Platform;
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

export interface FeedGroup {
  id: string;
  name: string;
  createdAt: string;
}

export interface SubredditResult {
  name: string;
  displayName: string;
  subscriberCount: number;
  description: string;
  iconUrl?: string;
  isSubscribed: boolean;
}

export interface ImportResult {
  imported: number;
  skipped: number;
  failed: number;
  sources: Source[];
  errors: string[];
}

// ============================================================================
// SavedBoard Types
// ============================================================================

export interface FilterState {
  persons: string[];
  sources: string[];
  tags: string[];
  searchQuery: string;
}

export interface SavedBoard {
  id: string;
  name: string;
  filters: FilterState;
  createdAt: string;
  userId: string;
}

export interface SavedBoardInput {
  name: string;
  filters: FeedFilters;
}

// ============================================================================
// Creator/Identity Types
// ============================================================================

export interface SourceLink {
  platform: Platform;
  id: string;
  label?: string;
  hidden: boolean;
}

export interface Relationship {
  targetId: string;
  type: string;
  target?: IdentityProfile;
}

export interface IdentityProfile {
  id: string;
  name: string;
  bio: string;
  avatarUrl: string;
  aliases: string[];
  sources: SourceLink[];
  contextKeywords: string[];
  imagePool: string[];
  relationships: Relationship[];
}

export interface Handle {
  id: string;
  platform: Platform;
  username: string;
  handle: string;
  url: string;
  verified: boolean;
  status: HandleStatus;
  creator?: Creator;
  mediaCount: number;
  lastSynced?: string;
  health: string;
  label?: string;
  hidden: boolean;
}

export interface Creator {
  id: string;
  slug: string;
  name: string;
  displayName: string;
  bio?: string;
  avatarUrl?: string;
  verified: boolean;
  handles: Handle[];
  aliases: string[];
  contextKeywords: string[];
  imagePool: string[];
  relationships: Relationship[];
}

// ============================================================================
// Image Processing Types
// ============================================================================

export interface SimilarImage {
  media: Media;
  similarityScore: number;
  method: string;
  hammingDistance?: number;
}

export interface OriginalImageInfo {
  mediaId: string;
  firstSeen: string;
  postId?: string;
}

export interface ImageIngestionResult {
  mediaId: string;
  clusterId: string;
  isDuplicate: boolean;
  isRepost: boolean;
  confidence?: number;
  matchedMethod?: string;
  original?: OriginalImageInfo;
}

export interface RepostInfo {
  media: Media;
  postId?: string;
  createdAt: string;
  confidence: number;
}

export interface ImageLineage {
  mediaId: string;
  clusterId: string;
  original?: Media;
  reposts: RepostInfo[];
}

// ============================================================================
// OPML Types
// ============================================================================

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
  errors: string[];
}

// ============================================================================
// GraphQL Response Types
// ============================================================================

export interface FeedQueryResponse {
  feed: FeedConnection;
}

export interface SourcesQueryResponse {
  getUserSources: Source[];
}

export interface SourceQueryResponse {
  getSourceById: Source | null;
}

export interface FeedGroupsQueryResponse {
  getFeedGroups: FeedGroup[];
}

export interface SubredditSearchResponse {
  searchSubreddits: SubredditResult[];
}

export interface SavedBoardsQueryResponse {
  getSavedBoards: SavedBoard[];
}

export interface CreateSourceResponse {
  createSource: Source;
}

export interface UpdateSourceResponse {
  updateSource: Source;
}

export interface DeleteSourceResponse {
  deleteSource: boolean;
}

export interface BulkDeleteResponse {
  bulkDeleteSources: number;
}

export interface TogglePauseResponse {
  toggleSourcePause: Source;
}

export interface ImportOPMLResponse {
  importOPML: ImportResult;
}

export interface SubscribeResponse {
  subscribeToSource: Source;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Extract node type from edge type
 */
export type NodeOf<T extends { edges: Array<{ node: unknown }> }> =
  T['edges'][number]['node'];

/**
 * Make all properties optional recursively
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

/**
 * Filter keys by value type
 */
export type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];
