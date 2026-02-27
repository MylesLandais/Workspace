# Nightly Pack System for Imageboard Cache

Create and unpack nightly parquet packs from imageboard cache for archival.

## Files

- `create_nightly_pack.py` - Python script to create packs from cache
- `unpack_nightly_pack.py` - Python script to unpack packs with timestamp support
- `nightly-pack.sh` - Helper script with convenient commands (recommended)
- `NIGHTLY_PACK.md` - This documentation

## Pack Types

### Metadata Pack (Default)
- Contains parquet files only
- References images in cache directory
- Size: ~1-5MB
- Fast to create
- Suitable for: Analysis, backups with separate image storage

### Full Pack
- Contains parquet files + actual image files
- Complete backup in single archive
- Size: 3-5GB+ (depending on cache size)
- Takes longer to create and compress
- Suitable for: Complete backups, archiving, transfer

## Quick Start

### Using Helper Script (Recommended)

```bash
# Make helper script executable
chmod +x nightly-pack.sh

# Create metadata pack
./nightly-pack.sh create

# Create full pack with images
./nightly-pack.sh create --full

# Unpack latest pack
./nightly-pack.sh unpack-latest

# List all packs
./nightly-pack.sh list

# Unpack pack from 3 days ago
./nightly-pack.sh unpack "3 days ago"

# Compare yesterday vs today
./nightly-pack.sh compare yesterday today

# Archive packs older than 30 days
./nightly-pack.sh archive-days 30
```

### Using Python Scripts Directly

## Setup

### Helper Script

The `nightly-pack.sh` wrapper provides convenient commands for common operations:

```bash
chmod +x nightly-pack.sh
./nightly-pack.sh help    # Show all commands
```

### Python Scripts

Install required dependencies:

```bash
pip install pandas pyarrow beautifulsoup4
```

Or update your requirements.txt:

```txt
pandas>=2.0.0
pyarrow>=14.0.0
beautifulsoup4>=4.12.0
```

## Creating Nightly Packs

### Basic Usage

Create a nightly pack from the default cache directory:

```bash
python create_nightly_pack.py
```

This creates a pack with today's date in the `packs/` directory:

```
packs/
├── nightly-2026-01-02/
│   ├── threads.parquet
│   ├── images.parquet
│   └── metadata.json
└── nightly-2026-01-02.tar.gz
```

### Custom Options

Specify custom cache and output directories:

```bash
python create_nightly_pack.py \
  --cache-dir /path/to/cache/imageboard \
  --output-dir /path/to/packs
```

Create a pack with a custom name:

```bash
python create_nightly_pack.py --pack-name my-custom-pack
```

Exclude HTML files (images only):

```bash
python create_nightly_pack.py --no-html
```

Exclude images (metadata only):

```bash
python create_nightly_pack.py --no-images
```

Create full pack with actual image files (larger):

```bash
python create_nightly_pack.py --include-image-content
```

Create full pack with HTML and images (complete backup):

```bash
python create_nightly_pack.py \
  --include-html-content \
  --include-image-content
```

Don't compress (keep as directory only):

```bash
python create_nightly_pack.py --no-compress
```

### List Available Packs

```bash
python create_nightly_pack.py --list
```

## Unpacking Nightly Packs

### Basic Usage

Unpack a pack to the default location:

```bash
python unpack_nightly_pack.py packs/nightly-2026-01-02.tar.gz
```

### Unpack by Timestamp

Unpack using a timestamp instead of full path:

```bash
# Unpack by date
python unpack_nightly_pack.py 2026-01-02

# Unpack by YYYYMMDD
python unpack_nightly_pack.py 20260102

# Unpack latest pack
python unpack_nightly_pack.py latest

# Unpack today's pack
python unpack_nightly_pack.py today

# Unpack yesterday's pack
python unpack_nightly_pack.py yesterday

# Unpack pack from 3 days ago
python unpack_nightly_pack.py "3 days ago"

# Unpack pack from 1 week ago
python unpack_nightly_pack.py "1 week ago"
```

This extracts to `unpacked/nightly-2026-01-02/` with only parquet files.

### Custom Options

Specify custom output directory:

```bash
python unpack_nightly_pack.py \
  packs/nightly-2026-01-02.tar.gz \
  --output-dir /path/to/unpacked
```

Extract HTML files from archive:

```bash
python unpack_nightly_pack.py \
  packs/nightly-2026-01-02.tar.gz \
  --extract-html
```

Extract images from archive:

```bash
python unpack_nightly_pack.py \
  packs/night6-01-02.tar.gz \
  --extract-images
```

Extract everything (parquet, HTML, and images):

```bash
python unpack_nightly_pack.py \
  packs/nightly-2026-01-02.tar.gz \
  --extract-html \
  --extract-images
```

### List Available Packs

```bash
python unpack_nightly_pack.py --list
```

## Pack Format

### Directory Structure

Unpacked pack:

```
nightly-2026-01-02/
├── threads.parquet       # Thread metadata
├── images.parquet        # Image metadata with SHA-256 hashes
├── metadata.json         # Pack metadata and statistics
├── html/                 # (if extracted) Cached HTML files
└── images/               # (if extracted) Cached image files
```

### Parquet Schemas

#### threads.parquet

- `board`: Board name (e.g., "b", "gif")
- `thread_id`: Thread ID
- `url`: Thread URL
- `title`: Thread title/subject
- `post_count`: Number of posts
- `image_count`: Number of images
- `html_path`: Path to cached HTML
- `html_filename`: HTML filename
- `file_size`: HTML file size in bytes
- `file_modified`: ISO timestamp of last modification
- `cached_at`: ISO timestamp when packed

#### images.parquet

- `sha256`: SHA-256 hash of image file
- `local_path`: Full path to cached image
- `relative_path`: Path relative to cache/images/
- `filename`: Image filename
- `file_size`: File size in bytes
- `file_modified`: ISO timestamp of last modification
- `cached_at`: ISO timestamp when packed

### metadata.json

```json
{
  "pack_name": "nightly-2026-01-02",
  "created_at": "2026-01-02T18:00:00.000000",
  "cache_hash": "abc123...",
  "source_cache_dir": "/path/to/cache/imageboard",
  "thread_count": 23,
  "image_count": 1042,
  "unique_images": 1015,
  "threads_file": "threads.parquet",
  "images_file": "images.parquet",
  "stats": {
    "total_size_bytes": 375500000,
    "avg_size_bytes": 360000,
    "by_extension": {
      "jpg": {"count": 800, "size_bytes": 280000000},
      "gif": {"count": 200, "size_bytes": 80000000},
      "png": {"count": 42, "size_bytes": 15500000}
    }
  }
}
```

**Full pack metadata (with `--include-image-content`):**

```json
{
  "pack_name": "nightly-2026-01-02-full",
  "created_at": "2026-01-02T18:00:00.000000",
  "cache_hash": "abc123...",
  "source_cache_dir": "/path/to/cache/imageboard",
  "thread_count": 23,
  "images_dir": "images",
  "images_files_count": 1250,
  "threads_file": "threads.parquet",
  "images_file": "images.parquet",
  "archive_file": "nightly-2026-01-02-full.tar.gz",
  "archive_size_bytes": 4360108405,
  "stats": {
    "total_size_bytes": 3162126504,
    "avg_size_bytes": 465703,
    "by_extension": {
      "jpg": {"count": 6113, "size_bytes": 2588703312},
      "png": {"count": 594, "size_bytes": 476784463},
      "gif": {"count": 83, "size_bytes": 96638729}
    }
  }
}
```

## Usage Examples

### Daily Backup with Helper Script

Create a cron job to create nightly packs daily at midnight:

```bash
# Edit crontab
crontab -e

# Add this line
0 0 * * * cd /path/to/jupyter && ./nightly-pack.sh create

# Or with logging
0 0 * * * cd /path/to/jupyter && ./nightly-pack.sh create >> logs/backup.log 2>&1
```

```bash
# Edit crontab
crontab -e

# Add this line
0 0 * * * cd /path/to/jupyter && python create_nightly_pack.py --pack-name nightly-$(date +\%Y-\%m-\%d)
```

### Automatic Analysis with Helper Script

Set up a daily analysis job that always uses the latest pack:

```bash
# Create cron job
0 2 * * * cd /path/to/jupyter && \
  ./nightly-pack.sh unpack-latest && \
  python create_gallery.py --cache-dir unpacked/nightly-latest && \
  ./nightly-pack.sh clean-unpacked
```

### Weekly Comparison Report

Compare this week's data with last week's:

```bash
#!/bin/bash
# weekly-comparison.sh

cd /path/to/jupyter

echo "=== Weekly Comparison Report ==="
echo "Date: $(date)"
echo ""

# Get dates
TODAY=$(date +%Y-%m-%d)
WEEK_AGO=$(date -d "7 days ago" +%Y-%m-%d)

echo "Comparing: $WEEK_AGO vs $TODAY"
echo ""

# Compare packs
./nightly-pack.sh compare "$WEEK_AGO" "$TODAY"

echo ""
echo "=== Growth Summary ==="
```

```bash
# Create cron job to run analysis on latest pack
0 2 * * * cd /path/to/jupyter && \
  python unpack_nightly_pack.py latest --extract-html --extract-images && \
  python create_gallery.py --cache-dir unpacked/nightly-latest && \
  python -c "import shutil; shutil.rmtree('unpacked/nightly-latest')"
```

### Weekly Backup Archive

Create weekly archive of older packs:

```bash
# Create a cron job to archive packs older than 7 days
0 3 * * 0 cd /path/to/jupyter && \
  find packs/ -name "nightly-*.tar.gz" -mtime +7 -exec mv {} archive/weekly/ \; && \
  find archive/weekly/ -name "nightly-*.tar.gz" -mtime +30 -delete
```

### Compare Today vs Yesterday

Compare pack sizes between today and yesterday:

```bash
#!/bin/bash

cd /path/to/jupyter

# Unpack both packs
python unpack_nightly_pack.py yesterday --no-compress --pack-name yesterday
python unpack_nightly_pack.py today --no-compress --pack-name today

# Compare statistics
python -c "
import pandas as pd
import json

yesterday = pd.read_parquet('packs/yesterday/images.parquet')
today = pd.read_parquet('packs/today/images.parquet')

print(f'Yesterday: {len(yesterday)} images')
print(f'Today: {len(today)} images')
print(f'New images: {len(today) - len(set(yesterday[\"sha256\"]) & set(today[\"sha256\"]))}')

# Cleanup
import shutil
shutil.rmtree('packs/yesterday')
shutil.rmtree('packs/today')
"
```

### Archive Old Packs

Move packs older than 30 days to archive:

```bash
find packs/ -name "nightly-*.tar.gz" -mtime +30 -exec mv {} archive/ \;
```

### Analyze Pack Statistics

Load parquet files with pandas:

```python
import pandas as pd

threads = pd.read_parquet("unpacked/nightly-2026-01-02/threads.parquet")
images = pd.read_parquet("unpacked/nightly-2026-01-02/images.parquet")

print(f"Total threads: {len(threads)}")
print(f"Total images: {len(images)}")
print(f"Boards: {threads['board'].unique()}")
print(f"Image types: {images['filename'].str.split('.').str[-1].value_counts()}")
```

### Deduplication Across Packs

Find duplicate images across multiple packs:

```python
import pandas as pd
from pathlib import Path

packs_dir = Path("unpacked")
all_images = []

for pack_dir in packs_dir.glob("nightly-*"):
    images_file = pack_dir / "images.parquet"
    if images_file.exists():
        df = pd.read_parquet(images_file)
        df["pack"] = pack_dir.name
        all_images.append(df)

all_images_df = pd.concat(all_images)

# Find duplicates (same SHA-256 in multiple packs)
duplicates = all_images_df.groupby("sha256").filter(lambda x: len(x) > 1)
print(f"Found {len(duplicates)} duplicate images across packs")
```

## Helper Script Commands

The `nightly-pack.sh` script provides a unified interface:

### Create Packs

```bash
# Create pack for today
./nightly-pack.sh create

# Create pack with custom name
./nightly-pack.sh create custom-name

# Create pack for specific date (note: this only names the pack, data comes from cache)
./nightly-pack.sh create "weekly-backup-$(date +%Y-%m-%d)"
```

### Unpack Packs

```bash
# Unpack latest pack
./nightly-pack.sh unpack-latest

# Unpack by path
./nightly-pack.sh unpack packs/nightly-2026-01-02.tar.gz

# Unpack by timestamp
./nightly-pack.sh unpack "3 days ago"
./nightly-pack.sh unpack yesterday
./nightly-pack.sh unpack 2026-01-02
```

### List and Inspect

```bash
# List all available packs
./nightly-pack.sh list

# Show pack metadata without unpacking
./nightly-pack.sh show latest
./nightly-pack.sh show "2026-01-02"

# Show pack size
./nightly-pack.sh size latest
./nightly-pack.sh size yesterday
```

### Compare Packs

```bash
# Compare two packs
./nightly-pack.sh compare yesterday today
./nightly-pack.sh compare "7 days ago" today

# Output shows:
# - Pack creation times
# - Thread counts
# - Image counts
# - Size differences
```

### Archive and Cleanup

```bash
# Archive packs older than N days
./nightly-pack.sh archive-days 30
./nightly-pack.sh archive-days 90

# Clean unpacked directories
./nightly-pack.sh clean-unpacked
```

### Environment Variables

Configure paths via environment variables:

```bash
# Set custom directories
export PACKS_DIR="/backup/packs"
export UNPACKED_DIR="/backup/unpacked"
export ARCHIVE_DIR="/backup/archive"

# Run commands
./nightly-pack.sh list
```

## Timestamp-Based Unpacking

The unpack script supports multiple timestamp formats:

| Format | Example | Description |
|--------|---------|-------------|
| Exact date | `2026-01-02` | Specific date (YYYY-MM-DD) |
| Short date | `20260102` | Date in YYYYMMDD format |
| Latest | `latest` | Most recently modified pack |
| Today | `today` | Pack from today |
| Yesterday | `yesterday` | Pack from yesterday |
| Relative | `3 days ago` | Pack from N days ago |
| Relative | `1 week ago` | Pack from N weeks ago |

### Finding Pack by Timestamp

The script automatically searches for the pack:

```bash
# Tries: nightly-2026-01-02.tar.gz, nightly-2026-01-02.tar, nightly-2026-01-02/
python unpack_nightly_pack.py 2026-01-02
```

### Automated Recovery Script

Example script to recover data from a specific date:

```bash
#!/bin/bash

DATE=$1

if [ -z "$DATE" ]; then
    echo "Usage: $0 <date>"
    echo "Example: $0 2026-01-02"
    exit 1
fi

cd /path/to/jupyter

echo "Unpacking pack from $DATE..."
python unpack_nightly_pack.py "$DATE" \
  --output-dir "recovery/$DATE" \
  --extract-html \
  --extract-images

if [ $? -eq 0 ]; then
    echo "Recovery successful! Data in: recovery/$DATE"
else
    echo "Recovery failed!"
    exit 1
fi
```

Save as `recover_backup.sh`:

```bash
chmod +x recover_backup.sh

# Recover from 3 days ago
./recover_backup.sh "3 days ago"
```

## Integration with Existing Tools

The nightly pack system integrates with existing imageboard tools:

- `create_gallery.py`: Generate gallery from cached data
- `parse_imageboard_thread.py`: Parse individual threads
- `monitor_imageboard_thread.py`: Monitor for updates

Pack the latest cache state before analysis:

```bash
# Pack current cache
python create_nightly_pack.py --pack-name before-analysis

# Run analysis
python create_gallery.py --cache-dir cache/imageboard

# Pack results
python create_nightly_pack.py --pack-name after-analysis
```

## Choosing Pack Type

| Aspect | Metadata Pack | Full Pack |
|--------|---------------|------------|
| **Creation time** | ~30 seconds | ~2-3 minutes |
| **Archive size** | 1-5 MB | 3-5 GB+ |
| **Contains** | Parquet files only | Parquet + all images |
| **Use case** | Analysis, incremental backups | Complete archive, transfer |
| **Storage** | References cache images | Self-contained |
| **Unpack time** | ~5 seconds | ~2 minutes |

### When to use Metadata Pack
- Daily backups when images are stored separately
- Quick analysis without moving large files
- Limited storage space
- Fast creation needed

### When to use Full Pack
- Complete system backup before major changes
- Archiving data for long-term storage
- Transferring to external systems
- Disaster recovery

## Performance

Typical performance metrics:

- Packing 1000 HTML files + 10,000 images: ~30 seconds
- Creating compressed tarball: ~45 seconds
- Unpacking parquet files: ~5 seconds
- Unpacking full archive (HTML + images): ~2 minutes

## Troubleshooting

### Import Errors

If you see "Required packages not installed":

```bash
pip install pandas pyarrow beautifulsoup4
```

### Out of Memory

For large caches, process in batches:

```bash
python create_nightly_pack.py --no-images --pack-name metadata-only
python create_nightly_pack.py --no-html --pack-name images-only
```

### Corrupted Archive

If unpacking fails, try:

```bash
# Test archive integrity
tar -tzf packs/nightly-2026-01-02.tar.gz | head -20

# Extract manually to debug
tar -xzf packs/nightly-2026-01-02.tar.gz -C /tmp/debug/
```
