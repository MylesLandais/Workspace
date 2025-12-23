# Feed GraphQL Schema

GraphQL types and operations for the Feed domain.

## Types

### Post

Represents a Reddit post with image content.

**Fields**:
- `id` (ID!): Unique post identifier (Reddit post ID)
- `title` (String!): Post title
- `score` (Int!): Upvote score
- `numComments` (Int!): Number of comments
- `upvoteRatio` (Float!): Upvote ratio (0.0-1.0)
- `url` (String!): Original Reddit URL
- `imageUrl` (String): Direct image URL (null for non-image posts)
- `isImage` (Boolean!): Whether post contains an image
- `mediaType` (String): MIME type (e.g., "image/jpeg")
- `imageWidth` (Int): Image width in pixels
- `imageHeight` (Int): Image height in pixels
- `createdAt` (DateTime!): Post creation timestamp
- `permalink` (String!): Reddit permalink path
- `subreddit` (Subreddit!): Subreddit this post belongs to
- `author` (User): User who posted (null for deleted accounts)
- `media` ([Media!]!): Media nodes linked to this post

### Media

Media file (image, video, gif) linked to a post.

**Fields**:
- `id` (ID!): Unique media identifier
- `url` (String!): Media URL
- `type` (String!): Media type ("image", "video", "gif")
- `format` (String!): File format ("jpeg", "png", "mp4")
- `width` (Int): Width in pixels
- `height` (Int): Height in pixels

### FeedConnection

Cursor-based pagination wrapper for feed queries.

**Fields**:
- `edges` ([FeedEdge!]!): Array of post edges
- `pageInfo` (PageInfo!): Pagination metadata

### FeedEdge

Individual post in paginated feed.

**Fields**:
- `node` (Post!): The post
- `cursor` (String!): Cursor for pagination (ISO 8601 timestamp)

### PageInfo

Pagination metadata.

**Fields**:
- `hasNextPage` (Boolean!): Whether more pages exist
- `endCursor` (String): Cursor for next page

## Queries

### feed

Infinite scroll feed query with cursor pagination.

**Arguments**:
- `cursor` (String): Pagination cursor (ISO 8601 timestamp). Omit for first page.
- `limit` (Int): Number of posts to return (default: 20, max: 100)

**Returns**: `FeedConnection!`

**Example**:
```graphql
query InfiniteFeed($cursor: String, $limit: Int = 20) {
  feed(cursor: $cursor, limit: $limit) {
    edges {
      node {
        id
        title
        imageUrl
        score
        subreddit {
          name
        }
        author {
          username
        }
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### feedBySubreddit

Get posts from a specific subreddit.

**Arguments**:
- `subreddit` (String!): Subreddit name (without "r/")
- `limit` (Int): Number of posts (default: 20, max: 100)

**Returns**: `[Post!]!`

**Example**:
```graphql
query FeedBySubreddit($subreddit: String!, $limit: Int = 20) {
  feedBySubreddit(subreddit: $subreddit, limit: $limit) {
    id
    title
    imageUrl
    score
  }
}
```

## Notes

- All timestamps use ISO 8601 format
- Cursor is the `createdAt` timestamp of the last post in the previous page
- Feed queries filter to `isImage = true` posts only
- Posts are ordered by `createdAt DESC` (newest first)


