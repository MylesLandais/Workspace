# Reddit Polling Results Summary

## Executive Summary
- **Total valid posts exported**: 785
- **Posts with entity tags**: 532 (Jordyn Jones)
- **Posts without entity tags**: 253
- **Subreddits crawled**: 7
- **Export location**: `/home/warby/Workspace/jupyter/reddit_posts_785.jsonl`

## Post Breakdown

### By Entity
- Jordyn Jones: 532 posts
- Unknown/Untagged: 253 posts

### By Subreddit
- r/JordynJonesBooty: 357 posts
- r/JordynJonesCandy: 156 posts
- r/JordynJones_gooners: 17 posts
- r/jordynjonesbody: 2 posts
- r/TaylorSwift: 1 post
- r/JordynJonesSimp: 0 posts
- r/JordynJonesSnark: 0 posts

## Creator Mapping

Creator: **Jordyn Jones** (slug: `jordyn-jones`)
- 7 subreddits linked via `HAS_SOURCE` relationships
- 532 posts tagged with `entity_matched = "Jordyn Jones"`
- All linked via `ABOUT` relationships to Creator node

## Graph Structure

```
(Creator: Jordyn Jones)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesBooty)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesCandy)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJones_gooners)
  ├── [:HAS_SOURCE] → (Subreddit: jordynjonesbody)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesSimp)
  ├── [:HAS_SOURCE] → (Subreddit: JordynJonesSnark)
  └── [:HAS_SOURCE] → (Subreddit: jordynjones)

(Post)-[:POSTED_IN]→(Subreddit)
(Post)-[:ABOUT]→(Creator)
Post.entity_matched = "Jordyn Jones"
```

## Export Format

JSON Lines (ndjson) format, one record per line:

```json
{
  "id": "reddit_post_id",
  "title": "Post title",
  "created_utc": "2026-01-01T21:29:19",
  "score": 58,
  "num_comments": 1,
  "url": "https://reddit.com/...",
  "permalink": "/r/subreddit/comments/...",
  "entity_matched": "Jordyn Jones",
  "over_18": true,
  "creator_slug": "jordyn-jones",
  "creator_name": "Jordyn Jones",
  "subreddit": "JordynJonesCandy"
}
```

## Status

Target: 1000 posts
Achieved: 785 valid posts
Completion: 78.5%

**Reason for not reaching 1000**:
- All available Jordyn Jones subreddits have been exhausted
- Additional subreddits either don't exist or are private/deleted
- No more new posts available from current sources

## Next Steps

To increase post count:
1. Add more creators with their associated subreddits
2. Poll other Reddit communities
3. Add other platform sources (Instagram, Twitter, etc.)

## Commands Used

```bash
# Setup entity mappings (one-time)
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --setup

# Poll specific creator
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --creator jordyn-jones --max-posts 1000

# Poll all creators
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py
```
