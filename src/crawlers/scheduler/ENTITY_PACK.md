# Reddit Entity Pack System

Entity-based parquet packing for Reddit data from Neo4j graph.

## Overview

Creates compressed parquet packs for specific creators/entities from Reddit data:
- Filters by `creator_slug` or `entity_matched`
- Exports posts, subreddits, images to parquet
- Optional compression to tar.gz
- Follows existing nightly pack patterns

## Usage

### Create Entity Pack

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create <creator-slug>
```

### Examples

Create pack for Jordyn Jones (default 30 days):
```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones
```

Create pack with custom date range:
```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones --days-back 90
```

Create pack with custom name:
```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones --pack-name reddit-jordyn-jones-full --days-back 365
```

Create uncompressed pack (directory only):
```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones --no-compress
```

### List Available Packs

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py list
```

## Options

| Option | Default | Description |
|--------|----------|-------------|
| `--days-back` | 30 | Number of days of data to include |
| `--pack-name` | reddit-{slug}-{date} | Custom pack name |
| `--output-dir` | packs | Output directory |
| `--no-compress` | false | Don't compress to tar.gz |

## Pack Structure

```
reddit-{creator-slug}-{date}/
├── metadata.json       # Pack metadata and stats
├── posts.parquet       # Post data
├── images.parquet      # Image URLs from posts
└── subreddits.parquet  # Subreddit info
```

## Parquet Schemas

### posts.parquet

- `id`: Reddit post ID
- `title`: Post title
- `created_utc`: Creation timestamp (ISO string)
- `score`: Upvote score
- `num_comments`: Number of comments
- `upvote_ratio`: Upvote ratio (0.0-1.0)
- `over_18`: NSFW flag
- `url`: Post URL (image/gallery)
- `permalink`: Reddit permalink
- `selftext`: Post body text
- `author`: Post author username
- `entity_matched`: Matched entity name
- `subreddit`: Subreddit name

### subreddits.parquet

- `name`: Subreddit name
- `post_count`: Number of posts (in date range)

### images.parquet

- `post_id`: Reddit post ID
- `image_url`: Image/gallery URL
- `subreddit`: Subreddit name
- `title`: Post title
- `created_utc`: Creation timestamp
- `score`: Post score

### metadata.json

```json
{
  "pack_name": "reddit-jordyn-jones-2026-01-03",
  "pack_type": "reddit-entity",
  "created_at": "2026-01-03T03:54:00.123456",
  "date_range_days": 365,
  "date_from": "2025-01-03T03:54:00.123456",
  "date_to": "2026-01-03T03:54:00.123456",
  "exported_at": "2026-01-03T03:54:00.123456",
  "creator_slug": "jordyn-jones",
  "subreddit_count": 7,
  "subreddits_file": "subreddits.parquet",
  "post_count": 532,
  "posts_file": "posts.parquet",
  "image_count": 532,
  "images_file": "images.parquet",
  "archive_file": "reddit-jordyn-jones-2026-01-03.tar.gz",
  "archive_size_bytes": 68752
}
```

## Example: Jordyn Jones Pack

```bash
# Create 365-day pack
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones --days-back 365

# Result:
#   Pack: packs/reddit-jordyn-jones-full/
#   Posts: 532
#   Images: 532
#   Subreddits: 7
#   Archive: 68KB
```

### Subreddits Included

- r/JordynJonesBooty: 357 posts
- r/JordynJonesCandy: 156 posts
- r/JordynJones_gooners: 17 posts
- r/jordynjonesbody: 2 posts
- r/JordynJonesSimp: 0 posts
- r/JordynJonesSnark: 0 posts
- r/jordynjones: 0 posts

## Data Loading

### Load with Pandas

```python
import pandas as pd

# Load posts
posts = pd.read_parquet("packs/reddit-jordyn-jones-full/posts.parquet")
print(f"Loaded {len(posts)} posts")

# Load subreddits
subreddits = pd.read_parquet("packs/reddit-jordyn-jones-full/subreddits.parquet")

# Load images
images = pd.read_parquet("packs/reddit-jordyn-jones-full/images.parquet")
```

### Filter by Date

```python
from datetime import datetime

# Filter posts from last 30 days
cutoff = datetime.utcnow() - timedelta(days=30)
recent_posts = posts[pd.to_datetime(posts['created_utc']) > cutoff]
print(f"Recent posts: {len(recent_posts)}")
```

### Group by Subreddit

```python
# Posts per subreddit
by_subreddit = posts.groupby('subreddit').size()
print(by_subreddit)

# Average score by subreddit
avg_score = posts.groupby('subreddit')['score'].mean()
print(avg_score)
```

## Integration with Existing Tools

### Polling → Packing Workflow

```bash
# 1. Poll for new posts
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --creator jordyn-jones

# 2. Create pack
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones

# 3. Analyze pack
docker compose exec jupyterlab python -c "
import pandas as pd
posts = pd.read_parquet('packs/reddit-jordyn-jones-2026-01-03/posts.parquet')
print(f'Top posts by score:')
print(posts.nlargest(10, 'score')[['title', 'subreddit', 'score']])
"
```

## Comparison: Entity Pack vs Generic Nightly Pack

| Aspect | Entity Pack | Generic Pack |
|---------|--------------|---------------|
| **Filtering** | By creator/entity | All data |
| **Use case** | Specific entities | General backup |
| **Query** | Creator + entity_matched | Date range only |
| **Size** | Smaller, focused | Larger, comprehensive |
| **Files** | posts, images, subreddits | posts, comments, images, subreddits |

## Adding New Creators

1. Set up creator mapping:

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --setup
```

2. Edit `poll_creator_sources.py` to add new creator:

```python
mappings = {
    "jordyn-jones": "Jordyn Jones",
    "new-creator": "Creator Name",
}

creator_sources = {
    "jordyn-jones": [
        "JordynJonesBooty",
        # ...
    ],
    "new-creator": [
        "Subreddit1",
        "Subreddit2",
    ],
}
```

3. Poll and pack:

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --creator new-creator
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create new-creator
```

## Troubleshooting

### Empty Pack

If pack has 0 posts:
- Check creator slug is correct
- Verify entity tags exist in Neo4j
- Check date range includes posts

### Incorrect Date Range

Posts use Neo4j datetime format. Verify epoch timestamp conversion:

```python
from datetime import datetime, timedelta
from_date_timestamp = int((datetime.utcnow() - timedelta(days=30)).timestamp())
```

### Missing Subreddits

Check `HAS_SOURCE` relationships exist:

```cypher
MATCH (c:Creator {slug: "jordyn-jones"})-[:HAS_SOURCE]->(s:Subreddit)
RETURN s.name
```

## Performance

Typical metrics:
- 532 posts + 7 subreddits: ~2 seconds
- Parquet export: ~1 second
- Compression: ~1 second
- Archive size: ~70KB (metadata only)

## Files

- `create_entity_pack.py` - Main script
- `poll_creator_sources.py` - Entity-based polling
- `ENTITY_PACK.md` - This documentation

See Also:
- `create_reddit_pack.py` - Generic Reddit packer
- `create_nightly_pack.py` - Imageboard packer
- `NIGHTLY_PACK.md` - Nightly pack documentation
