# YouTube Subscription Quick Reference

**IMPORTANT**: This code runs in Docker containers. All commands should be run via `docker exec`. See [YOUTUBE_SUBSCRIPTION_DOCKER.md](YOUTUBE_SUBSCRIPTION_DOCKER.md) for complete Docker guide.

**Quick Docker prefix**: `docker exec -w /home/jovyan/workspace jupyter`

## Test Commands (via Docker)

### Run All Tests
```bash
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -v
```

### Run Specific Test Class
```bash
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py::TestYouTubeChannelSubscription -v
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py::TestCreatorEntityInterface -v
```

### Run Specific Test
```bash
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py::TestYouTubeChannelSubscription::test_init_creators_in_graph -v
```

### Run with Coverage
```bash
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py --cov=src/feed/services --cov-report=html
```

## Init Script Commands

### Run Full Init and Tests
```bash
docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py
```

### Run Only Data Init
```bash
# In Docker
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from init_youtube_subscriptions import YouTubeSubscriptionInitializer
init = YouTubeSubscriptionInitializer()
init.run_init_script()
init.verify_init_data()
"

# Local
python3 -c "
import sys
sys.path.insert(0, 'src')
from init_youtube_subscriptions import YouTubeSubscriptionInitializer
init = YouTubeSubscriptionInitializer()
init.run_init_script()
init.verify_init_data()
"
```

### Run Only Health Checks
```bash
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from init_youtube_subscriptions import YouTubeSubscriptionInitializer
init = YouTubeSubscriptionInitializer()
init.test_redis_health_check()
init.test_neo4j_health_check()
init.get_subscription_health_status()
"
```

## Service Interface Examples

**Note**: Run these via Docker exec or inside container shell (`docker exec -it jupyter bash`).

### Docker One-Liner Example
```bash
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
service = YouTubeSubscriptionService()
print(service.get_creator_by_slug('fasffy'))
"
```

### Create New Creator
```python
# Run via: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
# Or: docker exec -it jupyter bash -> python3 -c "<code>"

from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService

service = YouTubeSubscriptionService()

# Create creator
creator = service.create_creator(
    name="Test Creator",
    slug="test-creator",
    bio="Test bio",
    avatar_url="https://example.com/avatar.jpg"
)
print(f"Created: {creator['name']}")
```

### Add YouTube Handle
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
success = service.add_youtube_handle(
    creator_slug="test-creator",
    handle="@TestCreator",
    display_name="Test Creator",
    profile_url="https://www.youtube.com/@TestCreator",
    follower_count=10000,
    verified=True
)
print(f"Handle added: {success}")
```

### Create Subscription
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
success = service.create_subscription(
    creator_slug="test-creator",
    poll_interval_hours=2
)
print(f"Subscription created: {success}")
```

### Get Creator (with caching)
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
# First call - loads from graph
creator = service.get_creator_by_slug("fasffy")

# Second call - loads from cache
creator_cached = service.get_creator_by_slug("fasffy")

# Get without cache
creator_no_cache = service.get_creator_by_slug("fasffy", use_cache=False)
```

### List All Subscriptions
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
subscriptions = service.list_all_subscriptions()
for sub in subscriptions:
    print(f"{sub['creator_name']}: {sub['handle_username']}")
    print(f"  Followers: {sub['followers']:,}")
    print(f"  Status: {sub['subscription_status']}")
```

### Get Subscription Health
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
health = service.get_subscription_health()
for sub in health:
    status_icon = "✓" if sub['status'] == 'healthy' else "⚠"
    print(f"{status_icon} {sub['creator_name']}")
    print(f"   Status: {sub['status'].upper()}")
    print(f"   Last poll: {sub['last_successful_poll']}")
    print(f"   Polls (24h): {sub['poll_count_24h']}")
    print(f"   Errors (24h): {sub['error_count_24h']}")
```

### Search Creators
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
results = service.search_creators("katie")
for creator in results:
    print(f"{creator['name']} (@{creator['slug']})")
```

### Update Subscription Status
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
from datetime import datetime

success = service.update_subscription_status(
    creator_slug="fasffy",
    last_successful_poll=datetime.utcnow(),
    increment_poll_count=True,
    increment_error_count=False
)
```

### Invalidate Cache
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
deleted = service.invalidate_creator_cache("fasffy")
print(f"Cache cleared: {deleted}")
```

### Health Checks
```python
# Docker: docker exec -w /home/jovyan/workspace jupyter python3 -c "<code>"
# Redis health
redis_health = service.health_check_redis()
print(f"Redis: {redis_health['status']}")
print(f"  Version: {redis_health['version']}")
print(f"  Clients: {redis_health['connected_clients']}")
print(f"  Memory: {redis_health['used_memory']}")
print(f"  Keys: {redis_health['database_size']}")

# Neo4j health
neo4j_health = service.health_check_neo4j()
print(f"Neo4j: {neo4j_health['status']}")
print(f"  Labels: {neo4j_health['node_labels']}")
print(f"  Relationships: {neo4j_health['relationship_types']}")
print(f"  Nodes: {neo4j_health['total_nodes']}")

# Overall health
overall = service.get_overall_health()
print(f"Overall: {overall['overall_status']}")
```

## Neo4j Queries

### Get Creator with Handles
```cypher
MATCH (c:Creator {slug: 'fasffy'})
OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform)
RETURN c, collect({handle: h, platform: p}) as handles
```

### List All YouTube Subscriptions
```cypher
MATCH (c:Creator)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
WHERE r.status = 'Active' AND r.verified = true
OPTIONAL MATCH (c)-[sub:SUBSCRIBED_TO]->(p)
RETURN 
    c.name as creator_name,
    h.username as handle_username,
    h.profile_url as profile_url,
    sub.status as subscription_status,
    sub.last_polled_at as last_polled_at
ORDER BY c.name
```

### Get Subscription Health
```cypher
MATCH (c:Creator)-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
RETURN 
    c.name as creator_name,
    h.username as youtube_handle,
    CASE 
        WHEN sub.last_successful_poll > datetime() - duration('PT6H') 
        THEN 'healthy'
        WHEN sub.last_successful_poll > datetime() - duration('PT24H')
        THEN 'warning'
        ELSE 'unhealthy'
    END as status,
    sub.last_successful_poll,
    sub.poll_interval_hours,
    sub.poll_count_24h,
    sub.error_count_24h
```

### Get Recent Videos
```cypher
MATCH (c:Creator {slug: 'fasffy'})-[r:OWNS_HANDLE]->(h:Handle)-[pub:PUBLISHED]->(v:Media:Video)
RETURN v.title as title, v.source_url as url, v.publish_date as published
ORDER BY v.publish_date DESC
LIMIT 10
```

## Redis Commands

### Check Cached Creator Data
```bash
docker exec -it jupyter redis-cli GET "creator:fasffy"
```

### Check All Creator Cache Keys
```bash
docker exec -it jupyter redis-cli KEYS "creator:*"
```

### Get Cache TTL
```bash
docker exec -it jupyter redis-cli TTL "creator:fasffy"
```

### Clear All Cache
```bash
docker exec -it jupyter redis-cli FLUSHDB
```

### Redis Info
```bash
docker exec -it jupyter redis-cli INFO
docker exec -it jupyter redis-cli DBSIZE
docker exec -it jupyter redis-cli PING
```

## Troubleshooting Commands

### Check Neo4j Connection
```bash
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
result = neo4j.execute_read('RETURN \"ok\" as status')
print(result)
"
```

### Check Redis Connection
```bash
docker exec -it jupyter redis-cli PING
docker exec -it jupyter redis-cli INFO
```

### View Test Data in Neo4j
```bash
docker exec jupyter cypher-shell -u neo4j -p password -d neo4j "
MATCH (c:Creator) WHERE c.slug IN ['fasffy', 'misskatie']
OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
RETURN c.name, h.username
"
```

### Clear Test Data
```cypher
// Delete creators
MATCH (c:Creator) WHERE c.slug IN ['fasffy', 'misskatie'] DETACH DELETE c

// Verify
MATCH (c:Creator) WHERE c.slug IN ['fasffy', 'misskatie'] RETURN count(c)
```

## Test Data Reference

### Fasffy
- Slug: `fasffy`
- Handle: `@Fasffy`
- URL: `https://www.youtube.com/@Fasffy`
- Followers: 150,000
- Video ID: `2vh31BrqhJQ`
- UUID: `550e8400-e29b-41d4-a716-446655440001`

### Miss Katie
- Slug: `misskatie`
- Handle: `@MissKatie`
- URL: `https://www.youtube.com/@MissKatie`
- Followers: 85,000
- UUID: `550e8400-e29b-41d4-a716-446655440002`

## File Locations

```
tests/
  conftest.py                                    # Pytest fixtures
  test_youtube_channel_subscription.py              # Unit tests

src/feed/
  services/
    youtube_subscription_service.py                 # Service interface
  storage/
    migrations/
      013_youtube_channel_subscription_init.cypher # Init script

init_youtube_subscriptions.py                    # Main init/test script
YOUTUBE_SUBSCRIPTION_TESTS.md                    # Full documentation
YOUTUBE_SUBSCRIPTION_QUICKREF.md                # This file
```

## Test Checklist

- [ ] Unit tests pass: `pytest tests/test_youtube_channel_subscription.py -v`
- [ ] Init script runs successfully: `python3 init_youtube_subscriptions.py`
- [ ] Test data verified: Creators, handles, videos loaded
- [ ] Redis cache working: Can retrieve cached data
- [ ] Redis health check passing: PING, INFO, DBSIZE
- [ ] Neo4j health check passing: Basic query, labels, nodes
- [ ] Subscription health reporting: Status, poll counts, error counts
- [ ] Service interface methods working: CRUD, search, cache, health
- [ ] Cache invalidation: Updates clear cache properly
- [ ] Cache fallback: Miss falls back to graph
