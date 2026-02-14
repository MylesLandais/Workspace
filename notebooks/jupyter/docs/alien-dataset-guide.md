# Reddit Alien Dataset Workflow Guide

## Overview

The **alien** dataset is our unified Reddit data collection, stored as a single Parquet file with all posts, comments, and image references embedded.

**Location:** `/home/warby/Workspace/jupyter/packs/reddit-all/`

**Archive:** `reddit-all.tar.gz` (3.2 MB)

---

## Dataset Structure

```
reddit-all/
├── reddit.parquet     # Single unified parquet with all data
├── images/            # Downloaded image files
└── metadata.json      # Dataset summary
```

### Parquet Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reddit post ID |
| `title` | string | Post title |
| `created_utc` | timestamp | Post creation time |
| `score` | int64 | Upvotes |
| `num_comments` | int64 | Comment count |
| `upvote_ratio` | float64 | Upvote ratio |
| `over_18` | bool | NSFW flag |
| `url` | string | Post URL |
| `selftext` | string | Post body text |
| `permalink` | string | Reddit permalink |
| `subreddit` | string | Subreddit name |
| `author` | string | Post author |
| `entity` | string | Matched entity/creator |
| `entity_slug` | string | Entity slug |
| `image_hash` | string | Image hash |
| `comments` | array | Nested comment objects |
| `images` | array | Nested image objects |

---

## Daily Workflow

### 1. Add New Subreddits

```python
# Add a new subreddit to monitoring
docker compose run --rm -w /home/jovyan/workspaces jupyterlab python -c "
import sys
sys.path.insert(0, 'src')
from feed.storage.neo4j_connection import get_connection
from uuid import uuid4

neo4j = get_connection()
name = 'NewSubreddit'
slug = 'new-subreddit'

neo4j.execute_write('''
    MERGE (c:Creator {slug: \$slug})
    ON CREATE SET c.uuid = \$uuid, c.name = \$name, c.slug = \$slug
    WITH c
    MERGE (s:Subreddit {name: \$name})
    MERGE (c)-[:HAS_SOURCE]->(s)
''', {'slug': slug, 'uuid': str(uuid4()), 'name': name})
print(f'Added r/{name}')
"
```

### 2. Poll for New Posts

```python
# Poll a subreddit for new posts (past 24h)
docker compose run --rm -w /home/jovyan/workspaces jupyterlab python -c "
import sys
sys.path.insert(0, 'src')
from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection
from datetime import datetime, timedelta

neo4j = get_connection()
reddit = RedditAdapter(mock=False, delay_min=5.0, delay_max=15.0)
subreddit = 'NewSubreddit'

cutoff = datetime.now() - timedelta(hours=24)
posts, after = [], None
page = 0

while page < 5:
    page += 1
    fetched, after = reddit.fetch_posts(source=subreddit, sort='new', limit=100, after=after)
    if not fetched: break
    
    new_posts = [p for p in fetched if p.created_utc >= cutoff]
    # Store new posts to Neo4j...
    if not after: break

print(f'Collected {len(posts)} posts')
"
```

### 3. Rebuild the Unified Dataset

```bash
# Rebuild the single unified parquet
docker compose run --rm -w /home/jovyan/workspaces \
  -v /home/warby/Workspace/jupyter/packs:/home/jovyan/workspaces/packs \
  jupyterlab python -c "
import sys
sys.path.insert(0, 'src')
from feed.storage.neo4j_connection import get_connection
from datetime import datetime
import json
import shutil
from pathlib import Path
import pandas as pd
import pyarrow as pa
from pyarrow.parquet import write_table

neo4j = get_connection()
pack_dir = Path('/home/jovyan/workspaces/packs/reddit-all')
pack_dir.mkdir(parents=True, exist_ok=True)

# Load comments/images by post, then all posts
# Build unified records with nested comments/images arrays
# Write to reddit.parquet with proper schema

# Copy images from Neo4j to images/

# Write metadata.json

print('Done! Pack at:', pack_dir)
"
```

Then create the archive:
```bash
cd /home/warby/Workspace/jupyter/packs
tar -czf reddit-all.tar.gz reddit-all
```

---

## Working with the Data

### Python

```python
import pandas as pd

# Load the unified dataset
df = pd.read_parquet('reddit-all/reddit.parquet')

# Filter by subreddit
df[df['subreddit'] == 'BrookeMonkNSFWHub']

# Filter by entity
df[df['entity'] == 'Brooke Monk']

# Get posts with comments
df[df['comments'].apply(len) > 0]

# Access nested comments
for idx, row in df.head(5).iterrows():
    print(row['title'])
    for comment in row['comments']:
        print(f"  - {comment['author']}: {comment['body'][:50]}")
```

### Query Examples

```python
# Top posts by score
df.nlargest(10, 'score')[['title', 'subreddit', 'score', 'entity']]

# Posts by entity with comment count
df.groupby('entity').agg({
    'id': 'count',
    'num_comments': 'sum'
}).sort_values('id', ascending=False)

# Posts per subreddit
df['subreddit'].value_counts()
```

---

## Architecture

```
Neo4j (Graph Database)
├── Post nodes
├── Subreddit nodes  
├── Creator nodes
└── Relationships
    ├── [:POSTED_IN] - Post to Subreddit
    ├── [:ABOUT] - Post to Creator
    └── [:HAS_IMAGE] - Post to Image

↓ Export

Single Parquet (reddit.parquet)
├── All posts flattened
├── Comments embedded as array
└── Images embedded as array
```

---

## Commands Reference

| Task | Command |
|------|---------|
| Start services | `docker compose up -d` |
| Check Neo4j | `docker compose exec n4j cypher-shell` |
| View monitored subreddits | `MATCH (s:Subreddit) RETURN s.name` |
| View entities | `MATCH (c:Creator) RETURN c.name, c.slug` |
| Rebuild pack | Run Python script above |
| Create archive | `tar -czf reddit-all.tar.gz reddit-all` |

---

## Tips

1. **Rate limiting**: Reddit API has limits - use 5-15s delays between requests
2. **Deduplication**: Neo4j handles deduplication by post ID automatically
3. **Images**: Only ~9 images downloaded; most are just URL references
4. **Updates**: Rebuild the parquet after any significant polling session
5. **Backup**: Keep old archives in `packs/archive/` if needed

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No new posts found | Check if subreddit exists in Neo4j |
| Parquet write fails | Ensure schema matches data types |
| Images not copied | Check Neo4j image_path values exist |
| Neo4j connection failed | Ensure services are running |
