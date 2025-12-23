# Discovery Engine

## Status

Accepted

## Context

Users need to discover new content that:
- Relates to their current reading interests
- Comes from sources similar to ones they already follow
- Is cited or referenced by content they've read
- Covers topics they're learning about
- Is popular or trending in their network
- **Is visually similar to images they've favorited or saved**
- **Matches dimensional requirements (width, height, aspect ratio)**
- **Is organized in boards/collections by other users**

Traditional recommendation systems use collaborative filtering or content-based filtering. Our graph database enables more sophisticated discovery through relationship traversal, citation networks, and topic clustering.

## Decision

Implement a graph-powered discovery engine that combines:
1. **Citation network traversal** - Find content that references or is referenced by user's reading
2. **Topic clustering** - Use community detection algorithms to find emerging themes
3. **Source similarity** - Recommend sources based on shared topics, authors, citations
4. **Collaborative filtering** - "Users like you also read..." using graph relationships
5. **Temporal patterns** - Surface trending content and emerging topics
6. **Personalization** - Adapt recommendations based on user's reading graph and expertise progression
7. **Visual similarity** - Find visually similar images using perceptual hashing and ML embeddings
8. **Dimensional search** - Filter by width, height, aspect ratio for specific use cases
9. **Board-based discovery** - Discover content through Pinterest-style boards and collections
10. **Tag-based discovery** - Leverage Booru-style tag relationships (implications, aliases, categories)

## Rationale

**Graph-Native**: Neo4j excels at relationship traversal, making citation networks and topic relationships natural to query.

**Context-Aware**: Graph structure provides rich context (citations, shared topics, user behavior) that flat databases cannot.

**Multi-Signal**: Combines multiple signals (citations, topics, user behavior, popularity) for better recommendations.

**Scalable**: Graph algorithms (PageRank, community detection) scale well and can be cached.

**Differentiation**: Graph-powered discovery is a key differentiator from competitors using traditional recommendation systems.

**Learning Paths**: Can identify learning paths through content (e.g., "to understand X, read Y, then Z").

## Consequences

**Positive**:
- More relevant recommendations through multi-signal approach
- Leverages graph structure for context-aware discovery
- Enables learning path discovery
- Citation networks surface original sources and related research
- Topic clustering finds emerging themes
- Collaborative filtering improves with more users

**Negative**:
- More complex than simple recommendation algorithms
- Requires tuning weights for different signals
- Graph algorithms can be computationally expensive (mitigated by caching)
- Cold start problem for new users (mitigated by content-based recommendations)

**Neutral**:
- Requires monitoring recommendation quality and user engagement
- May need to adjust algorithms based on user feedback
- Citation data quality depends on source metadata

## Alternatives Considered

**Content-Based Only**: Simple but misses social signals and citation relationships.

**Collaborative Filtering Only**: Requires many users and misses content relationships.

**Third-Party Recommendation Service**: Services like Amazon Personalize would be simpler but less customizable and don't leverage graph structure.

**Machine Learning Models**: Training ML models would provide good recommendations but requires labeled data and doesn't leverage graph structure as effectively.

## Implementation Notes

### Citation Network Discovery

```cypher
// Find content that cites items the user has read
MATCH (u:User {id: $user_id})-[:READ]->(read:Item)
MATCH (cited:Item)-[:CITES]->(read)
WHERE NOT (u)-[:READ]->(cited)
RETURN cited, count(read) as citation_count
ORDER BY citation_count DESC
LIMIT 20

// Find original sources cited by user's reading
MATCH (u:User {id: $user_id})-[:READ]->(read:Item)
MATCH (read)-[:CITES]->(original:Item)
WHERE NOT (u)-[:READ]->(original)
RETURN original, count(read) as times_cited
ORDER BY times_cited DESC
LIMIT 20
```

### Topic Clustering with Community Detection

```cypher
// Use GDS library for community detection
CALL gds.graph.project(
  'contentGraph',
  ['Item', 'Tag'],
  {
    TAGGED_WITH: {
      type: 'TAGGED_WITH',
      orientation: 'UNDIRECTED'
    }
  }
)

// Detect topic communities
CALL gds.louvain.stream('contentGraph')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) as item, communityId
WHERE item:Item
WITH communityId, collect(item) as items
WHERE size(items) > 5  // Only significant communities
RETURN communityId, items[0..10] as sample_items, size(items) as community_size
ORDER BY community_size DESC
```

### Source Similarity Recommendations

```cypher
// Find sources similar to user's subscribed sources
MATCH (u:User {id: $user_id})-[:SUBSCRIBES_TO]->(subscribed:Source)
MATCH (subscribed)-[:PUBLISHES]->(item:Item)-[:TAGGED_WITH]->(t:Tag)
MATCH (similar:Source)-[:PUBLISHES]->(other:Item)-[:TAGGED_WITH]->(t)
WHERE similar.id <> subscribed.id
  AND NOT (u)-[:SUBSCRIBES_TO]->(similar)

WITH similar, count(DISTINCT t) as shared_topics, 
     count(DISTINCT subscribed) as overlap_count
WHERE shared_topics > 3  // Minimum topic overlap

RETURN similar, 
       shared_topics,
       overlap_count,
       (shared_topics * 1.0 + overlap_count * 0.5) as similarity_score
ORDER BY similarity_score DESC
LIMIT 10
```

### Collaborative Filtering

```cypher
// Users like you also read...
MATCH (u:User {id: $user_id})-[:READ]->(read:Item)
MATCH (similar:User)-[:READ]->(read)
WHERE similar.id <> u.id
MATCH (similar)-[:READ]->(recommended:Item)
WHERE NOT (u)-[:READ]->(recommended)

WITH recommended, count(DISTINCT similar) as similar_user_count
ORDER BY similar_user_count DESC
LIMIT 20
```

### Reading Path Discovery

```cypher
// Find learning path: items that build on user's current knowledge
MATCH (u:User {id: $user_id})-[:READ]->(known:Item)
MATCH path = (known)-[:CITES*1..3]->(advanced:Item)
WHERE NOT (u)-[:READ]->(advanced)
  AND length(path) <= 3  // Not too far removed

WITH advanced, 
     min(length(path)) as shortest_path,
     count(path) as path_count
ORDER BY path_count DESC, shortest_path ASC
LIMIT 10
```

### Trending Content Detection

```cypher
// Find trending topics based on recent activity
MATCH (i:Item)-[:TAGGED_WITH]->(t:Tag)
WHERE i.created_at > datetime() - duration('P7D')  // Last 7 days
WITH t, count(i) as recent_count

MATCH (i2:Item)-[:TAGGED_WITH]->(t)
WHERE i2.created_at < datetime() - duration('P7D')
  AND i2.created_at > datetime() - duration('P14D')  // Previous week
WITH t, recent_count, count(i2) as previous_count

WITH t, recent_count, previous_count,
     (recent_count * 1.0 / NULLIF(previous_count, 0)) as growth_rate
WHERE growth_rate > 1.5  // 50% growth
  AND recent_count > 5  // Minimum activity

RETURN t.name, recent_count, growth_rate
ORDER BY growth_rate DESC
LIMIT 20
```

### Personalization Engine

```python
async def get_personalized_recommendations(user_id: str, limit: int = 20) -> list[dict]:
    # Get user's reading graph
    user_graph = await neo4j.get_user_reading_graph(user_id)
    
    # Get multiple recommendation signals
    citation_recs = await get_citation_recommendations(user_id)
    topic_recs = await get_topic_recommendations(user_id, user_graph.topics)
    source_recs = await get_source_recommendations(user_id)
    collaborative_recs = await get_collaborative_recommendations(user_id)
    
    # Combine and deduplicate
    all_recs = merge_recommendations([
        citation_recs,
        topic_recs,
        source_recs,
        collaborative_recs
    ])
    
    # Score with personalization weights
    scored = []
    for rec in all_recs:
        score = calculate_personalized_score(rec, user_graph)
        scored.append({**rec, "score": score})
    
    # Sort and return top N
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]

def calculate_personalized_score(rec: dict, user_graph: dict) -> float:
    score = 0.0
    
    # Topic alignment
    topic_overlap = len(set(rec["topics"]) & set(user_graph["interests"]))
    score += topic_overlap * 10
    
    # Source trust (user has read from similar sources)
    if rec["source_id"] in user_graph["trusted_sources"]:
        score += 20
    
    # Citation relevance
    if rec["cites_user_content"]:
        score += 15
    
    # Popularity (but not too much)
    score += min(rec["popularity"] * 0.1, 5)
    
    # Recency
    days_old = (datetime.now() - rec["created_at"]).days
    score += max(0, 10 - days_old * 0.5)
    
    return score
```

### Expertise Mapping

```cypher
// Track user's expertise progression through topics
MATCH (u:User {id: $user_id})-[:READ]->(i:Item)-[:TAGGED_WITH]->(t:Tag)
WITH t, count(i) as read_count, 
     max(i.created_at) as last_read,
     collect(i)[0..5] as sample_items

// Calculate expertise level
WITH t, read_count, last_read, sample_items,
     CASE
       WHEN read_count > 20 THEN 'expert'
       WHEN read_count > 10 THEN 'intermediate'
       WHEN read_count > 5 THEN 'beginner'
       ELSE 'novice'
     END as expertise_level

RETURN t.name, expertise_level, read_count, last_read, sample_items
ORDER BY read_count DESC
```

### Caching Recommendations

```python
async def get_cached_recommendations(user_id: str) -> list[dict]:
    cache_key = f"recommendations:{user_id}"
    
    # Check cache (5 minute TTL)
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Generate recommendations
    recommendations = await get_personalized_recommendations(user_id)
    
    # Cache for 5 minutes
    await valkey.setex(cache_key, 300, json.dumps(recommendations))
    
    return recommendations
```

### Graph Algorithms Integration

```cypher
// PageRank to find influential sources
CALL gds.graph.project(
  'sourceGraph',
  'Source',
  {
    SIMILAR_TO: {
      type: 'SIMILAR_TO',
      orientation: 'UNDIRECTED',
      properties: 'weight'
    }
  }
)

CALL gds.pageRank.stream('sourceGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS source, score
ORDER BY score DESC
LIMIT 20
```

### Visual Similarity Discovery

```cypher
// Find visually similar images to user's favorites
MATCH (u:User {id: $user_id})-[:FAVORITED]->(fav:MediaItem)
MATCH (fav)-[:SIMILAR_TO {score: $threshold}]->(similar:MediaItem)
WHERE NOT (u)-[:FAVORITED]->(similar)
  AND similar.width = fav.width  // Optional: same dimensions
  AND similar.height = fav.height

RETURN similar, 
       avg(similar.score) as avg_similarity,
       count(fav) as matched_favorites
ORDER BY avg_similarity DESC, matched_favorites DESC
LIMIT 20
```

```python
async def discover_visually_similar(user_id: str, limit: int = 20) -> list[dict]:
    """Discover visually similar content to user's favorites."""
    # Get user's favorited media
    favorites = await neo4j.get_user_favorites(user_id)
    
    similar_items = []
    for favorite in favorites:
        # Find visually similar using perceptual hash
        similar = await find_visually_similar(favorite["id"], threshold=5)
        
        # Also find using ML embeddings
        ml_similar = await find_similar_by_embedding(favorite["id"], top_k=10)
        
        # Combine and deduplicate
        all_similar = merge_similarity_results(similar, ml_similar)
        similar_items.extend(all_similar)
    
    # Deduplicate and rank
    ranked = rank_similar_items(similar_items, user_id)
    return ranked[:limit]
```

### Dimensional Search Discovery

```cypher
// Find content matching user's dimensional preferences
MATCH (u:User {id: $user_id})-[:FAVORITED]->(fav:MediaItem)
WITH u, 
     avg(fav.width) as preferred_width,
     avg(fav.height) as preferred_height,
     avg(fav.aspect_ratio) as preferred_aspect

MATCH (similar:MediaItem)
WHERE similar.width >= preferred_width * 0.9 
  AND similar.width <= preferred_width * 1.1
  AND similar.height >= preferred_height * 0.9
  AND similar.height <= preferred_height * 1.1
  AND NOT (u)-[:FAVORITED]->(similar)

// Match tags from user's favorites
MATCH (fav)-[:HAS_TAG]->(t:Tag)
MATCH (similar)-[:HAS_TAG]->(t)

RETURN similar, count(t) as tag_overlap
ORDER BY tag_overlap DESC
LIMIT 20
```

### Board-Based Discovery

```cypher
// Discover content through boards user follows
MATCH (u:User {id: $user_id})-[:FOLLOWS]->(b:Board)
MATCH (b)-[:CONTAINS]->(s:Section)-[:PINS]->(i:MediaItem)
WHERE NOT (u)-[:FAVORITED]->(i)
  AND i.created_at > datetime() - duration('P7D')  // Recent content

WITH i, count(DISTINCT b) as board_count
ORDER BY board_count DESC, i.score DESC
RETURN i
LIMIT 20
```

```cypher
// Find boards similar to user's created boards
MATCH (u:User {id: $user_id})-[:CREATED]->(user_board:Board)
MATCH (user_board)-[:CONTAINS]->(s:Section)-[:PINS]->(i:MediaItem)
MATCH (other_board:Board)-[:CONTAINS]->(s2:Section)-[:PINS]->(i)
WHERE other_board.id <> user_board.id
  AND NOT (u)-[:FOLLOWS]->(other_board)

WITH other_board, count(i) as shared_items
WHERE shared_items > 5  // Minimum overlap

RETURN other_board, shared_items
ORDER BY shared_items DESC
LIMIT 10
```

### Tag-Based Discovery with Implications

```cypher
// Discover content using tag implications and aliases
MATCH (u:User {id: $user_id})-[:FAVORITED]->(fav:MediaItem)-[:HAS_TAG]->(t:Tag)
MATCH (t)-[:IMPLIES*]->(implied:Tag)
MATCH (recommended:MediaItem)-[:HAS_TAG]->(implied)
WHERE NOT (u)-[:FAVORITED]->(recommended)

// Also check aliases
OPTIONAL MATCH (t)-[:ALIAS_OF*]->(canonical:Tag)
MATCH (recommended2:MediaItem)-[:HAS_TAG]->(canonical)
WHERE NOT (u)-[:FAVORITED]->(recommended2)

WITH coalesce(recommended, recommended2) as item, 
     count(DISTINCT t) as tag_relevance

RETURN item, tag_relevance
ORDER BY tag_relevance DESC
LIMIT 20
```

### Combined Discovery Strategy

```python
async def get_media_recommendations(user_id: str, limit: int = 20) -> list[dict]:
    """Combine multiple discovery signals for media recommendations."""
    # Get recommendations from different sources
    visual_recs = await discover_visually_similar(user_id, limit=10)
    dimensional_recs = await get_dimensional_recommendations(user_id, limit=10)
    board_recs = await get_board_recommendations(user_id, limit=10)
    tag_recs = await get_tag_based_recommendations(user_id, limit=10)
    
    # Combine and score
    all_recs = merge_recommendations([
        visual_recs,
        dimensional_recs,
        board_recs,
        tag_recs
    ])
    
    # Personalize scores
    scored = []
    for rec in all_recs:
        score = calculate_media_score(rec, user_id)
        scored.append({**rec, "score": score})
    
    # Sort and return
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]

def calculate_media_score(rec: dict, user_id: str) -> float:
    """Calculate personalized score for media recommendation."""
    score = 0.0
    
    # Visual similarity
    if rec.get("visual_similarity"):
        score += rec["visual_similarity"] * 20
    
    # Tag overlap
    score += rec.get("tag_overlap", 0) * 10
    
    # Board popularity
    score += rec.get("board_count", 0) * 5
    
    # Quality score
    score += rec.get("quality_score", 0) * 0.1
    
    # Recency
    days_old = (datetime.now() - rec["created_at"]).days
    score += max(0, 10 - days_old * 0.5)
    
    return score
```

## References

- [Neo4j Graph Data Science Library](https://neo4j.com/docs/graph-data-science/)
- [ADR: Hybrid Search Architecture](./hybrid-search-architecture.md)
- [ADR: Neo4j Graph Database](./neo4j-graph-database.md)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)
- [PageRank Algorithm](https://en.wikipedia.org/wiki/PageRank)
- [Louvain Community Detection](https://en.wikipedia.org/wiki/Louvain_method)

