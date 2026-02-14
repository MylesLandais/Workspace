# Intelligent Reddit Feed Monitoring

This document describes the intelligent Reddit data feed system that uses post count statistics to determine optimal crawling policies.

## Overview

The intelligent feed system tracks subreddit post counts over time and uses this data to automatically adjust crawler behavior. High-activity subreddits are crawled more frequently with shorter delays, while low-activity subreddits are crawled less frequently to be respectful of Reddit's resources.

## Key Components

### 1. Subreddit Statistics Service (`src/feed/services/subreddit_stats.py`)

The `SubredditStatsService` provides methods to:

- **Get post counts by time range**: Query Reddit's API with `after`/`before` timestamps to count posts in a specific period
- **Get monthly post counts**: Fetch post counts for specific months
- **Get yearly post counts**: Aggregate post counts for entire years
- **Get rolling monthly counts**: Track post counts for the last N months
- **Calculate post velocity**: Determine average posts per day over a period
- **Estimate all-time posts**: Approximate total posts by querying from Reddit's founding (2005) to now
- **Store statistics**: Save statistics to Neo4j for future reference

### 2. Crawler Policy Service (`src/feed/services/crawler_policy.py`)

The `CrawlerPolicy` service uses statistics to determine:

- **Crawl frequency**: How often to check a subreddit (VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW)
- **Crawl delays**: Time between crawls (1-2 hours for very high activity, 3-7 days for very low)
- **Request delays**: Time between requests within a crawl (2-5 seconds for high activity, 15-45 seconds for low)
- **Page limits**: How many pages to fetch per crawl (5 pages for very high activity, 1 page for low)

### 3. Database Schema

The system stores statistics and policies on `Subreddit` nodes in Neo4j:

- `stats`: Map containing monthly_counts, yearly_counts, post_velocity, etc.
- `stats_updated_at`: DateTime when statistics were last updated
- `crawler_policy`: Map containing frequency, delays, page limits, etc.
- `policy_updated_at`: DateTime when policy was last updated

See migration `012_subreddit_statistics.cypher` for schema details.

## Usage Examples

### Fetch Monthly Post Counts

```python
from feed.services.subreddit_stats import SubredditStatsService
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
stats_service = SubredditStatsService(neo4j=neo4j)

# Get post count for a specific month
count = stats_service.get_monthly_post_count("TaylorSwift", 2024, 1)
print(f"January 2024: {count} posts")
```

### Calculate Post Velocity

```python
# Calculate average posts per day over last 3 months
velocity = stats_service.calculate_post_velocity("TaylorSwift", months=3)
print(f"Post velocity: {velocity:.2f} posts/day")
```

### Get Crawler Policy

```python
from feed.services.crawler_policy import CrawlerPolicy

policy_service = CrawlerPolicy(neo4j=neo4j, stats_service=stats_service)
policy = policy_service.get_subreddit_policy("TaylorSwift", months=3)

print(f"Frequency: {policy['frequency']}")
print(f"Post velocity: {policy['post_velocity']:.2f} posts/day")
print(f"Crawl delay: {policy['crawl_delay_seconds']['min']/3600:.1f}-{policy['crawl_delay_seconds']['max']/3600:.1f} hours")
print(f"Request delay: {policy['request_delay_seconds']['min']:.1f}-{policy['request_delay_seconds']['max']:.1f} seconds")
print(f"Max pages: {policy['max_pages_per_crawl']}")
```

### Store Statistics and Policies

```python
# Fetch and store statistics
monthly_counts = stats_service.get_rolling_monthly_counts("TaylorSwift", months=6)
velocity = stats_service.calculate_post_velocity("TaylorSwift", months=3)

stats = {
    "monthly_counts": monthly_counts,
    "post_velocity": velocity,
    "calculated_at": datetime.utcnow().isoformat(),
}

stats_service.store_subreddit_stats("TaylorSwift", stats)

# Store policy
policy = policy_service.get_subreddit_policy("TaylorSwift", months=3)
policy_service.store_policy("TaylorSwift", policy)
```

## Crawler Frequency Levels

The system classifies subreddits into five frequency levels based on post velocity:

| Level | Posts/Day | Crawl Frequency | Request Delay | Max Pages |
|-------|-----------|-----------------|---------------|-----------|
| VERY_HIGH | > 50 | Every 1-2 hours | 2-5 seconds | 5 pages |
| HIGH | 20-50 | Every 3-6 hours | 3-8 seconds | 3 pages |
| MEDIUM | 5-20 | Every 12-24 hours | 5-15 seconds | 2 pages |
| LOW | 1-5 | Every 1-2 days | 10-30 seconds | 1 page |
| VERY_LOW | < 1 | Every 3-7 days | 15-45 seconds | 1 page |

## Methods for Getting Post Counts

### 1. API-Style Queries

Use Reddit's JSON API with time range filters:

```python
# Query posts in 2017
after = datetime(2017, 1, 1)
before = datetime(2018, 1, 1)
count = stats_service.get_post_count_by_range("subreddit", after, before)
```

### 2. Rolling Monthly Metrics

Track post counts for the last N months:

```python
# Get last 12 months
counts = stats_service.get_rolling_monthly_counts("subreddit", months=12)
# Returns: {"2024-01": 150, "2024-02": 180, ...}
```

### 3. Yearly Aggregations

Sum monthly counts or query year-wide ranges:

```python
# Get count for entire year
count = stats_service.get_yearly_post_count("subreddit", 2024)
```

### 4. All-Time Estimates

Approximate by querying from Reddit's founding (2005) to now:

```python
# Estimate all-time posts (approximate)
count = stats_service.estimate_all_time_posts("subreddit", start_year=2005)
```

**Note**: Reddit doesn't expose native "all-time" post counts. For more complete historical coverage, consider using public Reddit datasets (e.g., BigQuery mirrors of submissions/comments).

## Alternative Data Sources

For more complete historical coverage:

1. **Subreddit Stats** (https://subredditstats.com/): Third-party analytics site with post volume graphs
2. **Reddit Mod Tools**: If you moderate the subreddit, use Mod Tools → Insights/Stats
3. **BigQuery Public Datasets**: Google BigQuery has mirrors of Reddit submissions/comments
4. **Pushshift-style APIs**: Many clones still mirror Pushshift behavior with count metadata

## Integration with Crawlers

To use intelligent policies in your crawler:

```python
from feed.services.crawler_policy import CrawlerPolicy
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
policy_service = CrawlerPolicy(neo4j=neo4j)

# Get policy for subreddit
policy = policy_service.get_subreddit_policy("TaylorSwift", months=3)

# Use policy values in crawler
crawl_delay_min = policy['crawl_delay_seconds']['min']
crawl_delay_max = policy['crawl_delay_seconds']['max']
request_delay_min = policy['request_delay_seconds']['min']
request_delay_max = policy['request_delay_seconds']['max']
max_pages = policy['max_pages_per_crawl']

# Apply to RedditAdapter
reddit = RedditAdapter(
    delay_min=request_delay_min,
    delay_max=request_delay_max,
)
```

## Best Practices

1. **Update statistics regularly**: Recalculate post velocity every few weeks to account for activity changes
2. **Store policies**: Save policies to Neo4j so crawlers can reference them without recalculating
3. **Monitor changes**: Track how post velocity changes over time to identify trending subreddits
4. **Respect rate limits**: Always use appropriate delays, especially for low-activity subreddits
5. **Handle errors gracefully**: If statistics can't be fetched, fall back to default (MEDIUM) policy

## Future Enhancements

- **Trending detection**: Identify subreddits with increasing post velocity
- **Seasonal patterns**: Account for seasonal variations in activity
- **Historical analysis**: Track how subreddit activity has changed over years
- **BigQuery integration**: Use BigQuery for more accurate all-time counts
- **Automated policy updates**: Periodically recalculate and update policies





