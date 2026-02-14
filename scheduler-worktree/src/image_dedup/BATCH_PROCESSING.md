# Batch Processing Existing Data

This guide explains how to run CLIP and deduplication against existing Reddit posts in your Neo4j database.

## Prerequisites

1. Neo4j database with existing Post nodes containing image URLs
2. Valkey/Redis instance running
3. Image deduplication schema applied (run `schema/neo4j_schema.cypher`)

## Quick Start

### Command Line Usage

```bash
# Process all existing posts
python -m src.image_dedup.batch_process

# Process first 1000 posts
python -m src.image_dedup.batch_process --limit 1000

# Process with custom storage path
python -m src.image_dedup.batch_process --storage-path /path/to/storage

# Disable CLIP embeddings (faster, less accurate)
python -m src.image_dedup.batch_process --no-clip

# Process in smaller batches
python -m src.image_dedup.batch_process --batch-size 50

# Resume from offset (if interrupted)
python -m src.image_dedup.batch_process --offset 500
```

### Python API Usage

```python
from src.image_dedup.batch_process import BatchProcessor

# Initialize processor
processor = BatchProcessor(
    storage_path="/path/to/storage",
    enable_clip=True,  # Enable CLIP embeddings
    batch_size=100,    # Process 100 posts at a time
)

# Process all posts
stats = processor.process_all()

# Process limited number
stats = processor.process_all(limit=1000)

# Resume from offset
stats = processor.process_all(limit=1000, start_from=500)

print(f"Processed: {stats['processed']}")
print(f"Successful: {stats['successful']}")
print(f"New images: {stats['new']}")
print(f"Duplicates: {stats['duplicates']}")
print(f"Errors: {stats['errors']}")
print(f"Skipped: {stats['skipped']}")
```

## How It Works

1. **Query Existing Posts**: Fetches Post nodes with image URLs from Neo4j
2. **Check Already Processed**: Skips posts that already have ImageFile nodes linked
3. **Download Images**: Downloads images from URLs with retry logic
4. **Run Deduplication**: Processes each image through the deduplication pipeline:
   - Computes SHA-256, pHash, dHash
   - Checks for exact duplicates
   - Searches for near-duplicates using pHash buckets
   - Optionally computes CLIP embeddings for semantic similarity
   - Creates ImageFile nodes and clusters in Neo4j
   - Links images to posts via APPEARED_IN relationships
5. **Track Statistics**: Monitors progress and provides statistics

## Features

- **Resumable**: Can resume from any offset if interrupted
- **Batch Processing**: Processes posts in batches to manage memory
- **Error Handling**: Gracefully handles download failures and continues
- **Skip Already Processed**: Automatically skips posts that have been processed
- **Progress Reporting**: Shows progress and statistics during processing

## Performance Tips

1. **Disable CLIP for faster processing**: Use `--no-clip` flag if you don't need semantic similarity
2. **Adjust batch size**: Smaller batches use less memory but more database queries
3. **Run during off-peak**: Image downloads can be slow, run during low-traffic times
4. **Monitor storage**: Ensure sufficient disk space for image storage

## Statistics

The batch processor tracks:
- **processed**: Total posts attempted
- **successful**: Posts successfully processed
- **new**: New unique images created
- **duplicates**: Duplicate/repost images detected
- **errors**: Posts that failed to process
- **skipped**: Posts already processed (have ImageFile nodes)

## Troubleshooting

### Images fail to download
- Check network connectivity
- Verify image URLs are still valid
- Check if images are behind authentication

### Out of memory
- Reduce batch size with `--batch-size 50`
- Disable CLIP with `--no-clip`

### Neo4j connection errors
- Verify Neo4j is running and accessible
- Check connection credentials in `.env` file

### Storage full
- Free up disk space or change storage path
- Consider cleanup of old/unused images

## Example Output

```
Starting batch processing...
Batch size: 100
Starting from offset: 0
Processing all available posts

--- Batch 1 (offset: 0) ---
Processing 100 posts...
  [1] Processing t3_abc123... (success)
  [2] Processing t3_def456... (duplicate)
  [3] Processing t3_ghi789... (success)
  ...

Statistics: Processed: 100, Successful: 95, New: 60, Duplicates: 35, Errors: 5, Skipped: 0

--- Batch 2 (offset: 100) ---
...
```







