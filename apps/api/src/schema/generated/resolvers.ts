import { GraphQLResolveInfo, GraphQLScalarType, GraphQLScalarTypeConfig } from 'graphql';
import { Context } from '../../index.js';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
export type RequireFields<T, K extends keyof T> = Omit<T, K> & { [P in K]-?: NonNullable<T[P]> };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  DateTime: { input: any; output: any; }
  Upload: { input: any; output: any; }
};

export type Creator = {
  __typename?: 'Creator';
  aliases: Array<Scalars['String']['output']>;
  avatarUrl?: Maybe<Scalars['String']['output']>;
  bio?: Maybe<Scalars['String']['output']>;
  contextKeywords: Array<Scalars['String']['output']>;
  displayName: Scalars['String']['output'];
  handles: Array<Handle>;
  id: Scalars['ID']['output'];
  imagePool: Array<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  relationships: Array<Relationship>;
  slug: Scalars['String']['output'];
  verified: Scalars['Boolean']['output'];
};

export type FeedConnection = {
  __typename?: 'FeedConnection';
  edges: Array<FeedEdge>;
  pageInfo: PageInfo;
};

export type FeedEdge = {
  __typename?: 'FeedEdge';
  cursor: Scalars['String']['output'];
  node: Media;
};

export type FeedFilters = {
  categories: Array<Scalars['String']['input']>;
  persons: Array<Scalars['String']['input']>;
  searchQuery: Scalars['String']['input'];
  sources: Array<Scalars['String']['input']>;
  tags: Array<Scalars['String']['input']>;
};

export type FeedGroup = {
  __typename?: 'FeedGroup';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
};

export type FilterState = {
  __typename?: 'FilterState';
  persons: Array<Scalars['String']['output']>;
  searchQuery: Scalars['String']['output'];
  sources: Array<Scalars['String']['output']>;
  tags: Array<Scalars['String']['output']>;
};

export type Handle = {
  __typename?: 'Handle';
  creator?: Maybe<Creator>;
  handle: Scalars['String']['output'];
  health: Scalars['String']['output'];
  hidden: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  label?: Maybe<Scalars['String']['output']>;
  lastSynced?: Maybe<Scalars['DateTime']['output']>;
  mediaCount: Scalars['Int']['output'];
  platform: Platform;
  status: HandleStatus;
  url: Scalars['String']['output'];
  username: Scalars['String']['output'];
  verified: Scalars['Boolean']['output'];
};

export type HandleInfo = {
  __typename?: 'HandleInfo';
  creatorName?: Maybe<Scalars['String']['output']>;
  handle: Scalars['String']['output'];
  name: Scalars['String']['output'];
};

export enum HandleStatus {
  Abandoned = 'ABANDONED',
  Active = 'ACTIVE',
  Suspended = 'SUSPENDED'
}

export type IdentityProfile = {
  __typename?: 'IdentityProfile';
  aliases: Array<Scalars['String']['output']>;
  avatarUrl: Scalars['String']['output'];
  bio: Scalars['String']['output'];
  contextKeywords: Array<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  imagePool: Array<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  relationships: Array<Relationship>;
  sources: Array<SourceLink>;
};

export type IdentityProfileInput = {
  aliases: Array<Scalars['String']['input']>;
  avatarUrl: Scalars['String']['input'];
  bio: Scalars['String']['input'];
  contextKeywords: Array<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  imagePool: Array<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  relationships: Array<RelationshipInput>;
  sources: Array<SourceLinkInput>;
};

export type ImageCluster = {
  __typename?: 'ImageCluster';
  canonicalMedia?: Maybe<Media>;
  canonicalSha256: Scalars['String']['output'];
  firstSeen: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  lastSeen: Scalars['DateTime']['output'];
  memberImages: Array<Media>;
  repostCount: Scalars['Int']['output'];
};

export type ImageIngestionResult = {
  __typename?: 'ImageIngestionResult';
  clusterId: Scalars['ID']['output'];
  confidence?: Maybe<Scalars['Float']['output']>;
  isDuplicate: Scalars['Boolean']['output'];
  isRepost: Scalars['Boolean']['output'];
  matchedMethod?: Maybe<Scalars['String']['output']>;
  mediaId: Scalars['ID']['output'];
  original?: Maybe<OriginalImageInfo>;
};

export type ImageLineage = {
  __typename?: 'ImageLineage';
  clusterId: Scalars['ID']['output'];
  mediaId: Scalars['ID']['output'];
  original?: Maybe<Media>;
  reposts: Array<RepostInfo>;
};

export type Media = {
  __typename?: 'Media';
  author?: Maybe<User>;
  cluster?: Maybe<ImageCluster>;
  dhash?: Maybe<Scalars['String']['output']>;
  handle: HandleInfo;
  height?: Maybe<Scalars['Int']['output']>;
  id: Scalars['ID']['output'];
  imageUrl: Scalars['String']['output'];
  isDuplicate?: Maybe<Scalars['Boolean']['output']>;
  isRepost?: Maybe<Scalars['Boolean']['output']>;
  mediaType: MediaType;
  mimeType?: Maybe<Scalars['String']['output']>;
  phash?: Maybe<Scalars['String']['output']>;
  platform: Platform;
  presignedUrl?: Maybe<Scalars['String']['output']>;
  publishDate: Scalars['DateTime']['output'];
  score?: Maybe<Scalars['Int']['output']>;
  sha256?: Maybe<Scalars['String']['output']>;
  sizeBytes?: Maybe<Scalars['Int']['output']>;
  sourceUrl: Scalars['String']['output'];
  storagePath?: Maybe<Scalars['String']['output']>;
  subreddit?: Maybe<Subreddit>;
  title: Scalars['String']['output'];
  urlExpiresAt?: Maybe<Scalars['DateTime']['output']>;
  viewCount?: Maybe<Scalars['Int']['output']>;
  width?: Maybe<Scalars['Int']['output']>;
};

export enum MediaType {
  Image = 'IMAGE',
  Text = 'TEXT',
  Video = 'VIDEO'
}

export type Mutation = {
  __typename?: 'Mutation';
  addHandle: Handle;
  createCreator: Creator;
  createFeedGroup: FeedGroup;
  createIdentityProfile: IdentityProfile;
  createRelationship: Relationship;
  createSavedBoard: SavedBoard;
  deleteIdentityProfile: Scalars['Boolean']['output'];
  deleteRelationship: Scalars['Boolean']['output'];
  deleteSavedBoard: Scalars['Boolean']['output'];
  ingestImage: ImageIngestionResult;
  removeHandle: Scalars['Boolean']['output'];
  subscribeToSource: Source;
  toggleHandlePause: Handle;
  updateHandleStatus: Handle;
  updateIdentityProfile: IdentityProfile;
  updateSavedBoard: SavedBoard;
  verifyHandle: Handle;
};


export type MutationAddHandleArgs = {
  creatorId: Scalars['ID']['input'];
  platform: Platform;
  url: Scalars['String']['input'];
  username: Scalars['String']['input'];
};


export type MutationCreateCreatorArgs = {
  displayName: Scalars['String']['input'];
  name: Scalars['String']['input'];
};


export type MutationCreateFeedGroupArgs = {
  name: Scalars['String']['input'];
};


export type MutationCreateIdentityProfileArgs = {
  input: IdentityProfileInput;
  userId: Scalars['ID']['input'];
};


export type MutationCreateRelationshipArgs = {
  input: RelationshipInput;
  profileId: Scalars['ID']['input'];
};


export type MutationCreateSavedBoardArgs = {
  input: SavedBoardInput;
  userId: Scalars['ID']['input'];
};


export type MutationDeleteIdentityProfileArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteRelationshipArgs = {
  profileId: Scalars['ID']['input'];
  targetId: Scalars['ID']['input'];
};


export type MutationDeleteSavedBoardArgs = {
  id: Scalars['ID']['input'];
};


export type MutationIngestImageArgs = {
  author?: InputMaybe<Scalars['String']['input']>;
  createdAt?: InputMaybe<Scalars['DateTime']['input']>;
  image: Scalars['Upload']['input'];
  postId?: InputMaybe<Scalars['String']['input']>;
  subreddit?: InputMaybe<Scalars['String']['input']>;
  title?: InputMaybe<Scalars['String']['input']>;
};


export type MutationRemoveHandleArgs = {
  handleId: Scalars['ID']['input'];
};


export type MutationSubscribeToSourceArgs = {
  groupId?: InputMaybe<Scalars['String']['input']>;
  subredditName: Scalars['String']['input'];
};


export type MutationToggleHandlePauseArgs = {
  handleId: Scalars['ID']['input'];
};


export type MutationUpdateHandleStatusArgs = {
  handleId: Scalars['ID']['input'];
  status: HandleStatus;
};


export type MutationUpdateIdentityProfileArgs = {
  id: Scalars['ID']['input'];
  input: IdentityProfileInput;
};


export type MutationUpdateSavedBoardArgs = {
  id: Scalars['ID']['input'];
  input: SavedBoardInput;
};


export type MutationVerifyHandleArgs = {
  handleId: Scalars['ID']['input'];
};

export type OriginalImageInfo = {
  __typename?: 'OriginalImageInfo';
  firstSeen: Scalars['DateTime']['output'];
  mediaId: Scalars['ID']['output'];
  postId?: Maybe<Scalars['String']['output']>;
};

export type PageInfo = {
  __typename?: 'PageInfo';
  endCursor?: Maybe<Scalars['String']['output']>;
  hasNextPage: Scalars['Boolean']['output'];
};

export enum Platform {
  Imageboard = 'IMAGEBOARD',
  Instagram = 'INSTAGRAM',
  Reddit = 'REDDIT',
  Tiktok = 'TIKTOK',
  Twitter = 'TWITTER',
  Vsco = 'VSCO',
  Youtube = 'YOUTUBE'
}

export type Query = {
  __typename?: 'Query';
  checkDuplicate: ImageIngestionResult;
  creator?: Maybe<Creator>;
  creators: Array<Creator>;
  feed: FeedConnection;
  getFeedGroups: Array<FeedGroup>;
  getIdentityProfile?: Maybe<IdentityProfile>;
  getIdentityProfiles: Array<IdentityProfile>;
  getSavedBoards: Array<SavedBoard>;
  getSources: Array<Source>;
  imageCluster?: Maybe<ImageCluster>;
  imageLineage?: Maybe<ImageLineage>;
  searchSubreddits: Array<SubredditResult>;
  similarImages: Array<SimilarImage>;
};


export type QueryCheckDuplicateArgs = {
  image: Scalars['Upload']['input'];
};


export type QueryCreatorArgs = {
  slug: Scalars['String']['input'];
};


export type QueryCreatorsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  query?: InputMaybe<Scalars['String']['input']>;
};


export type QueryFeedArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filters?: InputMaybe<FeedFilters>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryGetIdentityProfileArgs = {
  id: Scalars['ID']['input'];
};


export type QueryGetIdentityProfilesArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  query?: InputMaybe<Scalars['String']['input']>;
};


export type QueryGetSavedBoardsArgs = {
  userId: Scalars['ID']['input'];
};


export type QueryGetSourcesArgs = {
  groupId?: InputMaybe<Scalars['String']['input']>;
};


export type QueryImageClusterArgs = {
  clusterId: Scalars['ID']['input'];
};


export type QueryImageLineageArgs = {
  mediaId: Scalars['ID']['input'];
};


export type QuerySearchSubredditsArgs = {
  query: Scalars['String']['input'];
};


export type QuerySimilarImagesArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  mediaId: Scalars['ID']['input'];
};

export type Relationship = {
  __typename?: 'Relationship';
  target?: Maybe<IdentityProfile>;
  targetId: Scalars['ID']['output'];
  type: Scalars['String']['output'];
};

export type RelationshipInput = {
  targetId: Scalars['ID']['input'];
  type: Scalars['String']['input'];
};

export type RepostInfo = {
  __typename?: 'RepostInfo';
  confidence: Scalars['Float']['output'];
  createdAt: Scalars['DateTime']['output'];
  media: Media;
  postId?: Maybe<Scalars['String']['output']>;
};

export type SavedBoard = {
  __typename?: 'SavedBoard';
  createdAt: Scalars['DateTime']['output'];
  filters: FilterState;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  userId: Scalars['ID']['output'];
};

export type SavedBoardInput = {
  filters: FeedFilters;
  name: Scalars['String']['input'];
};

export type SimilarImage = {
  __typename?: 'SimilarImage';
  hammingDistance?: Maybe<Scalars['Int']['output']>;
  media: Media;
  method: Scalars['String']['output'];
  similarityScore: Scalars['Float']['output'];
};

export type Source = {
  __typename?: 'Source';
  entityId?: Maybe<Scalars['String']['output']>;
  entityName?: Maybe<Scalars['String']['output']>;
  group: Scalars['String']['output'];
  health: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  isPaused: Scalars['Boolean']['output'];
  lastSynced?: Maybe<Scalars['DateTime']['output']>;
  mediaCount: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  sourceType: Platform;
  subredditName?: Maybe<Scalars['String']['output']>;
  tags: Array<Scalars['String']['output']>;
  youtubeHandle?: Maybe<Scalars['String']['output']>;
};

export type SourceLink = {
  __typename?: 'SourceLink';
  hidden: Scalars['Boolean']['output'];
  id: Scalars['String']['output'];
  label?: Maybe<Scalars['String']['output']>;
  platform: Platform;
};

export type SourceLinkInput = {
  hidden: Scalars['Boolean']['input'];
  id: Scalars['String']['input'];
  label?: InputMaybe<Scalars['String']['input']>;
  platform: Platform;
};

export type Subreddit = {
  __typename?: 'Subreddit';
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  displayName: Scalars['String']['output'];
  iconUrl?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  subscriberCount: Scalars['Int']['output'];
};

export type SubredditResult = {
  __typename?: 'SubredditResult';
  description: Scalars['String']['output'];
  displayName: Scalars['String']['output'];
  iconUrl?: Maybe<Scalars['String']['output']>;
  isSubscribed: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  subscriberCount: Scalars['Int']['output'];
};

export type User = {
  __typename?: 'User';
  accountAgeDays?: Maybe<Scalars['Int']['output']>;
  karma?: Maybe<Scalars['Int']['output']>;
  username: Scalars['String']['output'];
};

export type WithIndex<TObject> = TObject & Record<string, any>;
export type ResolversObject<TObject> = WithIndex<TObject>;

export type ResolverTypeWrapper<T> = Promise<T> | T;


export type ResolverWithResolve<TResult, TParent, TContext, TArgs> = {
  resolve: ResolverFn<TResult, TParent, TContext, TArgs>;
};
export type Resolver<TResult, TParent = {}, TContext = {}, TArgs = {}> = ResolverFn<TResult, TParent, TContext, TArgs> | ResolverWithResolve<TResult, TParent, TContext, TArgs>;

export type ResolverFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => Promise<TResult> | TResult;

export type SubscriptionSubscribeFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => AsyncIterable<TResult> | Promise<AsyncIterable<TResult>>;

export type SubscriptionResolveFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => TResult | Promise<TResult>;

export interface SubscriptionSubscriberObject<TResult, TKey extends string, TParent, TContext, TArgs> {
  subscribe: SubscriptionSubscribeFn<{ [key in TKey]: TResult }, TParent, TContext, TArgs>;
  resolve?: SubscriptionResolveFn<TResult, { [key in TKey]: TResult }, TContext, TArgs>;
}

export interface SubscriptionResolverObject<TResult, TParent, TContext, TArgs> {
  subscribe: SubscriptionSubscribeFn<any, TParent, TContext, TArgs>;
  resolve: SubscriptionResolveFn<TResult, any, TContext, TArgs>;
}

export type SubscriptionObject<TResult, TKey extends string, TParent, TContext, TArgs> =
  | SubscriptionSubscriberObject<TResult, TKey, TParent, TContext, TArgs>
  | SubscriptionResolverObject<TResult, TParent, TContext, TArgs>;

export type SubscriptionResolver<TResult, TKey extends string, TParent = {}, TContext = {}, TArgs = {}> =
  | ((...args: any[]) => SubscriptionObject<TResult, TKey, TParent, TContext, TArgs>)
  | SubscriptionObject<TResult, TKey, TParent, TContext, TArgs>;

export type TypeResolveFn<TTypes, TParent = {}, TContext = {}> = (
  parent: TParent,
  context: TContext,
  info: GraphQLResolveInfo
) => Maybe<TTypes> | Promise<Maybe<TTypes>>;

export type IsTypeOfResolverFn<T = {}, TContext = {}> = (obj: T, context: TContext, info: GraphQLResolveInfo) => boolean | Promise<boolean>;

export type NextResolverFn<T> = () => Promise<T>;

export type DirectiveResolverFn<TResult = {}, TParent = {}, TContext = {}, TArgs = {}> = (
  next: NextResolverFn<TResult>,
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => TResult | Promise<TResult>;



/** Mapping between all available schema types and the resolvers types */
export type ResolversTypes = ResolversObject<{
  Boolean: ResolverTypeWrapper<Scalars['Boolean']['output']>;
  Creator: ResolverTypeWrapper<Creator>;
  DateTime: ResolverTypeWrapper<Scalars['DateTime']['output']>;
  FeedConnection: ResolverTypeWrapper<FeedConnection>;
  FeedEdge: ResolverTypeWrapper<FeedEdge>;
  FeedFilters: FeedFilters;
  FeedGroup: ResolverTypeWrapper<FeedGroup>;
  FilterState: ResolverTypeWrapper<FilterState>;
  Float: ResolverTypeWrapper<Scalars['Float']['output']>;
  Handle: ResolverTypeWrapper<Handle>;
  HandleInfo: ResolverTypeWrapper<HandleInfo>;
  HandleStatus: HandleStatus;
  ID: ResolverTypeWrapper<Scalars['ID']['output']>;
  IdentityProfile: ResolverTypeWrapper<IdentityProfile>;
  IdentityProfileInput: IdentityProfileInput;
  ImageCluster: ResolverTypeWrapper<ImageCluster>;
  ImageIngestionResult: ResolverTypeWrapper<ImageIngestionResult>;
  ImageLineage: ResolverTypeWrapper<ImageLineage>;
  Int: ResolverTypeWrapper<Scalars['Int']['output']>;
  Media: ResolverTypeWrapper<Media>;
  MediaType: MediaType;
  Mutation: ResolverTypeWrapper<{}>;
  OriginalImageInfo: ResolverTypeWrapper<OriginalImageInfo>;
  PageInfo: ResolverTypeWrapper<PageInfo>;
  Platform: Platform;
  Query: ResolverTypeWrapper<{}>;
  Relationship: ResolverTypeWrapper<Relationship>;
  RelationshipInput: RelationshipInput;
  RepostInfo: ResolverTypeWrapper<RepostInfo>;
  SavedBoard: ResolverTypeWrapper<SavedBoard>;
  SavedBoardInput: SavedBoardInput;
  SimilarImage: ResolverTypeWrapper<SimilarImage>;
  Source: ResolverTypeWrapper<Source>;
  SourceLink: ResolverTypeWrapper<SourceLink>;
  SourceLinkInput: SourceLinkInput;
  String: ResolverTypeWrapper<Scalars['String']['output']>;
  Subreddit: ResolverTypeWrapper<Subreddit>;
  SubredditResult: ResolverTypeWrapper<SubredditResult>;
  Upload: ResolverTypeWrapper<Scalars['Upload']['output']>;
  User: ResolverTypeWrapper<User>;
}>;

/** Mapping between all available schema types and the resolvers parents */
export type ResolversParentTypes = ResolversObject<{
  Boolean: Scalars['Boolean']['output'];
  Creator: Creator;
  DateTime: Scalars['DateTime']['output'];
  FeedConnection: FeedConnection;
  FeedEdge: FeedEdge;
  FeedFilters: FeedFilters;
  FeedGroup: FeedGroup;
  FilterState: FilterState;
  Float: Scalars['Float']['output'];
  Handle: Handle;
  HandleInfo: HandleInfo;
  ID: Scalars['ID']['output'];
  IdentityProfile: IdentityProfile;
  IdentityProfileInput: IdentityProfileInput;
  ImageCluster: ImageCluster;
  ImageIngestionResult: ImageIngestionResult;
  ImageLineage: ImageLineage;
  Int: Scalars['Int']['output'];
  Media: Media;
  Mutation: {};
  OriginalImageInfo: OriginalImageInfo;
  PageInfo: PageInfo;
  Query: {};
  Relationship: Relationship;
  RelationshipInput: RelationshipInput;
  RepostInfo: RepostInfo;
  SavedBoard: SavedBoard;
  SavedBoardInput: SavedBoardInput;
  SimilarImage: SimilarImage;
  Source: Source;
  SourceLink: SourceLink;
  SourceLinkInput: SourceLinkInput;
  String: Scalars['String']['output'];
  Subreddit: Subreddit;
  SubredditResult: SubredditResult;
  Upload: Scalars['Upload']['output'];
  User: User;
}>;

export type CreatorResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Creator'] = ResolversParentTypes['Creator']> = ResolversObject<{
  aliases?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  avatarUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  bio?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  contextKeywords?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  displayName?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  handles?: Resolver<Array<ResolversTypes['Handle']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  imagePool?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  relationships?: Resolver<Array<ResolversTypes['Relationship']>, ParentType, ContextType>;
  slug?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  verified?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export interface DateTimeScalarConfig extends GraphQLScalarTypeConfig<ResolversTypes['DateTime'], any> {
  name: 'DateTime';
}

export type FeedConnectionResolvers<ContextType = Context, ParentType extends ResolversParentTypes['FeedConnection'] = ResolversParentTypes['FeedConnection']> = ResolversObject<{
  edges?: Resolver<Array<ResolversTypes['FeedEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type FeedEdgeResolvers<ContextType = Context, ParentType extends ResolversParentTypes['FeedEdge'] = ResolversParentTypes['FeedEdge']> = ResolversObject<{
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Media'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type FeedGroupResolvers<ContextType = Context, ParentType extends ResolversParentTypes['FeedGroup'] = ResolversParentTypes['FeedGroup']> = ResolversObject<{
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type FilterStateResolvers<ContextType = Context, ParentType extends ResolversParentTypes['FilterState'] = ResolversParentTypes['FilterState']> = ResolversObject<{
  persons?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  searchQuery?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  sources?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  tags?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type HandleResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Handle'] = ResolversParentTypes['Handle']> = ResolversObject<{
  creator?: Resolver<Maybe<ResolversTypes['Creator']>, ParentType, ContextType>;
  handle?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  health?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  hidden?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  label?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  lastSynced?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  mediaCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType>;
  platform?: Resolver<ResolversTypes['Platform'], ParentType, ContextType>;
  status?: Resolver<ResolversTypes['HandleStatus'], ParentType, ContextType>;
  url?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  username?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  verified?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type HandleInfoResolvers<ContextType = Context, ParentType extends ResolversParentTypes['HandleInfo'] = ResolversParentTypes['HandleInfo']> = ResolversObject<{
  creatorName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  handle?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type IdentityProfileResolvers<ContextType = Context, ParentType extends ResolversParentTypes['IdentityProfile'] = ResolversParentTypes['IdentityProfile']> = ResolversObject<{
  aliases?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  avatarUrl?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  bio?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  contextKeywords?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  imagePool?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  relationships?: Resolver<Array<ResolversTypes['Relationship']>, ParentType, ContextType>;
  sources?: Resolver<Array<ResolversTypes['SourceLink']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type ImageClusterResolvers<ContextType = Context, ParentType extends ResolversParentTypes['ImageCluster'] = ResolversParentTypes['ImageCluster']> = ResolversObject<{
  canonicalMedia?: Resolver<Maybe<ResolversTypes['Media']>, ParentType, ContextType>;
  canonicalSha256?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  firstSeen?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  lastSeen?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  memberImages?: Resolver<Array<ResolversTypes['Media']>, ParentType, ContextType>;
  repostCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type ImageIngestionResultResolvers<ContextType = Context, ParentType extends ResolversParentTypes['ImageIngestionResult'] = ResolversParentTypes['ImageIngestionResult']> = ResolversObject<{
  clusterId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  confidence?: Resolver<Maybe<ResolversTypes['Float']>, ParentType, ContextType>;
  isDuplicate?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  isRepost?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  matchedMethod?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  mediaId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  original?: Resolver<Maybe<ResolversTypes['OriginalImageInfo']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type ImageLineageResolvers<ContextType = Context, ParentType extends ResolversParentTypes['ImageLineage'] = ResolversParentTypes['ImageLineage']> = ResolversObject<{
  clusterId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  mediaId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  original?: Resolver<Maybe<ResolversTypes['Media']>, ParentType, ContextType>;
  reposts?: Resolver<Array<ResolversTypes['RepostInfo']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type MediaResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Media'] = ResolversParentTypes['Media']> = ResolversObject<{
  author?: Resolver<Maybe<ResolversTypes['User']>, ParentType, ContextType>;
  cluster?: Resolver<Maybe<ResolversTypes['ImageCluster']>, ParentType, ContextType>;
  dhash?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  handle?: Resolver<ResolversTypes['HandleInfo'], ParentType, ContextType>;
  height?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  imageUrl?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  isDuplicate?: Resolver<Maybe<ResolversTypes['Boolean']>, ParentType, ContextType>;
  isRepost?: Resolver<Maybe<ResolversTypes['Boolean']>, ParentType, ContextType>;
  mediaType?: Resolver<ResolversTypes['MediaType'], ParentType, ContextType>;
  mimeType?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  phash?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  platform?: Resolver<ResolversTypes['Platform'], ParentType, ContextType>;
  presignedUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  publishDate?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  score?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  sha256?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  sizeBytes?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  sourceUrl?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  storagePath?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  subreddit?: Resolver<Maybe<ResolversTypes['Subreddit']>, ParentType, ContextType>;
  title?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  urlExpiresAt?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  viewCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  width?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type MutationResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Mutation'] = ResolversParentTypes['Mutation']> = ResolversObject<{
  addHandle?: Resolver<ResolversTypes['Handle'], ParentType, ContextType, RequireFields<MutationAddHandleArgs, 'creatorId' | 'platform' | 'url' | 'username'>>;
  createCreator?: Resolver<ResolversTypes['Creator'], ParentType, ContextType, RequireFields<MutationCreateCreatorArgs, 'displayName' | 'name'>>;
  createFeedGroup?: Resolver<ResolversTypes['FeedGroup'], ParentType, ContextType, RequireFields<MutationCreateFeedGroupArgs, 'name'>>;
  createIdentityProfile?: Resolver<ResolversTypes['IdentityProfile'], ParentType, ContextType, RequireFields<MutationCreateIdentityProfileArgs, 'input' | 'userId'>>;
  createRelationship?: Resolver<ResolversTypes['Relationship'], ParentType, ContextType, RequireFields<MutationCreateRelationshipArgs, 'input' | 'profileId'>>;
  createSavedBoard?: Resolver<ResolversTypes['SavedBoard'], ParentType, ContextType, RequireFields<MutationCreateSavedBoardArgs, 'input' | 'userId'>>;
  deleteIdentityProfile?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType, RequireFields<MutationDeleteIdentityProfileArgs, 'id'>>;
  deleteRelationship?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType, RequireFields<MutationDeleteRelationshipArgs, 'profileId' | 'targetId'>>;
  deleteSavedBoard?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType, RequireFields<MutationDeleteSavedBoardArgs, 'id'>>;
  ingestImage?: Resolver<ResolversTypes['ImageIngestionResult'], ParentType, ContextType, RequireFields<MutationIngestImageArgs, 'image'>>;
  removeHandle?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType, RequireFields<MutationRemoveHandleArgs, 'handleId'>>;
  subscribeToSource?: Resolver<ResolversTypes['Source'], ParentType, ContextType, RequireFields<MutationSubscribeToSourceArgs, 'subredditName'>>;
  toggleHandlePause?: Resolver<ResolversTypes['Handle'], ParentType, ContextType, RequireFields<MutationToggleHandlePauseArgs, 'handleId'>>;
  updateHandleStatus?: Resolver<ResolversTypes['Handle'], ParentType, ContextType, RequireFields<MutationUpdateHandleStatusArgs, 'handleId' | 'status'>>;
  updateIdentityProfile?: Resolver<ResolversTypes['IdentityProfile'], ParentType, ContextType, RequireFields<MutationUpdateIdentityProfileArgs, 'id' | 'input'>>;
  updateSavedBoard?: Resolver<ResolversTypes['SavedBoard'], ParentType, ContextType, RequireFields<MutationUpdateSavedBoardArgs, 'id' | 'input'>>;
  verifyHandle?: Resolver<ResolversTypes['Handle'], ParentType, ContextType, RequireFields<MutationVerifyHandleArgs, 'handleId'>>;
}>;

export type OriginalImageInfoResolvers<ContextType = Context, ParentType extends ResolversParentTypes['OriginalImageInfo'] = ResolversParentTypes['OriginalImageInfo']> = ResolversObject<{
  firstSeen?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  mediaId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  postId?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type PageInfoResolvers<ContextType = Context, ParentType extends ResolversParentTypes['PageInfo'] = ResolversParentTypes['PageInfo']> = ResolversObject<{
  endCursor?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  hasNextPage?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type QueryResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Query'] = ResolversParentTypes['Query']> = ResolversObject<{
  checkDuplicate?: Resolver<ResolversTypes['ImageIngestionResult'], ParentType, ContextType, RequireFields<QueryCheckDuplicateArgs, 'image'>>;
  creator?: Resolver<Maybe<ResolversTypes['Creator']>, ParentType, ContextType, RequireFields<QueryCreatorArgs, 'slug'>>;
  creators?: Resolver<Array<ResolversTypes['Creator']>, ParentType, ContextType, Partial<QueryCreatorsArgs>>;
  feed?: Resolver<ResolversTypes['FeedConnection'], ParentType, ContextType, Partial<QueryFeedArgs>>;
  getFeedGroups?: Resolver<Array<ResolversTypes['FeedGroup']>, ParentType, ContextType>;
  getIdentityProfile?: Resolver<Maybe<ResolversTypes['IdentityProfile']>, ParentType, ContextType, RequireFields<QueryGetIdentityProfileArgs, 'id'>>;
  getIdentityProfiles?: Resolver<Array<ResolversTypes['IdentityProfile']>, ParentType, ContextType, Partial<QueryGetIdentityProfilesArgs>>;
  getSavedBoards?: Resolver<Array<ResolversTypes['SavedBoard']>, ParentType, ContextType, RequireFields<QueryGetSavedBoardsArgs, 'userId'>>;
  getSources?: Resolver<Array<ResolversTypes['Source']>, ParentType, ContextType, Partial<QueryGetSourcesArgs>>;
  imageCluster?: Resolver<Maybe<ResolversTypes['ImageCluster']>, ParentType, ContextType, RequireFields<QueryImageClusterArgs, 'clusterId'>>;
  imageLineage?: Resolver<Maybe<ResolversTypes['ImageLineage']>, ParentType, ContextType, RequireFields<QueryImageLineageArgs, 'mediaId'>>;
  searchSubreddits?: Resolver<Array<ResolversTypes['SubredditResult']>, ParentType, ContextType, RequireFields<QuerySearchSubredditsArgs, 'query'>>;
  similarImages?: Resolver<Array<ResolversTypes['SimilarImage']>, ParentType, ContextType, RequireFields<QuerySimilarImagesArgs, 'mediaId'>>;
}>;

export type RelationshipResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Relationship'] = ResolversParentTypes['Relationship']> = ResolversObject<{
  target?: Resolver<Maybe<ResolversTypes['IdentityProfile']>, ParentType, ContextType>;
  targetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  type?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type RepostInfoResolvers<ContextType = Context, ParentType extends ResolversParentTypes['RepostInfo'] = ResolversParentTypes['RepostInfo']> = ResolversObject<{
  confidence?: Resolver<ResolversTypes['Float'], ParentType, ContextType>;
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  media?: Resolver<ResolversTypes['Media'], ParentType, ContextType>;
  postId?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SavedBoardResolvers<ContextType = Context, ParentType extends ResolversParentTypes['SavedBoard'] = ResolversParentTypes['SavedBoard']> = ResolversObject<{
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  filters?: Resolver<ResolversTypes['FilterState'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  userId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SimilarImageResolvers<ContextType = Context, ParentType extends ResolversParentTypes['SimilarImage'] = ResolversParentTypes['SimilarImage']> = ResolversObject<{
  hammingDistance?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  media?: Resolver<ResolversTypes['Media'], ParentType, ContextType>;
  method?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  similarityScore?: Resolver<ResolversTypes['Float'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SourceResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Source'] = ResolversParentTypes['Source']> = ResolversObject<{
  entityId?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  entityName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  group?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  health?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  isPaused?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  lastSynced?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  mediaCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  sourceType?: Resolver<ResolversTypes['Platform'], ParentType, ContextType>;
  subredditName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  tags?: Resolver<Array<ResolversTypes['String']>, ParentType, ContextType>;
  youtubeHandle?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SourceLinkResolvers<ContextType = Context, ParentType extends ResolversParentTypes['SourceLink'] = ResolversParentTypes['SourceLink']> = ResolversObject<{
  hidden?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  label?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  platform?: Resolver<ResolversTypes['Platform'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SubredditResolvers<ContextType = Context, ParentType extends ResolversParentTypes['Subreddit'] = ResolversParentTypes['Subreddit']> = ResolversObject<{
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  displayName?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  iconUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  subscriberCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SubredditResultResolvers<ContextType = Context, ParentType extends ResolversParentTypes['SubredditResult'] = ResolversParentTypes['SubredditResult']> = ResolversObject<{
  description?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  displayName?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  iconUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  isSubscribed?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  subscriberCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export interface UploadScalarConfig extends GraphQLScalarTypeConfig<ResolversTypes['Upload'], any> {
  name: 'Upload';
}

export type UserResolvers<ContextType = Context, ParentType extends ResolversParentTypes['User'] = ResolversParentTypes['User']> = ResolversObject<{
  accountAgeDays?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  karma?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  username?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type Resolvers<ContextType = Context> = ResolversObject<{
  Creator?: CreatorResolvers<ContextType>;
  DateTime?: GraphQLScalarType;
  FeedConnection?: FeedConnectionResolvers<ContextType>;
  FeedEdge?: FeedEdgeResolvers<ContextType>;
  FeedGroup?: FeedGroupResolvers<ContextType>;
  FilterState?: FilterStateResolvers<ContextType>;
  Handle?: HandleResolvers<ContextType>;
  HandleInfo?: HandleInfoResolvers<ContextType>;
  IdentityProfile?: IdentityProfileResolvers<ContextType>;
  ImageCluster?: ImageClusterResolvers<ContextType>;
  ImageIngestionResult?: ImageIngestionResultResolvers<ContextType>;
  ImageLineage?: ImageLineageResolvers<ContextType>;
  Media?: MediaResolvers<ContextType>;
  Mutation?: MutationResolvers<ContextType>;
  OriginalImageInfo?: OriginalImageInfoResolvers<ContextType>;
  PageInfo?: PageInfoResolvers<ContextType>;
  Query?: QueryResolvers<ContextType>;
  Relationship?: RelationshipResolvers<ContextType>;
  RepostInfo?: RepostInfoResolvers<ContextType>;
  SavedBoard?: SavedBoardResolvers<ContextType>;
  SimilarImage?: SimilarImageResolvers<ContextType>;
  Source?: SourceResolvers<ContextType>;
  SourceLink?: SourceLinkResolvers<ContextType>;
  Subreddit?: SubredditResolvers<ContextType>;
  SubredditResult?: SubredditResultResolvers<ContextType>;
  Upload?: GraphQLScalarType;
  User?: UserResolvers<ContextType>;
}>;

