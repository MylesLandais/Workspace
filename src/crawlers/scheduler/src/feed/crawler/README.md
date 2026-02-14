# Modular Reddit Crawler

A modular, testable Reddit crawler for monitoring subreddits and collecting posts.

## Features

- **Modular Design**: Easy to test and extend
- **Configurable**: Adjust delays, limits, and behavior via `CrawlerConfig`
- **Multiple Modes**: Support for dry-run, mock, and production modes
- **Testable**: Can be instantiated with mock dependencies for unit testing

## Usage

### Quick Test (Dry-Run Mode)

```bash
# Test without writing to database
python test_crawler.py --mode dry-run
```

### Mock Mode

```bash
# Test with mock data (no network requests)
python test_crawler.py --mode mock
```

### Production Mode

```bash
# Run with real data and database writes
python test_crawler.py --mode production
```

### Production Crawler

```bash
# Run the full production crawler (100 subreddits, infinite cycles)
python run_crawler.py
```

## Programmatic Usage

```python
from feed.crawler.reddit_crawler import RedditCrawler, CrawlerConfig

# Create configuration
config = CrawlerConfig(
    subreddits=["TaylorSwift", "TaylorSwiftPictures"],
    request_delay_min=2.0,
    request_delay_max=5.0,
    max_cycles=1,
    dry_run=False,
)

# Create and run crawler
crawler = RedditCrawler(config)
crawler.run()
```

## Configuration Options

- `subreddits`: List of subreddit names to monitor
- `request_delay_min/max`: Delay between requests (seconds)
- `subreddit_delay_min/max`: Delay between subreddits (seconds)
- `cycle_delay_min/max`: Delay between cycles (seconds)
- `step_delay_min/max`: Delay before/after operations (seconds)
- `max_pages`: Maximum pages to fetch per subreddit
- `limit_per_page`: Posts per page (max 100)
- `max_cycles`: Maximum cycles to run (None = infinite)
- `dry_run`: If True, don't write to database
- `mock`: If True, use mock data (no network requests)

## Testing

The crawler can be easily tested with dependency injection:

```python
from unittest.mock import Mock

# Create mock dependencies
mock_reddit = Mock()
mock_engine = Mock()
mock_neo4j = Mock()

config = CrawlerConfig(subreddits=["test"], max_cycles=1, dry_run=True)
crawler = RedditCrawler(
    config,
    reddit_adapter=mock_reddit,
    polling_engine=mock_engine,
    neo4j_connection=mock_neo4j,
)

# Run test
crawler.run()
```




