# imageboard /b/ Archiver System

A modern, scalable archiving system for imageboard boards built with Python, Valkey, Neo4j, MinIO, and GraphQL.

## Architecture

The system consists of three main services that work together:

1. **Catalog Poller** - Continuously monitors board catalogs, detects new threads, and publishes events
2. **Media Downloader** - Downloads thumbnails/full images, deduplicates by hash, stores in MinIO
3. **Ingestion Processor** - Parses posts, extracts relationships (quotes/replies), stores in Neo4j graph

### Data Flow

```
imageboard API → Catalog Poller → Valkey Queue → Media Downloader → MinIO
                                      ↓
                              Ingestion Processor → Neo4j Graph
```

## Components

### Catalog Poller (`catalog_poller.py`)

- Polls `/boards/{board}/catalog.json` every 30-60 seconds
- Tracks active thread IDs
- Detects new threads and archived threads
- Publishes events via Valkey pubsub
- Queues thread IDs for processing

**Usage:**
```python
from feed.archivers.catalog_poller import CatalogPoller
import asyncio

poller = CatalogPoller(board="b", poll_interval=45)
asyncio.run(poller.run())
```

### Media Downloader (`media_downloader.py`)

- Consumes thread IDs from Valkey queue
- Downloads thumbnails (default) and optionally full images
- Computes MD5/SHA256 hashes for deduplication
- Stores media in MinIO with original filenames (tim + ext)
- Indexes by hash to prevent duplicates

**Usage:**
```python
from feed.archivers.media_downloader import MediaDownloader
import asyncio

downloader = MediaDownloader(
    board="b",
    download_thumbs=True,
    download_full=False,  # Set True for full images (high storage)
)
asyncio.run(downloader.run(num_workers=2))
```

### Ingestion Processor (`ingestion_processor.py`)

- Consumes thread IDs from Valkey queue
- Fetches thread JSON from imageboard API
- Parses posts and extracts quotes (>>123456 patterns)
- Creates Neo4j graph:
  - `Thread` nodes
  - `Post` nodes
  - `QUOTES` relationships (post → quoted post)
  - `REPLIES_TO` relationships (reply → OP)

**Usage:**
```python
from feed.archivers.ingestion_processor import IngestionProcessor
import asyncio

processor = IngestionProcessor(board="b")
asyncio.run(processor.run(num_workers=2))
```

### Orchestrator (`orchestrator.py`)

Runs all three services concurrently for easy deployment.

**Usage:**
```python
from feed.archivers.orchestrator import ArchiverOrchestrator
import asyncio

orchestrator = ArchiverOrchestrator(
    board="b",
    poll_interval=45,
    download_thumbs=True,
    download_full=False,
)
asyncio.run(orchestrator.run())
```

## Setup

### 1. Environment Variables

Add to your `.env` file:

```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_REGION=us-east-1
MINIO_SECURE=false

# Neo4j (already configured)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Valkey (already configured)
VALKEY_URI=redis://localhost:6379
VALKEY_PASSWORD=
```

### 2. Start Services

```bash
# Start MinIO, Valkey, Neo4j via docker-compose
docker compose up -d minio valkey

# Or use existing docker-compose.yml which includes all services
docker compose up -d
```

### 3. Run Archiver

**Option A: Use orchestrator (recommended)**
```bash
python -m feed.archivers.orchestrator b --thumbs --interval 45
```

**Option B: Run services separately**
```bash
# Terminal 1: Catalog Poller
python -m feed.archivers.catalog_poller b --interval 45

# Terminal 2: Media Downloader
python -m feed.archivers.media_downloader b --thumbs

# Terminal 3: Ingestion Processor
python -m feed.archivers.ingestion_processor b
```

## Storage

### MinIO Buckets

- `imageboard-{board}-thumbs/` - Thumbnail images
- `imageboard-{board}-images/` - Full images (if enabled)

Objects are stored with original imageboard filenames: `{tim}{ext}`

### Neo4j Graph Schema

```
(:Thread {board, thread_id, subject, post_count, ...})
  <-[:POSTED_IN]-
(:Post {id, post_no, comment, media_url, ...})
  -[:QUOTES]->
(:Post)
  -[:REPLIES_TO]->
(:Post)
```

### Valkey Keys

- `imageboard:{board}:threads:queue` - List of thread IDs to process
- `imageboard:{board}:threads:seen` - Set of seen thread IDs
- `imageboard:{board}:threads:processed` - Set of processed thread IDs
- `imageboard:{board}:media:seen` - Set of processed media
- `imageboard:{board}:media:hash_index` - Hash → object mapping
- `imageboard:{board}:events` - Pubsub channel for events

## Querying Data

### Neo4j Cypher Queries

**Find most quoted posts:**
```cypher
MATCH (p:Post)-[:QUOTES]->(q:Post)
WITH q, count(p) as quote_count
RETURN q.id, q.comment, quote_count
ORDER BY quote_count DESC
LIMIT 10
```

**Find reply chains:**
```cypher
MATCH path = (p:Post)-[:REPLIES_TO*]->(op:Post)
WHERE op.post_no = start(relationships(path)[0]).post_no
RETURN path
LIMIT 10
```

**Find threads with most activity:**
```cypher
MATCH (t:Thread)<-[:POSTED_IN]-(p:Post)
WITH t, count(p) as post_count
RETURN t.thread_id, t.subject, post_count
ORDER BY post_count DESC
LIMIT 20
```

## Performance Considerations

### For /b/ Volume

- **Thumbnails only**: ~10-50 GB/month
- **Full media**: Hundreds of GB/month
- **Poll interval**: 45 seconds recommended (balance between coverage and rate limits)
- **Workers**: 2-4 workers per service for parallel processing

### Rate Limiting

- imageboard uses Cloudflare and may rate limit aggressive polling
- Random delays between requests (1-3 seconds)
- Rotate user-agents if needed
- Use residential proxies if banned

## Analytics Enhancements

The graph structure enables powerful analytics:

- **Influence networks**: PageRank on quote/reply graph
- **Topic clustering**: Embed comments → vector search
- **Trend detection**: Time-series analysis of post patterns
- **Meme propagation**: Track quote chains over time

## Legal/Ethical Considerations

- Private system only - do not redistribute content
- Filter sensitive/illegal content if needed (hash blocklists)
- Comply with local laws regarding content archival
- Consider content warnings for NSFW material

## Troubleshooting

**Threads not being processed:**
- Check Valkey queue: `redis-cli LRANGE imageboard:b:threads:queue 0 -1`
- Verify services are running and connected

**Media not downloading:**
- Check MinIO connection and bucket creation
- Verify network access to i.4cdn.org
- Check Valkey hash index for deduplication status

**Neo4j storage errors:**
- Verify Neo4j connection and credentials
- Check for duplicate post IDs (should be handled automatically)

## Future Enhancements

- GraphQL API for querying archived data
- Analytics workers (sentiment, topic modeling, image embeddings)
- Web interface for browsing archives
- Export to Parquet for big data analysis
- Integration with public archives (thebarchive.com) for backfill




