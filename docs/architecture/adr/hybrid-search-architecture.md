# Hybrid Search Architecture

## Status

Accepted

## Context

Users need to search across all saved content including:
- Full-text search within article content
- Semantic search for conceptually similar content
- Graph-based discovery of related items through citations, topics, and user behavior
- Filtering by metadata (source, date, tags, reading status)

Traditional full-text search alone cannot capture semantic relationships or leverage the graph structure of our Neo4j database. We need a hybrid approach that combines multiple search strategies.

## Decision

Implement a hybrid search architecture that combines:
1. **Graph traversal** (Neo4j) for relationship-based discovery
2. **Semantic search** (vector embeddings via LiteLLM) for conceptual similarity
3. **Full-text search** (Neo4j full-text indexes) for keyword matching
4. **LLM re-ranking** for intelligent result ordering

## Rationale

**Graph-Native Discovery**: Neo4j excels at finding related content through citations, shared topics, and user reading patterns. This provides context-aware results that pure text search cannot.

**Semantic Understanding**: Vector embeddings capture meaning beyond keywords, enabling "find articles about X" even when X isn't mentioned explicitly.

**Keyword Precision**: Full-text search provides exact keyword matching and phrase queries that semantic search may miss.

**Intelligent Ranking**: LLM re-ranking combines all signals (relevance, popularity, user preferences) to surface the most useful results.

**Leverages Existing Infrastructure**: Uses Neo4j full-text indexes, LiteLLM embeddings (already cached in Valkey), and graph queries we're already running.

**Best-of-Breed**: Each search method excels at different query types, and combining them provides comprehensive coverage.

## Consequences

**Positive**:
- More relevant search results by combining multiple signals
- Leverages graph structure for contextual discovery
- Semantic search finds conceptually related content
- Full-text search provides precise keyword matching
- Re-ranking improves result quality
- Can cache embeddings and graph queries for performance

**Negative**:
- More complex implementation than single search method
- Requires tuning weights/priorities for different search types
- Higher computational cost (multiple search operations + re-ranking)
- Need to maintain consistency between vector embeddings and graph data
- Embedding generation adds latency (mitigated by caching)

**Neutral**:
- Requires monitoring search performance and user satisfaction
- May need to adjust search strategy based on query type
- Vector storage in Valkey adds memory usage

## Alternatives Considered

**Neo4j Full-Text Only**: Simple but misses semantic relationships and doesn't leverage graph structure effectively.

**Vector Search Only**: Good for semantic similarity but misses exact keyword matches and graph relationships.

**Elasticsearch**: Powerful but adds another infrastructure component and doesn't integrate well with Neo4j graph queries.

**Graph + Full-Text Only**: Missing semantic understanding limits ability to find conceptually related content.

## Implementation Notes

### Search Architecture Flow

```python
async def intelligent_search(
    query: str,
    user_id: str,
    filters: dict,
    limit: int = 20
) -> list[dict]:
    # 1. Generate embedding via LiteLLM
    embedding = await litellm.aembedding(
        model="openrouter/text-embedding-3-small",
        input=query
    )
    
    # 2. Semantic search in Valkey (cached vectors)
    similar_ids = await valkey_vector_search(embedding, top_k=50)
    
    # 3. Full-text search in Neo4j
    fulltext_results = await neo4j.fulltext_search(query, limit=50)
    
    # 4. Graph context from Neo4j (related items, citations)
    graph_results = await neo4j.graph_search(query, user_id, limit=50)
    
    # 5. Combine and deduplicate results
    combined = merge_results(similar_ids, fulltext_results, graph_results)
    
    # 6. Re-rank with LLM
    reranked = await rerank_with_llm(query, combined, user_id, limit)
    
    return reranked
```

### Neo4j Full-Text Index Setup

```cypher
// Create full-text index on item content
CREATE FULLTEXT INDEX itemContent FOR (i:Item) 
ON EACH [i.title, i.content, i.summary]

// Query example
CALL db.index.fulltext.queryNodes('itemContent', 'AI agents machine learning')
YIELD node, score
RETURN node.title, score
ORDER BY score DESC
LIMIT 20
```

### Hybrid Query Pattern

```cypher
// Combine full-text search with graph traversal
CALL db.index.fulltext.queryNodes('itemContent', $query)
YIELD node, score AS textScore

// Find related items through graph
MATCH (node)-[:TAGGED_WITH]->(t:Tag)
MATCH (related:Item)-[:TAGGED_WITH]->(t)
WHERE related.id <> node.id

// Apply user context
OPTIONAL MATCH (u:User {id: $user_id})-[:READ]->(related)
WITH node, related, textScore, 
     count(DISTINCT related) as relatedCount,
     count(DISTINCT u) as userReadCount

// Calculate combined score
RETURN node, 
       (textScore * 0.4 + 
        relatedCount * 0.3 + 
        userReadCount * 0.3) as combinedScore
ORDER BY combinedScore DESC
LIMIT 20
```

### Vector Search in Valkey

```python
async def valkey_vector_search(
    query_embedding: list[float],
    top_k: int = 50
) -> list[str]:
    # Get all item embeddings from cache
    keys = await valkey.keys("ai:embeddings:*")
    
    similarities = []
    for key in keys:
        item_id = key.split(":")[-1]
        cached = await valkey.hgetall(key)
        if cached:
            item_embedding = json.loads(cached["vector"])
            similarity = cosine_similarity(query_embedding, item_embedding)
            similarities.append((item_id, similarity))
    
    # Return top K most similar
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [item_id for item_id, _ in similarities[:top_k]]
```

### LLM Re-Ranking

```python
async def rerank_with_llm(
    query: str,
    candidates: list[dict],
    user_id: str,
    limit: int
) -> list[dict]:
    # Get user context from Neo4j
    user_prefs = await neo4j.get_user_preferences(user_id)
    
    # Build prompt for re-ranking
    prompt = f"""Rank these search results by relevance to the query: "{query}"

User preferences: {user_prefs}

Candidates:
{format_candidates(candidates)}

Return the top {limit} most relevant items with brief explanations."""

    response = await litellm.acompletion(
        model="openrouter/google/gemini-flash-1.5",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse and return ranked results
    return parse_ranking_response(response, candidates)
```

### Search Strategy Selection

```python
def select_search_strategy(query: str) -> dict:
    """Choose which search methods to use based on query characteristics."""
    
    # Exact phrase match suggests full-text is most important
    if '"' in query:
        return {
            "fulltext": 0.6,
            "semantic": 0.2,
            "graph": 0.2
        }
    
    # Conceptual query suggests semantic search
    if any(word in query.lower() for word in ["about", "related to", "similar"]):
        return {
            "fulltext": 0.2,
            "semantic": 0.5,
            "graph": 0.3
        }
    
    # Citation or relationship query suggests graph
    if any(word in query.lower() for word in ["cited", "references", "by author"]):
        return {
            "fulltext": 0.1,
            "semantic": 0.2,
            "graph": 0.7
        }
    
    # Default balanced approach
    return {
        "fulltext": 0.3,
        "semantic": 0.4,
        "graph": 0.3
    }
```

### Caching Strategy

```python
async def cached_search(query: str, user_id: str) -> list[dict]:
    # Check cache first
    cache_key = f"search:{hash(query)}:{user_id}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Perform search
    results = await intelligent_search(query, user_id, {})
    
    # Cache for 5 minutes (search results may change frequently)
    await valkey.setex(cache_key, 300, json.dumps(results))
    
    return results
```

### Performance Optimization

- Cache embeddings in Valkey to avoid regenerating for similar queries
- Use Neo4j query result caching for common graph patterns
- Batch embedding generation for multiple queries
- Pre-compute graph relationships for popular items
- Monitor search latency and optimize slow paths

## References

- [Neo4j Full-Text Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)
- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)
- [ADR: AI Agent Architecture](./ai-agent-architecture.md)
- [ADR: Discovery Engine](./discovery-engine.md)

