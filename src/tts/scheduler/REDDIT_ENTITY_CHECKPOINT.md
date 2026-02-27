# Reddit Entity Pack Checkpoint - 2026-01-02

## Status: PAUSED
Ready to resume at later time.

## Completed Work

### 1. Entity-Based Polling System ✓

Created `poll_creator_sources.py` for entity-based Reddit crawling:
- Maps Creator nodes to Subreddit sources in Neo4j
- Polls subreddits and tags posts with `entity_matched`
- Links posts to Creator nodes via `ABOUT` relationships
- Respects rate limits (5-30s delays)

**Documentation**: `ENTITY_POLLING.md`

### 2. Entity-Based Packing System ✓

Created `create_entity_pack.py` for entity-based parquet packs:
- Filters by `creator_slug` or `entity_matched`
- Exports posts, subreddits, images to parquet
- Optional compression to tar.gz
- Follows existing nightly pack patterns

**Documentation**: `ENTITY_PACK.md`

### 3. Jordyn Jones Entity Pack ✓

**Pack**: `packs/reddit-jordyn-jones-full/`
- Posts: 532
- Images: 532
- Subreddits: 7
- Archive: 68KB

**Subreddits**:
- r/JordynJonesBooty: 357 posts
- r/JordynJonesCandy: 156 posts
- r/JordynJones_gooners: 17 posts
- r/jordynjonesbody: 2 posts
- r/JordynJonesSimp: 0 posts
- r/JordynJonesSnark: 0 posts
- r/jordynjones: 0 posts

### 4. Brooke Monk Entity Pack ✓

**Pack**: `packs/reddit-brooke-monk-1000posts/`
- Posts: 1230
- Images: 1230
- Subreddits: 3
- Archive: 145KB

**Subreddits**:
- r/BrookeMonkNSFWHub: 1000 posts
- r/BrookeMonkTheSecond: 189 posts
- r/BestOfBrookeMonk: 41 posts

## Current State

### Neo4j Graph Structure

```
(Creator: Jordyn Jones [jordyn-jones])
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesBooty)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesCandy)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJones_gooners)
  ├── [:HAS_SOURCE] → (Subreddit: jordynjonesbody)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesSimp)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesSnark)
  └── [:HAS_SOURCE] → (Subreddit: jordynjones)

(Creator: Brooke Monk [brooke-monk])
  ├── [:HAS_SOURCE] → (Subreddit: BrookeMonkNSFWHub)
  ├── [:HAS_SOURCE] → (Subreddit: BrookeMonkTheSecond)
  └── [:HAS_SOURCE] → (Subreddit: BestOfBrookeMonk)

(Post)-[:POSTED_IN]→(Subreddit)
(Post)-[:ABOUT]→(Creator)
Post.entity_matched = "Entity Name"
```

### Data Summary

| Entity | Posts | Subreddits | Pack | Status |
|---------|--------|-------------|-------|--------|
| Jordyn Jones | 532 | 7 | reddit-jordyn-jones-full.tar.gz | ✓ Complete |
| Brooke Monk | 1230 | 3 | reddit-brooke-monk-1000posts.tar.gz | ✓ Complete |
| Reddit All | 1763 | 11 | reddit-nightly-final.tar.gz | ✓ Complete |
| **Total** | **1763** | **11** | **3 packs** | **✓ Done** |

## Files Created

### Scripts
- `poll_creator_sources.py` - Entity-based Reddit polling
- `create_entity_pack.py` - Entity-based parquet packing

### Documentation
- `ENTITY_POLLING.md` - Polling system usage guide
- `ENTITY_PACK.md` - Packing system usage guide
- `POLLING_RESULTS.md` - Initial polling report
- `REDDIT_ENTITY_CHECKPOINT.md` - This file

### Data Packs
- `packs/reddit-jordyn-jones-full.tar.gz` (68KB)
- `packs/reddit-brooke-monk-1000posts.tar.gz` (145KB)
- `packs/reddit-nightly-final.tar.gz` (118KB)

### Data Exports
- `jordyn_jones_reddit_posts_532.jsonl` - Jordyn Jones posts
- `reddit_posts_785.jsonl` - All valid posts (mixed entities)

## Next Steps When Resuming

### Option 1: Add More Entities
1. Add creator to `poll_creator_sources.py` mappings
2. Run setup: `docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --setup`
3. Poll: `docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --creator new-entity`
4. Pack: `docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create new-entity`

### Option 2: Daily/Weekly Updates
1. Update existing entities: `docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py`
2. Create fresh packs: `docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones --days-back 7`

### Option 3: Analysis
```bash
# Load pack data
docker compose exec jupyterlab python -c "
import pandas as pd
posts = pd.read_parquet('packs/reddit-jordyn-jones-full/posts.parquet')
# ... analyze ...
"
```

## Command Reference

### Polling
```bash
# Setup new entity
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --setup

# Poll all creators
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py

# Poll specific creator
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --creator jordyn-jones --max-posts 1000
```

### Packing
```bash
# Create entity pack
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create jordyn-jones

# Create with custom date range
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py create brooke-monk --days-back 90

# List packs
docker compose exec jupyterlab python /home/jovyan/workspaces/create_entity_pack.py list
```

### Verification
```bash
# Check creator nodes
docker compose exec jupyterlab python -c "
sys.path.insert(0, 'src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
result = neo4j.execute_read('MATCH (c:Creator) RETURN c.name, c.slug')
for r in result:
    print(f'{r[\"c.name\"]} ({r[\"c.slug\"]})')
"
```

## Notes

### Rate Limiting
- Reddit API limits: 30-60s delays between subreddits
- Additional delays: 5-15s between pages
- Total poll time for 1000 posts: ~15-20 minutes

### Pack Sizes
- Parquet files only: ~70-150KB
- Includes all metadata: posts, images, subreddits
- No actual images stored (URLs only)
- Fast to create and transfer

### Data Model
- Posts stored with `created_utc` as DateTime objects in Neo4j
- Pack exports convert to ISO strings
- Parquet loading may need `pd.to_datetime()` for analysis

### Entity Matching
- `entity_matched` set to creator name (e.g., "Jordyn Jones")
- `creator_slug` for graph queries (e.g., "jordyn-jones")
- Both fields in pack for flexibility

## System Requirements

### Dependencies
- Python 3.11+
- Neo4j (running in Docker)
- pandas, pyarrow for parquet
- feed.platforms.reddit for polling

### Docker Services
- jupyter.dev.local - Main runtime
- n4j.jupyter.dev.local - Neo4j graph
- s3.jupyter.dev.local - S3 storage (optional)

## Bookmark Timestamp

**Checkpoint created**: 2026-01-02
**Last action**: Created Brooke Monk entity pack (1230 posts)
**Next action**: Add more entities or analyze existing data

---

To resume: Read this file and follow "Next Steps When Resuming" section.
