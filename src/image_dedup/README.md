# Image Deduplication System

A scalable image deduplication system for Reddit content using Valkey (in-memory cache) + Neo4j (graph database) architecture.

## Features

- **Exact duplicate detection** using SHA-256 hashing
- **Near-duplicate detection** using perceptual hashing (pHash, dHash)
- **Cluster management** for grouping similar images
- **Lineage tracking** to trace image reposts
- **CLIP embeddings** for semantic similarity (optional)
- **Fast lookups** via Valkey bucketing system
- **Query and analytics** APIs

## Architecture

```
Incoming Image
    ↓
1. Compute hashes (SHA-256, pHash, dHash)
    ↓
2. Check Valkey for exact match (SHA-256)
    ↓
3. Check Valkey for near-duplicates (pHash buckets)
    ↓
4. [Optional] CLIP semantic check
    ↓
5. Persist to Neo4j (ImageFile + relationships)
    ↓
6. Update Valkey indexes
```

## Usage

### Basic Usage

```python
from image_dedup import ImageDeduplicator, IngestRequest

# Initialize deduplicator
deduplicator = ImageDeduplicator(
    storage_path="/path/to/storage",
    enable_clip=True,  # Optional CLIP embeddings
)

# Ingest an image
request = IngestRequest(
    image_bytes=image_data,
    post_id="t3_abc123",
    source="reddit",
    metadata={
        "subreddit": "memes",
        "author": "user123",
        "title": "Funny meme",
        "created_at": datetime.utcnow(),
    }
)

result = deduplicator.ingest_image(request)

if result.is_duplicate:
    print(f"Duplicate found! Cluster: {result.cluster_id}")
    print(f"Confidence: {result.confidence}")
    print(f"Method: {result.matched_method}")
```

### Integration with Feed Pipeline

The deduplication system is automatically integrated into the feed ingestion pipeline. Enable it by setting:

```python
from feed.polling.engine import PollingEngine

engine = PollingEngine(
    platform=reddit_adapter,
    neo4j=neo4j_connection,
    enable_deduplication=True,
    deduplication_storage_path="/path/to/storage",
)
```

### Querying Clusters and Lineage

```python
from image_dedup import ImageQueries

queries = ImageQueries()

# Get cluster information
cluster_info = queries.get_cluster_info("cluster-uuid", include_members=True)

# Get image lineage
lineage = queries.get_image_lineage("image-uuid")

# Search similar images
similar = queries.search_similar_images("image-uuid", limit=10)
```

### Analytics

```python
from image_dedup import ImageAnalytics

analytics = ImageAnalytics()

# Get most reposted images
top_reposts = analytics.get_most_reposted_images(limit=50)

# Get daily statistics
stats = analytics.get_daily_statistics()

# Get subreddit statistics
subreddit_stats = analytics.get_subreddit_statistics()
```

## Configuration

Set environment variables:

```bash
IMAGE_DEDUP_STORAGE_PATH=/home/jovyan/storage/images
IMAGE_DEDUP_PHASH_THRESHOLD=10
IMAGE_DEDUP_DHASH_THRESHOLD=5
IMAGE_DEDUP_CLIP_THRESHOLD=0.95
IMAGE_DEDUP_BUCKET_BITS=16
```

## Neo4j Schema Setup

Run the schema migration:

```cypher
:source src/image_dedup/schema/neo4j_schema.cypher
```

Or manually execute the Cypher queries in `schema/neo4j_schema.cypher`.

## Components

- **ImageHasher**: Computes SHA-256, pHash, dHash
- **ImageStorage**: Filesystem storage for images
- **DuplicateDetector**: Fast duplicate detection via Valkey
- **ClusterManager**: Neo4j cluster operations
- **ImageDeduplicator**: Main orchestrator
- **ImageQueries**: Query functions
- **ImageAnalytics**: Analytics functions
- **CLIPEmbedder**: CLIP embedding computation

## Performance Targets

- Duplicate check latency: < 50ms (95th percentile)
- Ingestion throughput: > 100 images/sec
- Memory usage: < 100 bytes/image in Valkey
- Query latency: < 200ms for complex lineage queries

## Dependencies

- `imagehash>=4.3.1` - Perceptual hashing
- `Pillow>=10.0.0` - Image processing
- `sentence-transformers>=2.2.0` - CLIP embeddings (optional)
- `neo4j>=5.0.0` - Graph database
- `redis>=5.0.0` - Valkey/Redis client

## Testing

See test files in `tests/` directory:

- `test_hasher.py` - Hash computation tests
- `test_detector.py` - Duplicate detection tests
- `test_cluster_manager.py` - Cluster management tests







