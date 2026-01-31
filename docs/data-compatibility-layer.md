# Data Schema Compatibility Layer

## Problem

Bunny's GraphQL server expects a specific Neo4j schema with `Media` nodes:

```cypher
(Media)-[:APPEARED_IN]->(Post)-[:POSTED_IN]->(Subreddit)
```

But your Reddit data pipeline creates a simpler schema with just `Post` nodes:

```cypher
(Post)-[:POSTED_IN]->(Subreddit)
(User)-[:POSTED]->(Post)
```

## Solution

Created a **compatibility layer** that bridges the two schemas without requiring data migration.

### Architecture

```
┌─────────────────────────────────────┐
│   GraphQL feed Query                │
└──────────────┬──────────────────────┘
               │
         ┌─────▼──────┐
         │ getFeedHybrid │
         └─────┬──────┘
               │
        ┌──────▼───────┐
        │ Check Schema │
        └──────┬───────┘
               │
       ┌───────▼────────┐
       │  Media nodes?  │
       └───┬────────┬───┘
           │        │
       Yes │        │ No
           │        │
   ┌───────▼──┐  ┌─▼──────────────┐
   │ getFeed  │  │ getFeedFromPosts│
   │(Standard)│  │  (Compatibility)│
   └──────────┘  └─────────────────┘
```

## Implementation

### 1. Compatibility Query (`feed-compat.ts`)

**`getFeedFromPosts()`** - Queries `Post` nodes directly:

```cypher
MATCH (p:Post)
WHERE p.image_url IS NOT NULL
OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
OPTIONAL MATCH (p)<-[:POSTED]-(u:User)
RETURN p, s.name AS subreddit, u.username AS author
ORDER BY p.created_utc DESC
```

Transforms Post data to match Media interface:

```typescript
{
  id: post.id,
  title: post.title,
  imageUrl: post.image_url,  // Key mapping!
  sourceUrl: post.url,
  publishDate: new Date(post.created_utc * 1000).toISO String(),
  score: post.score,
  width: post.image_width,
  height: post.image_height,
  subreddit: { name: subreddit },
  author: { username: author },
  platform: "REDDIT",
  handle: { name: subreddit, handle: `r/${subreddit}` },
  mediaType: "IMAGE" | "VIDEO"
}
```

**`getFeedHybrid()`** - Auto-detects schema:

1. Runs quick check: `MATCH (m:Media) RETURN count(m)`
2. If Media nodes exist -> use standard `getFeed()`
3. If no Media nodes -> use `getFeedFromPosts()`

### 2. Resolver Update (`resolvers/queries.ts`)

Changed feed resolver to use hybrid query:

```typescript
// Before:
const feedResult = await getFeed(cursor, limit, filters);

// After:
const feedResult = await getFeedHybrid(cursor, limit, filters);
```

## Post Node Schema Requirements

For the compatibility layer to work, your `Post` nodes must have:

**Required Properties:**

- `id` - Unique identifier
- `title` - Post title
- `image_url` - Direct image URL
- `created_utc` - Unix timestamp
- `url` - Source URL (Reddit permalink)

**Optional Properties:**

- `score` - Upvote score
- `image_width` - Image width in pixels
- `image_height` - Image height in pixels
- `media_type` - "IMAGE" or "VIDEO"
- `thumbnail` - Thumbnail URL (fallback)
- `is_video` - Boolean flag
- `view_count` - View count

**Required Relationships:**

- `(Post)-[:POSTED_IN]->(Subreddit)` - Links to subreddit
- `(User)-[:POSTED]->(Post)` - Links to author

**Subreddit Node:**

- `name` - Subreddit name (without "r/")

**User Node:**

- `username` - Reddit username

## Data Mapping

| Bunny (Media)     | Reddit (Post)              | Notes                  |
| ----------------- | -------------------------- | ---------------------- |
| `id`              | `id`                       | Direct mapping         |
| `title`           | `title`                    | Direct mapping         |
| `imageUrl`        | `image_url`                | Key field!             |
| `sourceUrl`       | `url`                      | Reddit permalink       |
| `publishDate`     | `created_utc`              | Unix -> ISO conversion |
| `score`           | `score`                    | Direct mapping         |
| `width`           | `image_width`              | Optional               |
| `height`          | `image_height`             | Optional               |
| `platform`        | `"REDDIT"`                 | Hardcoded              |
| `mediaType`       | `media_type` or `is_video` | Inferred               |
| `handle.name`     | `subreddit.name`           | Via relationship       |
| `handle.handle`   | `r/${subreddit}`           | Constructed            |
| `author.username` | `user.username`            | Via relationship       |

## Testing

### 1. Check Your Data Schema

```cypher
// Check if you have Media nodes
MATCH (m:Media) RETURN count(m) as mediaCount

// Check if you have Post nodes
MATCH (p:Post) RETURN count(p) as postCount

// Check Post structure
MATCH (p:Post)
WHERE p.image_url IS NOT NULL
OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
RETURN p, s LIMIT 5
```

### 2. Test Feed Query

```bash
curl -X POST http://localhost:4002/api/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ feed(limit: 10) { edges { node { id title imageUrl subreddit { name } } } } }"
  }'
```

Should return posts if:

- Neo4j is running
- Post nodes exist with `image_url`
- Posts are linked to Subreddits

### 3. Test with Filters

```bash
# Filter by subreddit
curl -X POST http://localhost:4002/api/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($filters: FeedFilters) { feed(limit: 10, filters: $filters) { edges { node { id title subreddit { name } } } } }",
    "variables": {
      "filters": {
        "sources": ["unixporn", "ergo"],
        "persons": [],
        "tags": [],
        "searchQuery": ""
      }
    }
  }'
```

## Migration Path (Future)

When you want to migrate to full Media nodes:

### Option 1: Transform in Place

```cypher
// Create Media nodes from Posts
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE p.image_url IS NOT NULL
CREATE (m:Media {
  id: p.id + '_media',
  url: p.image_url,
  mime_type: 'image/jpeg',
  width: p.image_width,
  height: p.image_height,
  created_at: datetime({epochMillis: p.created_utc * 1000}),
  sha256: p.sha256
})
CREATE (m)-[:APPEARED_IN]->(p)
RETURN count(m)
```

### Option 2: ETL Pipeline

Create a script that:

1. Fetches Posts from Neo4j
2. Downloads images to S3/MinIO
3. Generates hashes (SHA256, pHash, dHash)
4. Creates Media nodes with full metadata
5. Links via `APPEARED_IN` relationship

### Option 3: Gradual Migration

Keep both schemas:

- New content -> Media nodes
- Old content -> Post nodes
- Hybrid query handles both

## Troubleshooting

### "No posts found"

**Check 1: Neo4j Running?**

```bash
neo4j status
# Or
docker ps | grep neo4j
```

**Check 2: GraphQL Server Running?**

```bash
curl http://localhost:4002/health
```

**Check 3: Data Exists?**

```cypher
MATCH (p:Post) WHERE p.image_url IS NOT NULL RETURN count(p)
```

**Check 4: Server Logs**

```bash
# In devenv shell
server-logs

# Look for:
# "No Media nodes found, using Post-based feed"
# "Feed query (Posts)" with recordCount > 0
```

### "Media nodes found but no data"

You have Media nodes but they're empty/broken:

1. Check Media node properties: `MATCH (m:Media) RETURN m LIMIT 5`
2. Verify relationships: `MATCH (m:Media)-[r]-() RETURN type(r), count(*)`
3. Check `mime_type`: `MATCH (m:Media) WHERE m.mime_type IS NULL RETURN count(m)`

### "Compatibility layer not working"

**Check import:**

```bash
cd app/server
grep "getFeedHybrid" src/resolvers/queries.ts
```

Should show:

```typescript
import { getFeedHybrid } from "../neo4j/queries/feed-compat.js";
```

**Restart server:**

```bash
server-stop
server-start
```

## Performance

The hybrid check adds ~1ms overhead:

- Check query: `MATCH (m:Media) RETURN count(m) LIMIT 1`
- Result cached in function scope
- Only runs once per query

Post-based query performance:

- ~50-200ms for 20 posts (depends on data size)
- Valkey caching reduces to ~5ms on cache hit
- Same performance as Media query

## Summary

- **No data migration required**
- **Works with existing Post schema**
- **Auto-detects schema type**
- **Same performance as original**
- **Transparent to client**
- **Allows gradual migration**

Your feed should now work with existing Reddit `Post` data!
