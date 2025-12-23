# Media Tagging and Visual Search

## Status

Accepted

## Context

Users need to discover and organize image/media content with:
- Duplicate detection (same image posted multiple times)
- Visual similarity search (find similar images)
- Efficient storage and retrieval of image metadata

Traditional text-based search is insufficient for media discovery. We need visual understanding and duplicate detection to improve content organization and reduce storage overhead.

## Decision

Implement a visual search and deduplication system that combines:
1. **Image hashing** - Hash-based duplicate detection stored on Post nodes in Neo4j
2. **Visual similarity search** - CLIP embeddings stored in Valkey for fast similarity queries
3. **Deduplication** - Identify duplicate posts sharing the same image URL or hash
4. **Metadata storage** - Store image URLs, dimensions, and source information in Neo4j

## Rationale

**Image Hashing**: Simple and efficient way to detect exact duplicate images. Fast lookups using Neo4j indexes.

**CLIP Embeddings**: State-of-the-art visual similarity search. Enables finding visually similar content even when images differ slightly.

**Valkey Storage**: Fast vector similarity search using Valkey's vector search capabilities. Separates hot-path similarity queries from graph queries.

**Deduplication**: Identifies duplicate posts sharing the same image, improving feed quality and reducing redundant content.

**Hybrid Approach**: Neo4j for structured metadata and relationships, Valkey for fast vector similarity search.

## Consequences

**Positive**:
- Efficient duplicate detection reduces storage and improves feed quality
- Visual similarity enables content discovery beyond text search
- Fast vector search using Valkey for similarity queries
- Simple architecture without complex tag relationship management

**Negative**:
- Visual similarity requires ML models (CLIP embeddings) with computational cost
- No hierarchical tagging system (future enhancement)
- No board/collection management (future enhancement)
- Image hashing only detects exact duplicates, not near-duplicates

**Neutral**:
- Requires tuning similarity thresholds for CLIP embeddings
- May need to adjust CLIP model for different content types
- Deduplication quality depends on hash algorithm and image preprocessing

## Alternatives Considered

**Booru-Style Tagging**: Comprehensive tagging system with relationships, but adds significant complexity and maintenance overhead. Deferred to future enhancement.

**Perceptual Hashing Only**: Simpler than CLIP embeddings but less accurate for visual similarity. CLIP provides better semantic understanding.

**Neo4j Vector Search**: Storing embeddings in Neo4j would unify storage but Valkey provides better performance for vector similarity queries.

**External Image Deduplication Service**: Using third-party services would be simpler but reduces control and adds external dependencies.

## Implementation Notes

### Neo4j Graph Schema for Posts

```cypher
// Post nodes with image metadata
(:Post {
  id: String (unique),
  title: String,
  url: String (image URL),
  image_hash: String (hash for duplicate detection),
  created_utc: DateTime,
  score: Integer,
  subreddit: String
})

// Relationships
(:Post)-[:POSTED_IN]->(:Subreddit)

// Indexes for duplicate detection
CREATE INDEX post_image_hash_index FOR (p:Post) ON (p.image_hash);
CREATE INDEX post_url_index FOR (p:Post) ON (p.url);
```

### Image Hash Deduplication

```cypher
// Find duplicate posts by image hash
MATCH (p:Post)
WHERE p.image_hash IS NOT NULL AND p.image_hash <> ""
WITH p.image_hash as image_hash, collect(p) as posts
WHERE size(posts) > 1
RETURN image_hash,
       size(posts) as duplicate_count,
       [post IN posts | {
           id: post.id,
           title: post.title,
           subreddit: [(post)-[:POSTED_IN]->(s) | s.name][0],
           url: post.url
       }] as duplicate_posts
ORDER BY duplicate_count DESC

// Find duplicate posts by image URL
MATCH (p:Post)
WHERE p.url IS NOT NULL AND p.url <> ""
WITH p.url as image_url, collect(p) as posts
WHERE size(posts) > 1
RETURN image_url,
       size(posts) as duplicate_count,
       [post IN posts | {
           id: post.id,
           title: post.title,
           subreddit: [(post)-[:POSTED_IN]->(s) | s.name][0]
       }] as duplicate_posts
ORDER BY duplicate_count DESC
```

### Visual Similarity Search with CLIP Embeddings

```python
import numpy as np
import redis
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

# Initialize Valkey client
r = redis.Redis(host='localhost', port=6379)
INDEX_NAME = "clip_embeddings_idx"
VECTOR_DIM = 512
DOC_PREFIX = "img:"

def create_index(r, idx_name, dim):
    """Create ValkeySearch index for CLIP embeddings."""
    try:
        r.ft(idx_name).info()
        print(f"Index '{idx_name}' already exists.")
    except redis.exceptions.ResponseError:
        schema = (
            TagField("id"),
            VectorField("embedding",
                "HNSW", {
                    "TYPE": "FLOAT32",
                    "DIM": dim,
                    "DISTANCE_METRIC": "COSINE"
                }
            )
        )
        definition = IndexDefinition(prefix=[DOC_PREFIX], index_type=IndexType.HASH)
        r.ft(idx_name).create_index(schema, definition=definition)
        print(f"Created index '{idx_name}'.")

def store_embedding(image_id: str, embedding: np.ndarray):
    """Store CLIP embedding in Valkey."""
    vector_bytes = embedding.astype(np.float32).tobytes()
    key = f"{DOC_PREFIX}{image_id}"
    
    r.hset(key, mapping={
        "id": image_id,
        "embedding": vector_bytes,
        "timestamp": datetime.now().isoformat(),
    })

def search_similar(query_vector: np.ndarray, k: int = 5) -> list[dict]:
    """Find similar images using CLIP embeddings."""
    query_bytes = query_vector.astype(np.float32).tobytes()
    
    q = Query(f"*=>[KNN {k} @embedding $vec AS score]")\
        .sort_by("score")\
        .return_fields("id", "score")\
        .dialect(2)
    
    res = r.ft(INDEX_NAME).search(q, query_params={"vec": query_bytes})
    
    results = []
    for doc in res.docs:
        results.append({
            "image_id": doc.id,
            "similarity": float(doc.score)
        })
        # Fetch full node from Neo4j using doc.id
    
    return results
```

### Image Hash Computation

```python
import hashlib
from PIL import Image

def compute_image_hash(image_path: str) -> str:
    """Compute hash for image duplicate detection."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
        return hashlib.sha256(image_data).hexdigest()

def store_post_with_hash(post_data: dict, image_hash: str):
    """Store post with image hash in Neo4j."""
    query = """
    MERGE (p:Post {id: $post_id})
    SET p.title = $title,
        p.url = $url,
        p.image_hash = $image_hash,
        p.created_utc = $created_utc,
        p.score = $score
    WITH p
    MERGE (s:Subreddit {name: $subreddit})
    MERGE (p)-[:POSTED_IN]->(s)
    RETURN p
    """
    neo4j.execute_write(query, parameters={
        "post_id": post_data["id"],
        "title": post_data["title"],
        "url": post_data["url"],
        "image_hash": image_hash,
        "created_utc": post_data["created_utc"],
        "score": post_data["score"],
        "subreddit": post_data["subreddit"]
    })
```

## Future Enhancements

The following features are planned but not yet implemented:
- **Booru-style tagging system** - Hierarchical tags with relationships, implications, and aliases
- **Dimensional search** - Filter by width, height, aspect ratio
- **Board/collection system** - Pinterest-style organization with auto-query matching
- **Quality scoring** - Engagement-based quality metrics

## References

- [ADR: Unified Ingestion Layer](./unified-ingestion-layer.md)
- [ADR: Neo4j Graph Database](./neo4j-graph-database.md)
- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)
- [CLIP Model](https://openai.com/research/clip)
- Implementation: `notebooks/VKSearch_Cache.py`
- Implementation: `src/feed/storage/migrations/005_post_image_hash.cypher`

