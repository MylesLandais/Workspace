# Reverse Image Search Tooling

A comprehensive reverse image search service for managing image lookups in feed crawlers and content management systems.

## Overview

The reverse image search service provides multiple strategies for finding and managing images:

1. **URL-based lookup** - Fast exact URL matching
2. **Hash-based lookup** - SHA-256 (exact duplicates) and dHash (near-duplicates)
3. **Vector similarity search** - CLIP embeddings for visual similarity
4. **External API integration** - TinEye, Google Images, etc. (optional)

## Architecture

### Components

```
ReverseImageSearch
├── Neo4j (Graph Database)
│   ├── Image nodes with url, sha256_hash, dhash
│   └── Relationships: Post->HAS_IMAGE->Image, Product->HAS_IMAGE->Image
│
├── Valkey/Redis (Vector Store)
│   ├── CLIP embeddings (512-dim vectors)
│   └── HNSW index for fast similarity search
│
└── Image Hashing
    ├── SHA-256 (exact duplicates)
    └── dHash (perceptual hashing for near-duplicates)
```

### Data Flow

1. **Image Ingestion**:
   - Image URL stored in Neo4j as `Image` node
   - Hashes computed and stored in Neo4j
   - CLIP embedding computed and stored in Valkey

2. **Lookup Process**:
   - Fast path: URL lookup in Neo4j
   - Medium path: Hash lookup (if URL not found)
   - Slow path: Vector similarity search (if hash not found)

3. **Indexing**:
   - After crawling, images are indexed for future search
   - Hash values enable fast duplicate detection
   - Embeddings enable visual similarity matching

## Use Cases

### 1. Feed Management: Check if Image Already Crawled

Before processing a new post/product, check if its images are already in the database:

```python
from feed.services.reverse_image_search import ReverseImageSearch
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
reverse_search = ReverseImageSearch(neo4j=neo4j)

# Check before crawling
image_url = "https://i.redd.it/example.jpg"
result = reverse_search.check_if_crawled(image_url)

if result.found:
    print(f"Already crawled! Found in {len(result.matches)} location(s)")
    # Skip or handle duplicate
else:
    print("New image, safe to crawl")
    # Proceed with crawling
```

### 2. Deduplication: Find All Occurrences

Find all places where an image appears:

```python
result = reverse_search.find_exact_matches(image_url)

for match in result.matches:
    print(f"Found in: {match.source_post_id}")
    print(f"Match type: {match.match_type} (confidence: {match.confidence})")
```

### 3. Source Attribution: Find Original Source

Track where an image first appeared:

```python
result = reverse_search.find_original_source(image_url)

if result.found:
    earliest = result.matches[0]
    print(f"Original source: {earliest.source_post_id}")
    print(f"First seen: {earliest.metadata['earliest_time']}")
```

### 4. Visual Similarity: Find Related Images

Find visually similar images using CLIP embeddings:

```python
# Vector search is automatically used when hash lookup fails
result = reverse_search.find_exact_matches(image_url)

# Results include vector matches with similarity scores
for match in result.matches:
    if match.match_type == "vector":
        print(f"Similar image: {match.image_url}")
        print(f"Similarity: {match.confidence:.2f}")
```

## Integration with Feed Crawlers

### Reddit Crawler Integration

```python
from feed.platforms.reddit import RedditAdapter
from feed.storage.thread_storage import store_thread

reddit = RedditAdapter()
post, comments, raw_post_data = reddit.fetch_thread(permalink)

# Extract images
post_images = reddit.extract_all_images(post, raw_post_data)

# Check each image
new_images = []
for img_url in post_images:
    if not reverse_search.check_if_crawled(img_url).found:
        new_images.append(img_url)

# Store post
if new_images or store_duplicates:
    images = [{"url": url, "source": "post", "post_id": post.id} 
              for url in post_images]
    store_thread(neo4j, post, comments, images, raw_post_data)
    
    # Index new images
    for img_url in new_images:
        reverse_search.index_image(img_url)
```

### Product Crawler Integration

```python
from feed.platforms.depop import DepopAdapter
from feed.storage.product_storage import ProductStorage

depop = DepopAdapter()
product = depop.fetch_product(product_url)

# Check product images
for img_url in product.image_urls:
    result = reverse_search.check_if_crawled(img_url)
    if result.found:
        print(f"Duplicate image found: {img_url}")
        # Handle duplicate (skip, flag, etc.)

# Store product
product_storage.store_product(product)

# Index images
for img_url in product.image_urls:
    reverse_search.index_image(img_url)
```

## Performance Considerations

### Lookup Speed

1. **URL lookup**: ~1-5ms (Neo4j index lookup)
2. **Hash lookup**: ~10-50ms (download + hash computation + Neo4j lookup)
3. **Vector search**: ~50-200ms (download + embedding + Valkey search)

### Optimization Strategies

1. **Batch processing**: Check multiple images in parallel
2. **Caching**: Cache hash results for frequently checked images
3. **Lazy indexing**: Only index images that pass certain criteria
4. **Selective vector search**: Only use vector search for high-value images

### Indexing Strategy

- **Immediate indexing**: Index all images as they're crawled (recommended)
- **Batch indexing**: Index images in batches (for large backlogs)
- **Selective indexing**: Only index images that meet certain criteria

## Configuration

### Neo4j Schema

Ensure Image nodes have hash properties:

```cypher
// Migration: Add hash properties to Image nodes
MATCH (img:Image)
WHERE img.sha256_hash IS NULL
SET img.sha256_hash = "",
    img.dhash = ""
```

### Valkey/Redis Setup

The service automatically creates the vector index on first use. Ensure Valkey is running:

```bash
# Docker
docker run -d -p 6379:6379 valkey/valkey

# Or use existing Redis/Valkey instance
```

### CLIP Model

The service uses `sentence-transformers` with the `clip-ViT-B-32` model. Install:

```bash
pip install sentence-transformers
```

## API Reference

### ReverseImageSearch

#### `check_if_crawled(image_url: str) -> ImageLookupResult`

Fast check if image URL has been crawled. Returns immediately if URL match found.

#### `find_original_source(image_url: str, include_external: bool = False) -> ImageLookupResult`

Find the earliest occurrence of an image in the database.

#### `find_exact_matches(image_url: str, include_external: bool = False) -> ImageLookupResult`

Find all exact and near-exact matches using multiple strategies.

#### `index_image(image_url: str, image_bytes: Optional[bytes] = None, ...) -> bool`

Index an image for future search. Stores hashes in Neo4j and embedding in Valkey.

### ImageLookupResult

- `image_url: str` - The image URL that was searched
- `found: bool` - Whether any matches were found
- `matches: List[ImageMatch]` - List of matches found
- `hashes: Optional[Dict[str, str]]` - Computed hashes (sha256, dhash)
- `embedding_computed: bool` - Whether CLIP embedding was computed

### ImageMatch

- `image_url: str` - Matched image URL
- `match_type: str` - Type of match: 'url', 'sha256', 'dhash', 'vector', 'external'
- `confidence: float` - Confidence score (0.0 to 1.0)
- `source_post_id: Optional[str]` - Reddit post ID if from post
- `source_comment_id: Optional[str]` - Reddit comment ID if from comment
- `source_product_id: Optional[str]` - Product ID if from product
- `metadata: Optional[Dict[str, Any]]` - Additional metadata

## Future Enhancements

1. **External API Integration**: TinEye, Google Images, Bing Visual Search
2. **Fuzzy dHash Matching**: Hamming distance for near-duplicate detection
3. **Batch Operations**: Check/index multiple images efficiently
4. **Caching Layer**: Cache lookup results to reduce database queries
5. **Analytics**: Track image propagation and reuse patterns

## Troubleshooting

### Vector Search Not Working

- Check if `sentence-transformers` is installed
- Verify Valkey/Redis is running and accessible
- Check if CLIP model downloads successfully

### Hash Lookup Not Finding Matches

- Ensure images are indexed with `index_image()`
- Check if Image nodes have `sha256_hash` and `dhash` properties
- Verify hash computation is working (check logs)

### Performance Issues

- Use URL lookup first (fastest)
- Only use vector search when necessary
- Consider batch processing for multiple images
- Monitor Valkey memory usage (embeddings can be large)




