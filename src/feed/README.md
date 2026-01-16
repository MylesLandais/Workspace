# feed - Social Media Consumption Engine

An extensible framework for consuming and analyzing social media data, starting with Reddit.

## Quick Start

### Test with r/BrookeMonkTheSecond

```bash
# Mock mode (no real network requests)
python test_feed_brooke.py

# Real mode (makes actual API calls)
python test_feed_brooke.py --real

# Dry run (fetches but doesn't save to database)
python test_feed_brooke.py --real --dry-run
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables** in `.env`:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   VALKEY_URI=redis://localhost:6379
   VALKEY_PASSWORD=  # Optional
   FEED_USER_AGENT=feed/1.0 (by /u/yourusername)
   ```

3. **Run schema migration** (automatically runs on first use, or manually):
   ```cypher
   // In Neo4j browser or cypher-shell
   // Run src/feed/storage/migrations/001_initial_schema.cypher
   ```

## Usage

### Basic Polling

```python
from feed.platforms.reddit import RedditAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection

# Initialize
reddit = RedditAdapter(mock=False)  # Set mock=True for testing
neo4j = get_connection()
engine = PollingEngine(reddit, neo4j)

# Poll a subreddit
posts = engine.poll_source("BrookeMonkTheSecond", sort="new", max_pages=5)
print(f"Collected {len(posts)} posts")
```

### Mock Mode for Testing

```python
# Use mock mode to test without network requests
reddit = RedditAdapter(mock=True)
# Returns sample mock data
```

## Architecture

- **Platform Adapters** (`platforms/`): Abstract interface for different social media platforms
- **Polling Engine** (`polling/`): Handles rate-limited data collection with deduplication
- **Storage** (`storage/`): Neo4j for graph relationships, Valkey for caching
- **Models** (`models/`): Pydantic models for type safety

## Graph Schema

- **Nodes**: `Post`, `Subreddit`, `User`
- **Relationships**: 
  - `(:User)-[:POSTED]->(:Post)`
  - `(:Post)-[:POSTED_IN]->(:Subreddit)`

## Features

- Rate-limited polling with human-like delays
- Automatic deduplication
- Graph-based storage for relationship queries
- Extensible platform adapter pattern
- Mock mode for testing

## Future Enhancements

- Time series analysis
- Keyword tracking
- Visualization tools
- Additional platform adapters (Twitter/X, Instagram, etc.)








