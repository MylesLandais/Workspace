# Entity-Based Reddit Polling

## Overview

Modular entity-based Reddit polling system that:
1. Maps Creator entities to their Subreddit sources in Neo4j
2. Queries the graph for entity relationships
3. Polls subreddits and tags posts with `entity_matched`
4. Links posts to Creator nodes via `ABOUT` relationships

## Usage

### Setup (one-time)

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --setup
```

This creates:
- Creator node with slug `jordyn-jones`
- Links to subreddits: JordynJonesCandy, JordynJonesBooty, jordynjonesbody, JordynJones_gooners

### Poll all creators

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py
```

### Poll specific creator

```bash
docker compose exec jupyterlab python /home/jovyan/workspaces/poll_creator_sources.py --creator jordyn-jones
```

### Options

- `--max-posts N` - Max posts per creator (default: 500)
- `--delay-min N` - Min delay between subreddits (default: 10s)
- `--delay-max N` - Max delay between subreddits (default: 30s)
- `--creator SLUG` - Poll only specific creator

## Graph Schema

```
(Creator)-[:HAS_SOURCE]->(Subreddit)
(Post)-[:POSTED_IN]->(Subreddit)
(Post)-[:ABOUT]->(Creator)
Post.entity_matched = "Entity Name"
```

## Adding New Creators

Edit `setup_creator_mapping()` in `poll_creator_sources.py`:

```python
mappings = {
    "jordyn-jones": "Jordyn Jones",
    "new-creator": "Creator Name",
}

creator_sources = {
    "jordyn-jones": [
        "JordynJonesCandy",
        "JordynJonesBooty",
    ],
    "new-creator": [
        "Subreddit1",
        "Subreddit2",
    ],
}
```

Run `--setup` to create mappings.

## Verification

Query posts with entity tagging:

```cypher
MATCH (p:Post) 
WHERE p.entity_matched IS NOT NULL 
RETURN p.entity_matched, count(p)
```

Query creator sources:

```cypher
MATCH (c:Creator)-[:HAS_SOURCE]->(s:Subreddit)
RETURN c.name, collect(s.name)
```
