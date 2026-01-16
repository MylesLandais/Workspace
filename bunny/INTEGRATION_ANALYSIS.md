# Bunny App Integration - Data Analysis

## Current State

### Your Reddit Data (in our Neo4j)
**Neo4j Connection:** `bolt://localhost:7687`
**Password:** `password` (from jupyter container env)

**Successfully crawled subreddits:**

#### Recent Crawls (Last 7 days)
| Subreddit | Posts | Status |
|-----------|--------|--------|
| unixporn | Not yet | ❌ Need to crawl |
| BunnyGirls | Not yet | ❌ Need to crawl |
| AnimeFigures | 332 posts | ✅ Available |
| MaddieZiegler1 | 37 posts | ✅ Available |
| dancemoms/DanceMoms | 612 posts | ✅ Available |
| Sia | 15 posts | ✅ Available |
| Celebs | 204 posts | ✅ Available |
| OfflinetvGirls | 34 posts | ✅ Available |
| ElsaHosk | 10 posts | ✅ Available |
| KiraKosarinLewd | 20 posts | ✅ Available |
| lululemon | 232 posts | ✅ Available |
| sailormoon | 218 posts | ✅ Available |

**Total Posts in Database:** ~1,500+ posts across 30+ subreddits

---

### Bunny App Data Model

**Located at:** `~/Workspace/Bunny/`

**Tech Stack:**
- Runtime: Bun (JavaScript)
- Database: Neo4j
- Cache: Redis/Valkey
- Environment Manager: Devenv (Nix-based)

**Data Structure:**
```
Media nodes (posts/images/videos)
  ├── Source nodes (subreddit, YouTube channel, etc.)
  ├── Entity/Creator nodes (identity profiles)
  └── ImageCluster nodes (deduplication groups)
```

**Schema Mismatch:**

| Our System | Bunny App Expects |
|------------|-----------------|
| Post nodes | Media nodes |
| Post.title, Post.url, Post.author | Media.title, Media.sourceUrl, Media.handle |
| Post-[:POSTED_IN]->Subreddit | Media-[:HAS_SUBREDDIT]->Subreddit |
| created_utc (string) | publishDate (DateTime) |

---

## Integration Challenge

The Bunny app has its own data model and doesn't directly query our Post nodes. To integrate, we need to:

### Option 1: Extend Bunny Schema (Recommended)
Add GraphQL resolvers that query Post nodes directly:

```graphql
type Query {
  redditPosts(subreddit: String!, limit: Int): [Post!]!
  unixpornPosts(limit: Int): [Post!]!
  bunnyGirlsPosts(limit: Int): [Post!]!
  animeFiguresPosts(limit: Int): [Post!]!
}
```

File to update: `~/Workspace/Bunny/app/server/src/bunny/resolvers.ts`

### Option 2: Create Source Nodes
Add Source nodes for tracked subreddits so Bunny's existing feed system can work:

```cypher
MATCH (s:Subreddit)
WHERE s.name IN ['unixporn', 'BunnyGirls', 'AnimeFigures', ...]
MERGE (src:Source {
  id: 'reddit-' + s.name,
  name: s.name,
  sourceType: 'REDDIT',
  subredditName: s.name,
  url: 'https://reddit.com/r/' + s.name,
  isEnabled: true,
  isActive: true
})
RETURN src
```

### Option 3: Data Migration
Transform Post nodes to Media nodes:

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'unixporn'})
WHERE NOT (p)-[:MIGRATED_AS]->()
MERGE (m:Media {id: p.id})
ON CREATE SET
  m.title = p.title,
  m.sourceUrl = p.url,
  m.publishDate = datetime(p.created_utc),
  m.mediaType = CASE WHEN p.url CONTAINS '.jpg' OR p.url CONTAINS '.png' THEN 'IMAGE'
                 WHEN p.url CONTAINS '.mp4' OR p.url CONTAINS '.gif' THEN 'VIDEO'
                 ELSE 'TEXT' END,
  m.platform = 'REDDIT',
  m.handle = s.name,
  m.score = p.score,
  m.subreddit = s
CREATE (p)-[:MIGRATED_AS]->(m)
RETURN count(m) as migrated
```

---

## Next Steps

### 1. Configure Bunny to Use Local Neo4j

Create or update `~/Workspace/Bunny/.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

### 2. Crawl Missing Subreddits

Run these from our environment:
```bash
# Crawl high priority subreddits for Bunny
python pull_recent_posts.py unixporn --hours 168 --ingest
python pull_recent_posts.py BunnyGirls --hours 168 --ingest
```

### 3. Add Reddit Queries to Bunny

Update `~/Workspace/Bunny/app/server/src/bunny/resolvers.ts` with:

```typescript
const bunnyResolvers: Resolvers = {
  Query: {
    // ... existing queries ...
    
    redditPosts: async (_, { subreddit, limit = 20 }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
          RETURN p
          ORDER BY p.created_utc DESC
          LIMIT $limit
        `;
        
        const result = await session.run(query, { subreddit, limit });
        return result.records.map(r => r.get('p').properties) as any;
      });
    },
  },
}
```

Also update schema: `~/Workspace/Bunny/app/server/src/schema/schema.ts`:

```graphql
type Post {
  id: ID!
  title: String!
  author: String
  score: Int
  num_comments: Int
  url: String!
  selftext: String
  subreddit: String!
  permalink: String
  over_18: Boolean
  upvote_ratio: Float
  created_utc: String
}

extend type Query {
  redditPosts(subreddit: String!, limit: Int): [Post!]!
  unixpornPosts(limit: Int): [Post!]!
  bunnyGirlsPosts(limit: Int): [Post!]!
}
```

### 4. Start Bunny App

```bash
cd ~/Workspace/Bunny
nix develop          # Enter development environment
devenv up             # Start Neo4j, Redis, MySQL
cd app/server
bun run dev           # Start GraphQL server
```

The server will be available at `http://localhost:4000` (check their config)

---

## Files Created

1. `~/Workspace/jupyter/bunny/reddit_bridge.py` - Compatibility checker
2. `~/Workspace/jupyter/bunny/config/bunny_config.json` - Configuration
3. `~/Workspace/jupyter/bunny/INTEGRATION_GUIDE.md` - Integration guide
4. `~/Workspace/jupyter/bunny/INTEGRATION_ANALYSIS.md` - This file

---

## Quick Reference

**Pull posts from our system:**
```bash
cd ~/Workspace/jupyter
NEO4J_URI="bolt://localhost:7687" python pull_recent_posts.py <subreddit> --hours <hours> --ingest
```

**Check Bunny app status:**
```bash
cd ~/Workspace/Bunny
devenv status
```

**Restart Bunny services:**
```bash
cd ~/Workspace/Bunny
devenv down && devenv up
```
