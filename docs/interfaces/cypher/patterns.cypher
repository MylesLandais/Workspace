# Common Cypher Patterns

Reusable Cypher query patterns for common operations.

## Feed Queries

### Infinite Scroll Feed (Cursor Pagination)

```cypher
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
WHERE p.is_image = true
  AND ($cursor IS NULL OR p.created_utc < datetime($cursor))
OPTIONAL MATCH (u:User)-[:POSTED]->(p)
RETURN p, s.name AS subreddit, u.username AS author
ORDER BY p.created_utc DESC
LIMIT $limit
```

### Feed by Subreddit

```cypher
MATCH (s:Subreddit {name: $subreddit})<-[:POSTED_IN]-(p:Post)
WHERE p.is_image = true
RETURN p
ORDER BY p.created_utc DESC
LIMIT $limit
```

### Posts with Media

```cypher
MATCH (p:Post)-[:HAS_MEDIA]->(m:Media)
WHERE p.id = $postId
RETURN p, collect(m) AS media
```

## Subscription Queries

### Get Sources in Group

```cypher
MATCH (fg:FeedGroup {id: $groupId})-[:CONTAINS]->(s:Source)
OPTIONAL MATCH (s)-[:USING_RULE]->(r:IngestRule)
OPTIONAL MATCH (s)-[:POSTED_IN]->(sub:Subreddit)
RETURN s, r, sub, fg.name AS groupName
ORDER BY s.name
```

### Source Health Status

```cypher
MATCH (s:Source)
WITH s,
  CASE 
    WHEN s.last_synced IS NULL THEN 'red'
    WHEN duration.between(s.last_synced, datetime()) < duration({hours: 1}) THEN 'green'
    WHEN duration.between(s.last_synced, datetime()) < duration({hours: 24}) THEN 'yellow'
    ELSE 'red'
  END AS health
RETURN s, health
ORDER BY s.name
```

### Move Source to Group

```cypher
MATCH (s:Source {id: $sourceId})
MATCH (fg:FeedGroup {id: $groupId})
OPTIONAL MATCH (s)-[old:CONTAINS]-()
DELETE old
CREATE (fg)-[:CONTAINS]->(s)
RETURN s
```

## Data Creation

### Create Post with Relationships

```cypher
MATCH (s:Subreddit {name: $subreddit})
MERGE (u:User {username: coalesce($author, 'deleted')})

CREATE (p:Post {
  id: $id,
  title: $title,
  score: $score,
  num_comments: $numComments,
  upvote_ratio: $upvoteRatio,
  url: $url,
  image_url: $imageUrl,
  is_image: $isImage,
  created_utc: datetime($createdUtc),
  permalink: $permalink
})

CREATE (u)-[:POSTED]->(p)
CREATE (p)-[:POSTED_IN]->(s)

FOREACH (ignoreMe IN CASE WHEN $isImage THEN [1] ELSE [] END |
  CREATE (m:Media {
    url: $imageUrl,
    type: 'image',
    format: 'jpeg'
  })
  CREATE (p)-[:HAS_MEDIA]->(m)
)
```

### Create Source with Rule

```cypher
MATCH (sub:Subreddit {name: $subredditName})
MATCH (fg:FeedGroup {id: $groupId})

CREATE (r:IngestRule {
  id: randomUUID(),
  min_score: $minScore,
  media_only: $mediaOnly,
  min_resolution: $minResolution
})

CREATE (s:Source {
  id: randomUUID(),
  name: $subredditName,
  subreddit_name: $subredditName,
  is_paused: false,
  media_count: 0
})

CREATE (fg)-[:CONTAINS]->(s)
CREATE (s)-[:USING_RULE]->(r)

RETURN s, r
```

## Indexes

### Recommended Indexes

```cypher
// Post indexes
CREATE INDEX post_created_utc IF NOT EXISTS FOR (p:Post) ON (p.created_utc);
CREATE INDEX post_is_image IF NOT EXISTS FOR (p:Post) ON (p.is_image);
CREATE CONSTRAINT post_id_unique IF NOT EXISTS FOR (p:Post) REQUIRE p.id IS UNIQUE;

// Subreddit indexes
CREATE CONSTRAINT subreddit_name_unique IF NOT EXISTS FOR (s:Subreddit) REQUIRE s.name IS UNIQUE;

// Source indexes
CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE;
CREATE INDEX source_subreddit_name IF NOT EXISTS FOR (s:Source) ON (s.subreddit_name);

// FeedGroup indexes
CREATE CONSTRAINT feedgroup_id_unique IF NOT EXISTS FOR (fg:FeedGroup) REQUIRE fg.id IS UNIQUE;
```

## Performance Tips

1. Always use indexes for WHERE clauses on node properties
2. Use OPTIONAL MATCH for nullable relationships
3. Use UNWIND for batch operations
4. Limit result sets early in the query
5. Use CASE expressions for computed values rather than post-processing


