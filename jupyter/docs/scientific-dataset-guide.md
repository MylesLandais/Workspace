# Scientific Dataset Generation Guide

This guide provides practical examples for using the scientific dataset generation features of the spider. For full architecture details, see [SPIDER_ARCHITECTURE.md](./SPIDER_ARCHITECTURE.md).

## Quick Start

### Basic Usage

```python
from pathlib import Path
from core.spider import ScientificSpider

# Initialize spider with dataset root
spider = ScientificSpider(
    dataset_root=Path("datasets/science-v1"),
    policy_file="config/policies.yaml"
)

# Check if URL should be crawled (policy + freshness check)
if spider.should_crawl("https://reddit.com/r/all"):
    # Perform crawl with full pipeline
    history = spider.crawl("https://reddit.com/r/all")
    
    if history.success:
        print(f"Successfully crawled {history.url}")
        print(f"Content hash: {history.content_hash}")
        print(f"Raw snapshot: {history.raw_content_path}")
        print(f"Extracted data: {history.extracted_data_path}")
    else:
        print(f"Crawl failed: {history.error}")
```

### Policy Configuration

Create `config/policies.yaml`:

```yaml
global:
  min_delay: 300  # 5 minutes default
  max_requests_per_hour: 60
  respect_robots_txt: true
  user_agent: "ScientificSpider/1.0 (contact@example.com)"
  snapshot_retention_days: 90
  change_threshold: 0.1  # 10% change required for re-crawl

sites:
  reddit:
    min_delay: 120  # 2 minutes
    max_requests_per_hour: 120
    change_threshold: 0.05  # 5% for Reddit (more sensitive)
  
  youtube:
    min_delay: 600  # 10 minutes
    max_requests_per_hour: 30
    change_threshold: 0.15  # 15% for YouTube
  
  twitter:
    min_delay: 900  # 15 minutes
    max_requests_per_hour: 20
    change_threshold: 0.2  # 20% for Twitter
```

## Dataset Structure

### Directory Layout

```
datasets/science-v1/
├── snapshots/
│   ├── 2025-12-24/
│   │   ├── reddit-r-all-abc123.warc.gz
│   │   ├── youtube-video-xyz789.warc.gz
│   │   └── extracted/
│   │       ├── reddit-posts.parquet
│   │       ├── youtube-videos.parquet
│   │       └── reddit-posts.jsonl.gz  # Backup format
│   └── 2025-12-25/
│       └── ...
├── history/
│   └── crawl_history.parquet  # All crawl attempts
└── policies/
    └── site_policies.yaml  # Active policies
```

### Accessing Snapshots

```python
import warcio
from pathlib import Path

# Read WARC snapshot
warc_path = Path("datasets/science-v1/snapshots/2025-12-24/reddit-r-all-abc123.warc.gz")

with warcio.open(str(warc_path)) as warc_file:
    for record in warc_file:
        if record.rec_type == 'response':
            url = record.rec_headers.get('WARC-Target-URI')
            content = record.content_stream().read()
            print(f"Retrieved {len(content)} bytes from {url}")
```

### Accessing Extracted Data

```python
import pyarrow.parquet as pq
import pandas as pd

# Read Parquet dataset
parquet_path = Path("datasets/science-v1/snapshots/2025-12-24/extracted/reddit-posts.parquet")

# Using Pandas
df = pd.read_parquet(parquet_path)
print(df.head())

# Using PyArrow directly (more efficient)
table = pq.read_table(parquet_path)
print(table.to_pandas().head())
```

## History Analysis

### Querying Crawl History

```python
import polars as pl

# Load history table
history = pl.read_parquet("datasets/science-v1/history/crawl_history.parquet")

# Recent failures
recent_failures = history.filter(
    (pl.col("success") == False) &
    (pl.col("timestamp") > pl.datetime(2025, 12, 20))
).select(["url", "error", "timestamp"])

print(recent_failures)

# Success rate by site
site_stats = history.group_by("site").agg([
    pl.col("success").mean().alias("success_rate"),
    pl.col("success").count().alias("total_crawls"),
    pl.col("content_length").mean().alias("avg_content_size")
])

print(site_stats)

# Change detection analysis
changed_content = history.filter(
    pl.col("change_score").is_not_null() &
    (pl.col("change_score") > 0.1)
).select(["url", "change_score", "timestamp"])

print(changed_content.sort("change_score", descending=True))
```

### Dataset Summary

```python
# Get comprehensive dataset overview
summary = spider.dataset_summary()

print(f"Total crawls: {summary['total_crawls']}")
print(f"Success rate: {summary['success_rate']:.2%}")
print(f"Coverage by site: {summary['coverage_by_site']}")
print(f"Fresh content (24h): {summary['freshness_24h']}")
print(f"Total raw data: {summary['total_raw_gb']:.2f} GB")
print(f"Total extracted records: {summary['total_records']}")
```

## Reproducibility Workflows

### Re-extracting from Snapshots

When you improve an extractor, re-extract from old snapshots:

```python
from pathlib import Path
import warcio
from core.registry import ExtractorFactory

# Load old snapshot
warc_path = Path("datasets/science-v1/snapshots/2025-12-24/reddit-r-all-abc123.warc.gz")

with warcio.open(str(warc_path)) as warc_file:
    for record in warc_file:
        if record.rec_type == 'response':
            url = record.rec_headers.get('WARC-Target-URI')
            html = record.content_stream().read().decode('utf-8')
            
            # Re-extract with new extractor version
            site_name = spider._detect_site(url)
            config = spider._get_site_config(site_name)
            extractor = spider.factory.get_extractor(site_name, config)
            
            # Extract with updated logic
            data = extractor.extract(html)
            
            # Save to new extraction directory
            new_path = spider._save_extracted_data(
                site_name, 
                data,
                snapshot_date="2025-12-24-reprocessed"
            )
```

### Citation and Provenance

Each extracted record can reference its source:

```python
# Extract includes provenance
extracted_data = {
    "title": "Example Post",
    "author": "user123",
    # ... other fields
    "provenance": {
        "source_url": "https://reddit.com/r/all/post/abc123",
        "crawl_id": "abc123def456",
        "crawl_timestamp": "2025-12-24T10:30:00Z",
        "snapshot_path": "snapshots/2025-12-24/reddit-r-all-abc123.warc.gz",
        "extractor_version": "v2.1.0",
        "content_hash": "sha256:abc123..."
    }
}
```

## Policy Management

### Dynamic Policy Updates

```python
from core.policies import CrawlPolicy

# Update policy for a site
policy = CrawlPolicy.from_site("reddit")
policy.min_delay = 180  # Reduce to 3 minutes
policy.max_requests_per_hour = 150  # Increase limit

# Save updated policy
spider.update_policy("reddit", policy)
```

### robots.txt Respect

```python
from urllib.robotparser import RobotFileParser

# Check robots.txt before crawling
def check_robots_txt(url: str) -> bool:
    rp = RobotFileParser()
    rp.set_url(f"{url}/robots.txt")
    rp.read()
    return rp.can_fetch("ScientificSpider/1.0", url)

if check_robots_txt("https://reddit.com/r/all"):
    spider.crawl("https://reddit.com/r/all")
```

## Batch Crawling

### Scheduled Crawling

```python
from datetime import datetime, timedelta
import time

# Crawl list of URLs with policy enforcement
urls = [
    "https://reddit.com/r/all",
    "https://reddit.com/r/programming",
    "https://youtube.com/watch?v=abc123",
]

for url in urls:
    if spider.should_crawl(url):
        history = spider.crawl(url)
        print(f"{url}: {history.crawl_id} - {'Success' if history.success else 'Failed'}")
        
        # Policy-enforced delay happens automatically
    else:
        print(f"{url}: Skipped (policy/freshness check)")
    
    # Additional delay between different sites
    time.sleep(60)
```

### Change Detection Workflow

```python
# Only crawl if content has changed significantly
for url in urls:
    last_crawl = spider._last_successful_crawl(url)
    
    if last_crawl:
        # Check if change threshold met
        if last_crawl.change_score and last_crawl.change_score < 0.1:
            print(f"{url}: No significant changes, skipping")
            continue
    
    if spider.should_crawl(url):
        history = spider.crawl(url)
```

## Data Quality Monitoring

### Validation Metrics

```python
# Track validation failures
history = pl.read_parquet("datasets/science-v1/history/crawl_history.parquet")

validation_failures = history.filter(
    (pl.col("success") == False) &
    (pl.col("error").str.contains("validation", literal=False))
)

print(f"Validation failure rate: {len(validation_failures) / len(history):.2%}")

# By site
validation_by_site = validation_failures.group_by("site").agg([
    pl.count().alias("failures"),
    pl.col("error").first().alias("sample_error")
])

print(validation_by_site)
```

### Content Quality Tracking

```python
# Track content changes over time
history = pl.read_parquet("datasets/science-v1/history/crawl_history.parquet")

# URLs with frequent changes
frequent_changes = history.filter(
    pl.col("change_score").is_not_null()
).group_by("url").agg([
    pl.col("change_score").mean().alias("avg_change"),
    pl.col("change_score").count().alias("change_count")
]).filter(
    pl.col("change_count") > 5
).sort("avg_change", descending=True)

print("URLs with frequent content changes:")
print(frequent_changes)
```

## Storage Management

### Snapshot Retention

```python
from pathlib import Path
from datetime import datetime, timedelta

# Clean up old snapshots based on retention policy
def cleanup_old_snapshots(dataset_root: Path, retention_days: int = 90):
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    snapshots_dir = dataset_root / "snapshots"
    
    for date_dir in snapshots_dir.iterdir():
        if date_dir.is_dir():
            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    print(f"Removing old snapshot: {date_dir}")
                    # Archive or delete
                    # shutil.rmtree(date_dir)  # Uncomment to delete
            except ValueError:
                continue

cleanup_old_snapshots(Path("datasets/science-v1"), retention_days=90)
```

### Dataset Archival

```python
import shutil
import tarfile

# Archive a date's snapshots
def archive_snapshots(dataset_root: Path, date: str):
    snapshots_dir = dataset_root / "snapshots" / date
    
    if not snapshots_dir.exists():
        return
    
    archive_path = dataset_root / "archives" / f"{date}.tar.gz"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(snapshots_dir, arcname=date)
    
    # Remove original after archiving
    shutil.rmtree(snapshots_dir)
    print(f"Archived {date} to {archive_path}")

archive_snapshots(Path("datasets/science-v1"), "2025-12-24")
```

## Best Practices

### 1. Policy Configuration
- Set conservative defaults
- Adjust per-site based on site's rate limits
- Monitor and adjust based on success rates
- Document policy decisions

### 2. Snapshot Management
- Regular cleanup of old snapshots
- Archive important snapshots
- Monitor storage usage
- Use compression (WARC gzip)

### 3. History Analysis
- Regular review of crawl history
- Track success rates by site
- Monitor validation failures
- Analyze change patterns

### 4. Reproducibility
- Always include provenance in extracted data
- Version control extractor code
- Document policy versions
- Keep snapshot metadata

### 5. Ethical Crawling
- Respect robots.txt
- Use appropriate user-agent
- Honor rate limits
- Monitor for abuse patterns

## Troubleshooting

### High Failure Rate

```python
# Analyze failures
failures = history.filter(pl.col("success") == False)

# Group by error type
error_analysis = failures.group_by("error").agg([
    pl.count().alias("count"),
    pl.col("site").first().alias("site")
]).sort("count", descending=True)

print(error_analysis)
```

### Storage Growth

```python
# Check storage usage
from pathlib import Path

def get_directory_size(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total

snapshots_size = get_directory_size(Path("datasets/science-v1/snapshots"))
print(f"Snapshots: {snapshots_size / (1024**3):.2f} GB")

history_size = get_directory_size(Path("datasets/science-v1/history"))
print(f"History: {history_size / (1024**2):.2f} MB")
```

## References

- [SPIDER_ARCHITECTURE.md](./SPIDER_ARCHITECTURE.md) - Full architecture documentation
- [SPIDER_DESIGN_DECISIONS.md](./SPIDER_DESIGN_DECISIONS.md) - Design decisions
- [WARC Format Specification](https://iipc.github.io/warc-specifications/) - WARC standard
- [Apache Parquet](https://parquet.apache.org/) - Parquet format documentation
- [Common Crawl](https://commoncrawl.org/) - Large-scale web crawl practices





