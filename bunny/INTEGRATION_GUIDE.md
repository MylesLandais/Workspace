# Bunny App Integration with Local Reddit Data

## Summary

The Bunny app (in ~/Workspace/Bunny) is a GraphQL-based frontend for browsing social media content, with its own data model separate from our feed system.

## Data Model Comparison

### Our Feed System (Reddit Data)
```
Post nodes
  - id (Reddit post ID)
  - title
  - author
  - score
  - num_comments
  - url
  - selftext
  - subreddit
  - permalink
  - over_18
  - upvote_ratio
  - created_utc
  
Subreddit nodes
  - name
```

### Bunny App Data Model
```
Media nodes (posts/content)
  - id
  - title
  - sourceUrl
  - publishDate
  - imageUrl
  - mediaType (VIDEO/IMAGE/TEXT)
  - platform (REDDIT/YOUTUBE/etc)
  - handle (subreddit, channel, etc)
  - score
  - subreddit (Subreddit node)
  - sha256, phash, dhash (image hashes)
  - isDuplicate, isRepost
  - cluster (ImageCluster)
  - storagePath, mimeType, width, height

Source nodes (data sources like subreddits)
  - id
  - name (subreddit_name, youtube channel, etc)
  - sourceType (REDDIT/YOUTUBE)
  - url
  - subredditName (for Reddit sources)
  - label, hidden
  - mediaCount, storiesPerMonth, readsPerMonth
  - health

Entity/Creator/Identity nodes
  - id, name, type (person)
  - bio, avatarUrl, aliases
  - contextKeywords, imagePool
  - handles (links to Source nodes)
  - relationships
```

## Integration Options

### Option A: Extend Bunny Schema (Recommended)

Add resolvers to Bunny that query our Post nodes directly:

```typescript
// Add to bunny/resolvers.ts
Query: {
  redditPosts: async (_, { subreddit, limit }) => {
    return withSession(async (session) => {
      const query = `
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
        WHERE datetime(p.created_utc) >= datetime() - duration('P30D')
        RETURN p
        ORDER BY p.created_utc DESC
        LIMIT $limit
      `;
      const result = await session.run(query, { subreddit, limit });
      return result.records.map(r => r.get('p').properties);
    });
  },
  
  unixpornPosts: async (_, { limit }) => {
    return withSession(async (session) => {
      const query = `
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'unixporn'})
        RETURN p
        ORDER BY p.created_utc DESC
        LIMIT $limit
      `;
      const result = await session.run(query, { limit });
      return result.records.map(r => r.get('p').properties);
    });
  },
  
  bunnyGirlsPosts: async (_, { limit }) => {
    return withSession(async (session) => {
      const query = `
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'BunnyGirls'})
        RETURN p
        ORDER BY p.created_utc DESC
        LIMIT $limit
      `;
      const result = await session.run(query, { limit });
      return result.records.map(r => r.get('p').properties);
    });
  },
}
```

### Option B: Data Migration

Create migration script to duplicate our Posts as Media nodes that Bunny expects:

```cypher
// Migrate recent Reddit posts to Media nodes
MATCH (p:Post)
WHERE datetime(p.created_utc) >= datetime() - duration('P30D')
AND NOT (p)-[:MIGRATED_AS]->()
OPTIONAL MATCH (s:Subreddit {name: p.subreddit})
MERGE (m:Media {id: p.id})
ON CREATE SET
  m.title = p.title,
  m.sourceUrl = p.url,
  m.publishDate = p.created_utc,
  m.mediaType = CASE WHEN p.url CONTAINS '.jpg' OR p.url CONTAINS '.png' OR p.url CONTAINS '.gif' THEN 'IMAGE'
               WHEN p.url CONTAINS '.mp4' OR p.url CONTAINS '.webm' THEN 'VIDEO'
               ELSE 'TEXT' END,
  m.platform = 'REDDIT',
  m.handle = p.subreddit,
  m.score = p.score,
  m.subreddit = s
CREATE (p)-[:MIGRATED_AS]->(m)
RETURN count(m) as migrated
```

### Option C: Source Node Integration

Create Source nodes for tracked subreddits in Bunny's model:

```cypher
// Create Source nodes for subreddits we're tracking
MATCH (s:Subreddit)
WHERE s.name IN ['unixporn', 'BunnyGirls', 'AnimeFigures', 
                  'Celebs', 'OfflinetvGirls', 'ElsaHosk',
                  'KiraKosarinLewd', 'lululemon', 'sailormoon',
                  'dancemoms', 'Dance', 'MaddieZiegler1', 'Sia']
MERGE (src:Source {
  id: 'reddit-' + s.name,
  name: s.name,
  sourceType: 'REDDIT',
  subredditName: s.name,
  url: 'https://reddit.com/r/' + s.name,
  isEnabled: true,
  isActive: true,
  status: 'active'
})
MERGE (src)-[:TRACKS_SUBREDDIT]->(s)
RETURN src
```

## Current Data Availability

### Subreddits in our Neo4j (from recent crawls)

**High Priority:**
- unixporn: Posts available (need to crawl)
- BunnyGirls: Posts available (need to crawl)
- AnimeFigures: 332 posts (7 days)
- Celebs: 204 posts (7 days)
- OfflinetvGirls: 34 posts (7 days)
- ElsaHosk: 10 posts (7 days)

**Maddie Ziegler Related:**
- dancemoms: 612 posts (30 days)
- MaddieZiegler1: 37 posts (30 days)
- Sia: 15 posts (30 days)

**Lifestyle/Others:**
- lululemon: 232 posts (7 days) - includes erewhon collab
- sailormoon: 218 posts (7 days)
- Dance: 11 posts (7 days)
- Music: 976 posts (14 days)

## Recommended Next Steps

1. **Configure Bunny to use local Neo4j**
   - Update ~/Workspace/Bunny/devenv.yaml or create local override
   - Set NEO4J_URI to `bolt://localhost:7687`
   - Set NEO4J_USERNAME to `neo4j`
   - Set NEO4J_PASSWORD to `localpassword`

2. **Choose integration approach:**
   - **Option A** is fastest: Add Post queries to Bunny resolvers
   - Map Post properties to Media GraphQL types

3. **Crawl missing subreddits:**
   - Run pull_recent_posts for unixporn and BunnyGirls
   - These are high priority for Bunny app

4. **Test integration:**
   - Query posts from Bunny GraphQL API
   - Verify Post nodes are accessible
   - Check if data model mapping works correctly

## Configuration Updates Needed

### For Bunny App (~/Workspace/Bunny/)

1. Update environment variables:
   ```bash
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USERNAME="neo4j"
   export NEO4J_PASSWORD="localpassword"
   ```

2. Or update devenv.yaml:
   ```yaml
   neo4j:
     uri: "bolt://localhost:7687"
     username: "neo4j"
     password: "localpassword"
   ```

### For Our System

1. Continue crawling subreddits Bunny is interested in
2. Ensure Post nodes have all required fields
3. Consider adding Media nodes for better integration

## Connection Details

**Our Neo4j:** `bolt://localhost:7687`
**Database:** `neo4j`
**Status:** Running (Docker container)

**Bunny Default:** Cloud instance (neo4j+s://your-instance.databases.neo4j.io)
**Need to:** Update to use local instance
