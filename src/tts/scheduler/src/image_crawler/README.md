# Image Crawler with Real-Time Deduplication

Production-grade image crawler with real-time deduplication using Neo4j for graph storage and Valkey/Redis for fast lookups, bloom filters, and vector similarity search.

## Features

- **Real-time deduplication**: dHash and CLIP-based duplicate detection during ingestion
- **Bloom filter**: Fast URL "seen" checks (~1GB for 100M URLs)
- **Priority queue**: Redis sorted set for crawl queue management
- **Quality scoring**: Screenshot detection, resolution analysis, UI element detection
- **Face recognition**: InsightFace-based filtering for target person verification
- **Vector search**: CLIP embeddings with ValkeySearch for semantic similarity
- **Parent-child relationships**: Quality-based promotion of better images

## Architecture

```
[Crawlers] → [URL Frontier] → [Fetch Workers] → [Feature Extractor]
    ↓
[Perceptual Hash Store] → [Similarity Matcher] → [Quality Ranker] → [Index]
```

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- `imagehash` - Perceptual hashing
- `pybloom-live` - Bloom filter
- `opencv-python` - Image processing
- `pytesseract` - OCR
- `insightface` - Face recognition
- `sentence-transformers` - CLIP embeddings
- `beautifulsoup4` - HTML parsing (for general web pages, not Reddit - Reddit uses JSON API via RedditAdapter)

## Usage

### Basic Example

```python
from image_crawler import MasterCrawler
from image_crawler.platforms import RedditCrawler

# Initialize crawler
crawler = MasterCrawler(
    num_workers=4,
    face_similarity_threshold=0.65,
)

# Add platform crawlers
reddit_crawler = RedditCrawler(
    subreddit="BrookeMonk",
    check_interval=1800,  # 30 minutes
)
crawler.add_platform_crawler(reddit_crawler)

# Run crawler
crawler.run(max_urls=1000, max_duration=3600)
```

### With Face Filtering

```python
import numpy as np
from image_crawler import MasterCrawler, FaceFilter

# Extract target face embedding from reference image
face_filter = FaceFilter()
target_img = Image.open("reference.jpg")
target_embedding = face_filter.extract_target_embedding(target_img)

# Initialize crawler with face filtering
crawler = MasterCrawler(
    target_face_embedding=target_embedding,
    face_similarity_threshold=0.65,
)
```

## Configuration

Environment variables:

- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_PASSWORD` - Neo4j password
- `VALKEY_URI` - Valkey/Redis connection URI
- `VALKEY_PASSWORD` - Valkey password
- `CRAWL_BLOOM_CAPACITY` - Bloom filter capacity (default: 10M)
- `DHASH_THRESHOLD` - Hamming distance threshold (default: 5)
- `CLIP_SIMILARITY_THRESHOLD` - Cosine similarity threshold (default: 0.92)
- `FACE_SIMILARITY_THRESHOLD` - Face match threshold (default: 0.65)

## Components

### Storage (`storage.py`)
- Neo4j graph operations for images and relationships
- Parent-child relationship management
- Crawl state tracking

### Vector Store (`vector_store.py`)
- ValkeySearch index for CLIP embeddings
- Vector similarity search (512-dim, cosine distance)
- Batch operations

### URL Frontier (`frontier.py`)
- URL normalization
- Bloom filter for "seen" checks
- Priority queue with Redis sorted sets

### Fetch Worker (`fetch_worker.py`)
- HEAD request pre-checks
- Immediate dHash computation
- CLIP embedding generation
- Quality comparison

### Deduplication (`deduplication.py`)
- dHash-based fast matching
- CLIP embedding similarity
- Quality-based promotion

### Quality Scorer (`quality_scorer.py`)
- Resolution scoring
- Screenshot detection
- UI element detection
- OCR text overlay detection

### Face Filter (`face_filter.py`)
- InsightFace face detection
- Target person verification
- Largest face selection

## Data Models

### Neo4j Schema

- `Image` nodes: Canonical parent images
- `ImageDerivative` nodes: Duplicates linked via `DERIVATIVE_OF`
- `CrawlUrl` nodes: Normalized URLs with crawl state

### Valkey/Redis Structure

- `crawl:bloom` - Bloom filter data
- `crawl:queue` - Priority queue (sorted set)
- `image:dhash:{hash}` - dHash to image ID mapping
- `image:embedding:{id}` - CLIP embeddings with ValkeySearch index

## Performance

- dHash computation: ~5ms per image
- Bloom filter: O(1) lookup, ~1GB for 100M URLs
- CLIP embedding: ~100-200ms per image (GPU recommended)
- Vector search: Sub-millisecond with HNSW index

## License

See main project license.


