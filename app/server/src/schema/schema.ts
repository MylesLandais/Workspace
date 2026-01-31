export const typeDefs = `
  scalar DateTime

  enum Platform {
    RSS
    REDDIT
    YOUTUBE
    TWITTER
    INSTAGRAM
    TIKTOK
    VSCO
    IMAGEBOARD
  }

  enum MediaType {
    VIDEO
    IMAGE
    TEXT
  }

  enum HandleStatus {
    ACTIVE
    SUSPENDED
    ABANDONED
  }

  scalar Upload

  type HandleInfo {
    name: String!
    handle: String!
    creatorName: String
  }

  type Media {
    id: ID!
    title: String!
    sourceUrl: String!
    publishDate: DateTime!
    imageUrl: String!
    presignedUrl: String
    urlExpiresAt: DateTime
    mediaType: MediaType!
    platform: Platform!
    handle: HandleInfo!
    score: Int
    subreddit: Subreddit
    author: User
    viewCount: Int
    sha256: String
    phash: String
    dhash: String
    width: Int
    height: Int
    sizeBytes: Int
    mimeType: String
    storagePath: String
    cluster: ImageCluster
    isDuplicate: Boolean
    isRepost: Boolean
  }

  type Subreddit {
    name: String!
    displayName: String!
    description: String
    iconUrl: String
    subscriberCount: Int!
    createdAt: DateTime!
  }

  type User {
    username: String!
    karma: Int
    accountAgeDays: Int
  }

  type FeedConnection {
    edges: [FeedEdge!]!
    pageInfo: PageInfo!
  }

  type FeedEdge {
    node: Media!
    cursor: String!
  }

  type PageInfo {
    hasNextPage: Boolean!
    endCursor: String
  }

  type Creator {
    id: ID!
    slug: String!
    name: String!
    displayName: String!
    bio: String
    avatarUrl: String
    verified: Boolean!
    handles: [Handle!]!
    # Bunny extensions
    aliases: [String!]!
    contextKeywords: [String!]!
    imagePool: [String!]!
    relationships: [Relationship!]!
  }

  type Handle {
    id: ID!
    platform: Platform!
    username: String!
    handle: String!
    url: String!
    verified: Boolean!
    status: HandleStatus!
    creator: Creator
    mediaCount: Int!
    lastSynced: DateTime
    health: String!
    # Bunny extensions
    label: String
    hidden: Boolean!
  }

  type FeedGroup {
    id: ID!
    name: String!
    userId: ID
    createdAt: DateTime!
  }

  type Source {
    id: ID!
    name: String!
    subredditName: String
    sourceType: Platform!
    youtubeHandle: String
    twitterHandle: String
    instagramHandle: String
    tiktokHandle: String
    url: String
    rssUrl: String
    iconUrl: String
    description: String
    entityId: String
    entityName: String
    group: String!
    groupId: String
    tags: [String!]!
    isPaused: Boolean!
    isEnabled: Boolean!
    isActive: Boolean!
    lastSynced: DateTime
    mediaCount: Int!
    storiesPerMonth: Int!
    readsPerMonth: Int!
    health: String!
  }

  # Source Management Types
  type SourceStats {
    storiesPerMonth: Int!
    readsPerMonth: Int!
    lastFetched: String
  }

  type OPMLFeed {
    title: String!
    xmlUrl: String!
    htmlUrl: String
    category: String
    description: String
  }

  type OPMLParseResult {
    feeds: [OPMLFeed!]!
    feedCount: Int!
    categories: [String!]!
    errors: [String!]!
  }

  type ImportResult {
    imported: Int!
    skipped: Int!
    failed: Int!
    sources: [Source!]!
    errors: [String!]!
  }

  enum ActivityFilter {
    ALL
    ACTIVE
    INACTIVE
    PAUSED
  }

  input SourceFiltersInput {
    groupId: String
    userId: String
    sourceType: Platform
    activity: ActivityFilter
    searchQuery: String
  }

  input CreateSourceInput {
    name: String!
    sourceType: Platform!
    url: String
    subredditName: String
    youtubeHandle: String
    twitterHandle: String
    instagramHandle: String
    tiktokHandle: String
    groupId: String
    description: String
  }

  input UpdateSourceInput {
    name: String
    description: String
    groupId: String
    isPaused: Boolean
    isEnabled: Boolean
  }

  # Reddit post types for direct Post node queries
  type RedditPost {
    id: ID!
    title: String!
    url: String!
    permalink: String!
    author: String
    score: Int!
    numComments: Int!
    upvoteRatio: Float!
    over18: Boolean!
    selftext: String
    createdAt: DateTime!
    subreddit: String!
    isImage: Boolean!
    imageUrl: String
    imageWidth: Int
    imageHeight: Int
    mediaUrl: String
    isRead: Boolean
  }

  type NodeStats {
    mediaCount: Int!
    postCount: Int!
    subredditCount: Int!
  }

  type Query {
    feed(cursor: String, limit: Int, filters: FeedFilters): FeedConnection!
    creators(query: String, limit: Int): [Creator!]!
    creator(slug: String!): Creator
    getFeedGroups(userId: ID): [FeedGroup!]!
    getSources(groupId: String): [Source!]!
    getUserSources(filters: SourceFiltersInput): [Source!]!
    getSourceById(id: ID!): Source
    parseOPML(content: String!): OPMLParseResult!
    discoverFeeds(url: String!): [OPMLFeed!]!
    searchSubreddits(query: String!): [SubredditResult!]!
    checkDuplicate(image: Upload!): ImageIngestionResult!
    similarImages(mediaId: ID!, limit: Int): [SimilarImage!]!
    imageCluster(clusterId: ID!): ImageCluster
    imageLineage(mediaId: ID!): ImageLineage
    # Bunny queries
    getSavedBoards(userId: ID!): [SavedBoard!]!
    getIdentityProfiles(query: String, limit: Int): [IdentityProfile!]!
    getIdentityProfile(id: ID!): IdentityProfile
    # Reddit post queries
    redditPosts(subreddit: String!, limit: Int, offset: Int): [RedditPost!]!
    debugStats: NodeStats!
  }

  type SubredditResult {
    name: String!
    displayName: String!
    subscriberCount: Int!
    description: String!
    iconUrl: String
    isSubscribed: Boolean!
  }

  type ImageCluster {
    id: ID!
    canonicalSha256: String!
    canonicalMedia: Media
    repostCount: Int!
    firstSeen: DateTime!
    lastSeen: DateTime!
    memberImages: [Media!]!
  }

  type SimilarImage {
    media: Media!
    similarityScore: Float!
    method: String!
    hammingDistance: Int
  }

  type ImageIngestionResult {
    mediaId: ID!
    clusterId: ID!
    isDuplicate: Boolean!
    isRepost: Boolean!
    confidence: Float
    matchedMethod: String
    original: OriginalImageInfo
  }

  type OriginalImageInfo {
    mediaId: ID!
    firstSeen: DateTime!
    postId: String
  }

  type ImageLineage {
    mediaId: ID!
    clusterId: ID!
    original: Media
    reposts: [RepostInfo!]!
  }

  type RepostInfo {
    media: Media!
    postId: String
    createdAt: DateTime!
    confidence: Float!
  }

  # Bunny Types
  type FilterState {
    persons: [String!]!
    sources: [String!]!
    tags: [String!]!
    searchQuery: String!
  }

  type SavedBoard {
    id: ID!
    name: String!
    filters: FilterState!
    createdAt: DateTime!
    userId: ID!
  }

  type IdentityProfile {
    id: ID!
    name: String!
    bio: String!
    avatarUrl: String!
    aliases: [String!]!
    sources: [SourceLink!]!
    contextKeywords: [String!]!
    imagePool: [String!]!
    relationships: [Relationship!]!
  }

  type Relationship {
    targetId: ID!
    type: String!
    target: IdentityProfile
  }

  type SourceLink {
    platform: Platform!
    id: String!
    label: String
    hidden: Boolean!
  }

  input FeedFilters {
    persons: [String!]!
    sources: [String!]!
    tags: [String!]!
    searchQuery: String!
    categories: [String!]!
  }

  input SavedBoardInput {
    name: String!
    filters: FeedFilters!
  }

  input IdentityProfileInput {
    id: ID
    name: String!
    bio: String!
    avatarUrl: String!
    aliases: [String!]!
    sources: [SourceLinkInput!]!
    contextKeywords: [String!]!
    imagePool: [String!]!
    relationships: [RelationshipInput!]!
  }

  input SourceLinkInput {
    platform: Platform!
    id: String!
    label: String
    hidden: Boolean!
  }

  input RelationshipInput {
    targetId: ID!
    type: String!
  }

  type Mutation {
    createCreator(name: String!, displayName: String!): Creator!
    addHandle(
      creatorId: ID!
      platform: Platform!
      username: String!
      url: String!
    ): Handle!
    verifyHandle(handleId: ID!): Handle!
    updateHandleStatus(handleId: ID!, status: HandleStatus!): Handle!
    toggleHandlePause(handleId: ID!): Handle!
    removeHandle(handleId: ID!): Boolean!
    subscribeToSource(subredditName: String!, groupId: String): Source!
    createFeedGroup(name: String!): FeedGroup!
    createUserFeedGroup(userId: ID!, name: String!): FeedGroup!
    # Source Management mutations
    createSource(input: CreateSourceInput!): Source!
    updateSource(id: ID!, input: UpdateSourceInput!): Source!
    deleteSource(id: ID!): Boolean!
    importOPML(feedUrls: [String!]!, groupId: String): ImportResult!
    bulkDeleteSources(ids: [ID!]!): Int!
    toggleSourcePause(id: ID!): Source!
    ingestImage(
      image: Upload!
      postId: String
      subreddit: String
      author: String
      title: String
      createdAt: DateTime
    ): ImageIngestionResult!
    # Bunny mutations
    createSavedBoard(userId: ID!, input: SavedBoardInput!): SavedBoard!
    updateSavedBoard(id: ID!, input: SavedBoardInput!): SavedBoard!
    deleteSavedBoard(id: ID!): Boolean!
    createIdentityProfile(
      userId: ID!
      input: IdentityProfileInput!
    ): IdentityProfile!
    updateIdentityProfile(
      id: ID!
      input: IdentityProfileInput!
    ): IdentityProfile!
    deleteIdentityProfile(id: ID!): Boolean!
    createRelationship(profileId: ID!, input: RelationshipInput!): Relationship!
    deleteRelationship(profileId: ID!, targetId: ID!): Boolean!
  }
`;

export const schema = typeDefs;
