# YouTube Channel Subscription Tests

**IMPORTANT**: All code runs in Docker containers. See [YOUTUBE_SUBSCRIPTION_DOCKER.md](YOUTUBE_SUBSCRIPTION_DOCKER.md) for complete Docker setup and usage guide.

Quick command prefix: `docker exec -w /home/jovyan/workspace jupyter`

This directory contains comprehensive tests for the YouTube channel subscription feature, including Redis caching, health checks, and entity management interfaces.

## Files

### Test Files

- `tests/test_youtube_channel_subscription.py` - Comprehensive unit tests for YouTube subscriptions
  - Tests for creator initialization
  - Tests for YouTube handle addition
  - Tests for Redis caching
  - Tests for Neo4j health checks
  - Tests for cache fallback to graph
  - Tests for subscription listing and management
  - Tests for creator entity interface (CRUD operations)

### Init Scripts

- `src/feed/storage/migrations/013_youtube_channel_subscription_init.cypher` - Neo4j initialization script
  - Creates YouTube platform
  - Creates Fasffy creator with YouTube handle
  - Creates Miss Katie creator with YouTube handle
  - Sets up subscriptions to YouTube
  - Creates sample video media nodes
  - Verification queries

### Scripts

- `init_youtube_subscriptions.py` - Main initialization and testing script
  - Runs Cypher init script
  - Verifies test data
  - Tests Redis caching
  - Tests Redis health checks
  - Tests Neo4j health checks
  - Reports subscription health status
  - Lists all subscriptions

- `src/feed/services/youtube_subscription_service.py` - Service interface for managing subscriptions
  - Create/update creators
  - Add YouTube handles
  - Create/manage subscriptions
  - Get creators (with caching)
  - Invalidate cache
  - List subscriptions
  - Get subscription health
  - Search creators
  - Health checks (Redis, Neo4j)

## Test Data

### Fasffy

- **Name**: Fasffy
- **Slug**: fasffy
- **Bio**: Content creator and streamer - Testing memes and challenges
- **YouTube Handle**: @Fasffy
- **YouTube URL**: https://www.youtube.com/@Fasffy
- **Followers**: 150,000
- **Sample Video**: "These Memes Challenge Me..." (video_id: 2vh31BrqhJQ)

### Miss Katie

- **Name**: Miss Katie
- **Slug**: misskatie
- **Bio**: YouTube content creator - Lifestyle and vlogs
- **YouTube Handle**: @MissKatie
- **YouTube URL**: https://www.youtube.com/@MissKatie
- **Followers**: 85,000
- **Sample Video**: "A Day in My Life"

## Usage

### Running Unit Tests

```bash
# Run all YouTube subscription tests (via Docker)
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -v

# Run specific test class
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py::TestYouTubeChannelSubscription -v

# Run specific test
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py::TestYouTubeChannelSubscription::test_init_creators_in_graph -v
```

### Running Init Script

```bash
# Run in Docker container
docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py

# Run locally
python3 init_youtube_subscriptions.py
```

Expected output:
```
======================================================================
INITIALIZING YOUTUBE CHANNEL SUBSCRIPTION DATA
======================================================================

Running init script: 013_youtube_channel_subscription_init.cypher
Query 1: ✓ Executed successfully
...

======================================================================
VERIFYING TEST DATA
======================================================================

✓ Found 2 test creators:
  - Fasffy (@fasffy)
    Bio: Content creator and streamer - Testing memes and challenges...
  - Miss Katie (@misskatie)
    Bio: YouTube content creator - Lifestyle and vlogs...

✓ Found 2 YouTube handles:
  - Fasffy: @Fasffy
    URL: https://www.youtube.com/@Fasffy
  - Miss Katie: @MissKatie
    URL: https://www.youtube.com/@MissKatie

✓ Found 2 active subscriptions:
  - Fasffy: active (every 1h)
  - Miss Katie: active (every 1h)

✓ Found 2 test videos:
  - Fasffy: These Memes Challenge Me...
    Published: 2025-12-26T...
  - Miss Katie: A Day in My Life
    Published: 2025-12-28T...

======================================================================
TESTING REDIS CACHE
======================================================================

Caching Fasffy data with key: creator:fasffy
✓ Fasffy data cached (TTL: 1 hour)

Caching Miss Katie data with key: creator:misskatie
✓ Miss Katie data cached (TTL: 1 hour)

✓ Retrieved Fasffy from cache: Fasffy

Fasffy cache TTL: 3599 seconds

======================================================================
REDIS HEALTH CHECK
======================================================================

✓ Redis PING: PONG
✓ Redis version: 7.x.x
✓ Connected clients: 5
✓ Used memory: 15.2M
✓ Database size: 42 keys

======================================================================
NEO4J HEALTH CHECK
======================================================================

✓ Neo4j connection: OK
✓ Node labels: Creator, Handle, Platform, Media, Video, Post, Thread...
✓ Relationship types: OWNS_HANDLE, ON_PLATFORM, PUBLISHED, SUBSCRIBED_TO...
✓ Total nodes: 152

======================================================================
SUBSCRIPTION HEALTH STATUS
======================================================================

✓ Fasffy (@Fasffy)
   Status: HEALTHY
   Last successful poll: 2025-12-28T...
   Poll interval: 1 hours
   Polls (24h): 24
   Errors (24h): 0

✓ Miss Katie (@MissKatie)
   Status: HEALTHY
   Last successful poll: 2025-12-28T...
   Poll interval: 1 hours
   Polls (24h): 48
   Errors (24h): 1

======================================================================
ALL YOUTUBE CHANNEL SUBSCRIPTIONS
======================================================================

Name: Fasffy
  Slug: fasffy
  Handle: @Fasffy
  URL: https://www.youtube.com/@Fasffy
  Followers: 150,000
  Subscription: active (poll every 1h)

Name: Miss Katie
  Slug: misskatie
  Handle: @MissKatie
  URL: https://www.youtube.com/@MissKatie
  Followers: 85,000
  Subscription: active (poll every 1h)

======================================================================
SUMMARY
======================================================================
✓ Redis Health: OK
✓ Neo4j Health: OK
✓ Test data loaded successfully
```

### Using the Service Interface

**Note**: Run these via `docker exec` or inside container shell:
```bash
# Method 1: docker exec one-liner
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
<your code here>
"

# Method 2: Enter shell first
docker exec -it jupyter bash
cd /home/jovyan/workspace
python3 -c "<your code>"
```

```python
# Run this code in container (add sys.path.insert(0, '/home/jovyan/workspace/src'))
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService

service = YouTubeSubscriptionService()

# Create a new creator
creator = service.create_creator(
    name="New Creator",
    slug="new-creator",
    bio="Test creator",
    avatar_url="https://example.com/avatar.jpg"
)

# Add YouTube handle
service.add_youtube_handle(
    creator_slug="new-creator",
    handle="@NewCreator",
    display_name="New Creator",
    profile_url="https://www.youtube.com/@NewCreator",
    follower_count=50000,
    verified=True
)

# Create subscription
service.create_subscription(
    creator_slug="new-creator",
    poll_interval_hours=2
)

# Get creator (uses cache)
creator_data = service.get_creator_by_slug("new-creator")
print(creator_data)

# List all subscriptions
subscriptions = service.list_all_subscriptions()
for sub in subscriptions:
    print(f"{sub['creator_name']}: {sub['handle_username']}")

# Get subscription health
health = service.get_subscription_health()
for sub in health:
    status_icon = "✓" if sub['status'] == 'healthy' else "✗"
    print(f"{status_icon} {sub['creator_name']}: {sub['status']}")

# Search creators
results = service.search_creators("katie")
for creator in results:
    print(f"{creator['name']} (@{creator['slug']})")

# Update subscription status
service.update_subscription_status(
    creator_slug="fasffy",
    last_successful_poll=datetime.utcnow(),
    increment_poll_count=True
)

# Invalidate cache
service.invalidate_creator_cache("fasffy")

# Health checks
redis_health = service.health_check_redis()
neo4j_health = service.health_check_neo4j()
overall = service.get_overall_health()

print(f"Overall status: {overall['overall_status']}")
```

## Test Coverage

### Unit Tests (`test_youtube_channel_subscription.py`)

#### TestYouTubeChannelSubscription
- `test_init_creators_in_graph` - Test creator node creation
- `test_init_platform_in_graph` - Test platform node creation
- `test_add_youtube_handle_to_creator` - Test handle addition with relationship
- `test_redis_cache_creator_data` - Test Redis caching
- `test_redis_health_check` - Test Redis health check
- `test_neo4j_health_check` - Test Neo4j health check
- `test_get_creator_with_handles_from_graph` - Test retrieval with handles
- `test_cache_miss_fallback_to_graph` - Test cache miss fallback
- `test_list_all_youtube_subscriptions` - Test subscription listing
- `test_update_subscription_status` - Test subscription status updates
- `test_get_subscription_health_status` - Test health status queries

#### TestCreatorEntityInterface
- `test_create_new_creator_entity` - Test creator creation
- `test_add_platform_handle_to_creator` - Test handle addition
- `test_get_creator_by_slug` - Test creator retrieval
- `test_search_creators_by_name` - Test search functionality
- `test_update_creator_metadata` - Test metadata updates
- `test_delete_creator_entity` - Test soft delete
- `test_invalidate_cache_on_update` - Test cache invalidation

## Graph Schema

### Nodes

- `Creator` - Canonical creator entity
- `Handle` - Platform-specific account
- `Platform` - Platform (YouTube)
- `Media:Video` - Video content
- `Post` - Social media post
- `Thread` - Discussion thread

### Relationships

- `(:Creator)-[:OWNS_HANDLE]->(:Handle)` - Creator owns handle
- `(:Handle)-[:ON_PLATFORM]->(:Platform)` - Handle belongs to platform
- `(:Creator)-[:SUBSCRIBED_TO]->(:Platform)` - Subscription for polling
- `(:Handle)-[:PUBLISHED]->(:Media:Video)` - Handle published video
- `(:Media:Video)-[:SOURCED_FROM]->(:Platform)` - Video sourced from platform

## Redis Cache Keys

- `creator:{slug}` - Creator data (TTL: 1 hour)
  ```json
  {
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Fasffy",
    "slug": "fasffy",
    "bio": "...",
    "avatar_url": "..."
  }
  ```

## Health Check Endpoints

### Redis Health
- PING command
- INFO stats (version, clients, memory)
- DBSIZE (key count)

### Neo4j Health
- Basic query test
- Node labels count
- Relationship types count
- Total node count

### Subscription Health
- Last successful poll time
- 24h poll count
- 24h error count
- Status (healthy/warning/unhealthy based on last poll)

## Troubleshooting

### Tests Fail with Import Errors
Make sure dependencies are installed:
```bash
pip install pytest redis neo4j pydantic
```

### Redis Connection Failed
Check Redis is running:
```bash
docker ps | grep redis
# Check .env for VALKEY_URI
```

### Neo4j Connection Failed
Check Neo4j is running:
```bash
docker ps | grep neo4j
# Check .env for NEO4J_URI
```

### Cache Not Working
Check Redis has data:
```bash
docker exec -it jupyter redis-cli KEYS "creator:*"
```

### Init Script Not Running
Check Neo4j migration directory:
```bash
ls -la src/feed/storage/migrations/013_youtube_channel_subscription_init.cypher
```

## Next Steps

1. **Implement YouTube RSS/API polling** - Add service to poll YouTube for new videos
2. **Add video ingestion** - Process new videos and create Media:Video nodes
3. **Implement queue management** - Add tasks to queue for video processing
4. **Add webhooks** - Support real-time video notifications
5. **Create monitoring dashboard** - Visualize subscription health and polling activity
