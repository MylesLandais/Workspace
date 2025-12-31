# Feed Data Model

Neo4j graph structure for posts, subreddits, users, and media.

## Node Types

### Post

Core content node representing a Reddit post.

**Properties**:
- `id` (string): Reddit post ID (unique identifier)
- `title` (string): Post title
- `score` (integer): Upvote score
- `num_comments` (integer): Comment count
- `upvote_ratio` (float): Upvote ratio (0.0-1.0)
- `url` (string): Original Reddit URL
- `image_url` (string): Direct image URL (denormalized for fast queries)
- `is_image` (boolean): Whether post contains an image
- `media_type` (string): MIME type (e.g., "image/jpeg")
- `image_width` (integer): Image width in pixels
- `image_height` (integer): Image height in pixels
- `created_utc` (datetime): Post creation timestamp
- `permalink` (string): Reddit permalink path
- `selftext` (string): Post body text (empty for image posts)
- `over_18` (boolean): NSFW flag

**Indexes**:
- `Post.created_utc` (for cursor pagination)
- `Post.id` (unique constraint)
- `Post.is_image` (for filtering)

### Subreddit

Reddit community/source.

**Properties**:
- `name` (string): Subreddit name (e.g., "BrookeMonkTheSecond")
- `description` (string): Subreddit description
- `subscribers` (integer): Subscriber count
- `created_at` (datetime): When subreddit was added to our system

**Indexes**:
- `Subreddit.name` (unique constraint)

### User

Reddit user who posted content.

**Properties**:
- `username` (string): Reddit username (or "deleted" for deleted accounts)
- `karma` (integer): User karma
- `account_age_days` (integer): Account age in days

**Indexes**:
- `User.username`

### Media

Separate node for media files (supports galleries).

**Properties**:
- `url` (string): Media URL
- `type` (string): Media type ("image", "video", "gif")
- `format` (string): File format ("jpeg", "png", "mp4")
- `width` (integer): Width in pixels
- `height` (integer): Height in pixels

## Relationships

### POSTED_IN

`(Post)-[:POSTED_IN]->(Subreddit)`

Every post belongs to a subreddit.

### POSTED

`(User)-[:POSTED]->(Post)`

User who created the post. May be null for deleted accounts.

### HAS_MEDIA

`(Post)-[:HAS_MEDIA]->(Media)`

Links post to media nodes. A post can have multiple media nodes (galleries).

## Design Decisions

### Denormalized Image Data

We store `image_url`, `is_image`, and image dimensions directly on the Post node even though we also create Media nodes.

**Why**: Feed queries need to filter and display images quickly. Traversing to Media nodes adds query complexity.

**Pattern**: 
- Use denormalized fields for list/feed queries
- Use Media nodes for detail views and galleries

### Separate Media Nodes

Media is stored as separate nodes linked via `HAS_MEDIA` relationship.

**Why**: 
- Posts can have multiple images (galleries)
- Enables queries like "all images from this subreddit" without loading full posts
- Future support for video/gif media types

## Example Cypher Queries

### Create Post with Relationships

```cypher
MATCH (s:Subreddit {name: $subreddit})
MERGE (u:User {username: coalesce($author, 'deleted')})

CREATE (p:Post {
  id: $id,
  title: $title,
  score: $score,
  image_url: $image_url,
  is_image: true,
  created_utc: datetime($created_utc)
})

CREATE (u)-[:POSTED]->(p)
CREATE (p)-[:POSTED_IN]->(s)

FOREACH (ignoreMe IN CASE WHEN $is_image THEN [1] ELSE [] END |
  CREATE (m:Media {
    url: $image_url,
    type: 'image',
    format: 'jpeg'
  })
  CREATE (p)-[:HAS_MEDIA]->(m)
)
```

### Feed Query (Cursor Pagination)

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE p.is_image = true
  AND ($cursor IS NULL OR p.created_utc < datetime($cursor))
OPTIONAL MATCH (u:User)-[:POSTED]->(p)
RETURN p, s.name AS subreddit, u.username AS author
ORDER BY p.created_utc DESC
LIMIT $limit
```

### Posts by Subreddit

```cypher
MATCH (s:Subreddit {name: $subreddit})<-[:POSTED_IN]-(p:Post)
WHERE p.is_image = true
RETURN p
ORDER BY p.created_utc DESC
LIMIT $limit
```

## Migration Notes

When seeding mock data:
1. Create Subreddit nodes first
2. Create or match User nodes
3. Create Post nodes with relationships
4. Create Media nodes for image posts

See `scripts/seed-mock-data.ts` for complete seeding implementation.






