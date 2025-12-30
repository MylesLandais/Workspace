import gql from 'graphql-tag';

export const typeDefs = gql`
  scalar DateTime

  enum Platform {
    REDDIT
    YOUTUBE
    TWITTER
    INSTAGRAM
    TIKTOK
    VSCO
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

  type Media {
    id: ID!
    title: String!
    sourceUrl: String!
    publishDate: DateTime!
    imageUrl: String!
    mediaType: MediaType!
    platform: Platform!
    handle: Handle!
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
  }

  type FeedGroup {
    id: ID!
    name: String!
    createdAt: DateTime!
  }

  type Source {
    id: ID!
    name: String!
    subredditName: String
    sourceType: Platform!
    youtubeHandle: String
    entityId: String
    entityName: String
    group: String!
    tags: [String!]!
    isPaused: Boolean!
    lastSynced: DateTime
    mediaCount: Int!
    health: String!
  }

  type Query {
    feed(cursor: String, limit: Int): FeedConnection!
    creators(query: String, limit: Int): [Creator!]!
    creator(slug: String!): Creator
    getFeedGroups: [FeedGroup!]!
    getSources(groupId: String): [Source!]!
    searchSubreddits(query: String!): [SubredditResult!]!
    checkDuplicate(image: Upload!): ImageIngestionResult!
    similarImages(mediaId: ID!, limit: Int): [SimilarImage!]!
    imageCluster(clusterId: ID!): ImageCluster
    imageLineage(mediaId: ID!): ImageLineage
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

  type Mutation {
    createCreator(name: String!, displayName: String!): Creator!
    addHandle(creatorId: ID!, platform: Platform!, username: String!, url: String!): Handle!
    verifyHandle(handleId: ID!): Handle!
    updateHandleStatus(handleId: ID!, status: HandleStatus!): Handle!
    toggleHandlePause(handleId: ID!): Handle!
    removeHandle(handleId: ID!): Boolean!
    subscribeToSource(subredditName: String!, groupId: String): Source!
    createFeedGroup(name: String!): FeedGroup!
    ingestImage(
      image: Upload!
      postId: String
      subreddit: String
      author: String
      title: String
      createdAt: DateTime
    ): ImageIngestionResult!
  }
`;

