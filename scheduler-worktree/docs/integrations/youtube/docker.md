# YouTube Subscription Tests - Docker Guide

## Important: This Code Runs in Docker Containers

All tests and scripts are designed to run inside Docker containers. The workspace is mounted at `/home/jovyan/workspace` inside the container.

## Docker Container Setup

The main containers used:
- **jupyter**: JupyterLab container (Python, Neo4j, Redis clients)
- **neo4j**: Neo4j database
- **redis** / **valkey**: Redis/Valkey cache

## Docker Commands

### Execute Commands Inside Jupyter Container

```bash
# Run Python script
docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py

# Run pytest
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -v

# Run Python one-liner
docker exec -w /home/jovyan/workspace jupyter python3 -c "print('hello')"

# Check Redis connection
docker exec -it jupyter redis-cli PING

# Check Neo4j connection
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
print(neo4j.execute_read('RETURN \"ok\" as status'))
"
```

### Access Container Shell

```bash
# Open shell in container
docker exec -it jupyter bash

# Once inside container
cd /home/jovyan/workspace
python3 init_youtube_subscriptions.py
pytest tests/test_youtube_channel_subscription.py -v
```

### Container Environment

- **Working Directory**: `/home/jovyan/workspace`
- **Python**: `/usr/bin/python3`
- **Python Path**: Automatically includes `/home/jovyan/workspace/src`

## Running Tests in Docker

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

### Run Tests with Markers

```bash
# Run only fast tests
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -m "not slow" -v

# Run all tests including slow
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -v
```

## Running Init Script in Docker

### Full Init and Test

```bash
docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py
```

### Data Init Only

```bash
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from init_youtube_subscriptions import YouTubeSubscriptionInitializer
init = YouTubeSubscriptionInitializer()
init.run_init_script()
init.verify_init_data()
"
```

### Health Checks Only

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

## Using Service Interface in Docker

### Python Script in Container

Create script `/home/jovyan/workspace/test_subscription_service.py`:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')

from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
from datetime import datetime

# Create service
service = YouTubeSubscriptionService()

# Get overall health
print("=" * 70)
print("SYSTEM HEALTH")
print("=" * 70)
health = service.get_overall_health()
print(f"Overall: {health['overall_status']}")
print(f"Redis: {health['redis']['status']}")
print(f"Neo4j: {health['neo4j']['status']}")
print()

# List subscriptions
print("=" * 70)
print("ALL SUBSCRIPTIONS")
print("=" * 70)
subscriptions = service.list_all_subscriptions()
for sub in subscriptions:
    print(f"  {sub['creator_name']}: {sub['handle_username']}")
    print(f"    URL: {sub['profile_url']}")
    print(f"    Followers: {sub['followers']:,}")
print()

# Get subscription health
print("=" * 70)
print("SUBSCRIPTION HEALTH")
print("=" * 70)
health_status = service.get_subscription_health()
for sub in health_status:
    status_icon = "✓" if sub['status'] == 'healthy' else "⚠"
    print(f"{status_icon} {sub['creator_name']}: {sub['status']}")
    print(f"    Last poll: {sub['last_successful_poll']}")
    print(f"    Polls (24h): {sub['poll_count_24h']}")
    print(f"    Errors (24h): {sub['error_count_24h']}")
print()

# Get creator (with cache)
print("=" * 70)
print("CREATOR DATA (WITH CACHE)")
print("=" * 70)
creator = service.get_creator_by_slug("fasffy")
if creator:
    print(f"  Name: {creator['name']}")
    print(f"  Slug: {creator['slug']}")
    print(f"  Bio: {creator['bio'][:50]}...")
    print(f"  Handles: {len(creator['handles'])}")
print()
```

Run it:
```bash
docker exec -w /home/jovyan/workspace jupyter python3 test_subscription_service.py
```

### One-Liner Examples

```bash
# Get creator
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
service = YouTubeSubscriptionService()
print(service.get_creator_by_slug('fasffy'))
"

# List subscriptions
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
import json
service = YouTubeSubscriptionService()
print(json.dumps(service.list_all_subscriptions(), indent=2))
"

# Check health
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
import json
service = YouTubeSubscriptionService()
print(json.dumps(service.get_overall_health(), indent=2))
"
```

## Redis Commands in Docker

### Access Redis CLI

```bash
# Inside Jupyter container (if redis-cli is available)
docker exec -it jupyter redis-cli PING

# Directly in Redis container
docker exec -it redis redis-cli PING
docker exec -it valkey redis-cli PING
```

### Redis Commands

```bash
# Check Redis health
docker exec -it redis redis-cli PING
docker exec -it redis redis-cli INFO
docker exec -it redis redis-cli DBSIZE

# Get cached creator data
docker exec -it redis redis-cli GET "creator:fasffy"

# Check cache TTL
docker exec -it redis redis-cli TTL "creator:fasffy"

# List all creator cache keys
docker exec -it redis redis-cli KEYS "creator:*"

# Clear all cache
docker exec -it redis redis-cli FLUSHDB
```

## Neo4j Commands in Docker

### Access Neo4j Shell

```bash
# Via Docker
docker exec -it neo4j cypher-shell -u neo4j -p password

# Or via Jupyter container if neo4j is network accessible
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
result = neo4j.execute_read('MATCH (c:Creator) RETURN count(c) as count')
print(result)
"
```

### Neo4j Queries

```bash
# Count creators
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
result = neo4j.execute_read('MATCH (c:Creator) RETURN c.name as name')
for r in result:
    print(r['name'])
"

# Get Fasffy with handles
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
result = neo4j.execute_read('''
MATCH (c:Creator {slug: \"fasffy\"})
OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
RETURN c.name, h.username
''')
print(result)
"
```

## Docker-Specific Considerations

### Environment Variables

The `.env` file is typically mounted in the Docker container. The init script will load it from:

```python
# In valkey_connection.py
if Path("/home/jovyan/workspaces/.env").exists():
    self.env_path = Path("/home/jovyan/workspaces/.env")
elif Path(".env").exists():
    self.env_path = Path(".env").absolute()
else:
    self.env_path = Path.home() / "Workspace" / "jupyter" / ".env"
```

### Network Access

From inside the `jupyter` container:
- Neo4j: accessible via `neo4j` hostname or `localhost`
- Redis/Valkey: accessible via `redis` or `valkey` hostname or `localhost`

### File Paths

Inside container:
- Workspace root: `/home/jovyan/workspace`
- Source code: `/home/jovyan/workspace/src`
- Tests: `/home/jovyan/workspace/tests`
- Migrations: `/home/jovyan/workspace/src/feed/storage/migrations`

### Python Path

Always add `/home/jovyan/workspace/src` to path when running scripts:

```python
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
```

### Persistent Data

- Neo4j data: Stored in Docker volume (typically `/data` inside neo4j container)
- Redis data: Stored in Docker volume (typically `/data` inside redis container)
- Workspace files: Mounted from host system

## Troubleshooting Docker Issues

### Container Not Running

```bash
# Check container status
docker ps -a | grep -E "jupyter|neo4j|redis|valkey"

# Start containers if stopped
docker start jupyter neo4j redis

# View logs
docker logs jupyter
docker logs neo4j
docker logs redis
```

### Import Errors in Container

```bash
# Verify Python path
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
print(sys.path)
"

# Check if source files exist
docker exec jupyter ls -la /home/jovyan/workspace/src/feed/services/
```

### Connection Issues

```bash
# Check if containers can communicate
docker exec jupyter ping -c 2 neo4j
docker exec jupyter ping -c 2 redis

# Check port bindings
docker ps | grep -E "7474|7687|6379"
```

### Volume Mount Issues

```bash
# Check volume mounts
docker inspect jupyter | grep -A 10 Mounts

# Check workspace files
docker exec jupyter ls -la /home/jovyan/workspace
```

## Quick Start Checklist

- [ ] Docker containers running: `docker ps | grep -E "jupyter|neo4j|redis"`
- [ ] Workspace mounted correctly: `docker exec jupyter ls -la /home/jovyan/workspace`
- [ ] Python path correct: `docker exec jupyter python3 -c "import sys; sys.path.insert(0, '/home/jovyan/workspace/src'); print(sys.path)"`
- [ ] Neo4j accessible: `docker exec -w /home/jovyan/workspace jupyter python3 -c "import sys; sys.path.insert(0, '/home/jovyan/workspace/src'); from feed.storage.neo4j_connection import get_connection; print(get_connection().execute_read('RETURN \"ok\" as status'))"`
- [ ] Redis accessible: `docker exec -it redis redis-cli PING`
- [ ] Tests pass: `docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -v`
- [ ] Init script runs: `docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py`

## Common Docker Workflows

### Full Test and Init Workflow

```bash
# 1. Check containers are running
docker ps | grep -E "jupyter|neo4j|redis"

# 2. Run init script
docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py

# 3. Run tests
docker exec -w /home/jovyan/workspace jupyter pytest tests/test_youtube_channel_subscription.py -v

# 4. Check health
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
print(YouTubeSubscriptionService().get_overall_health())
"

# 5. View data
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
import json
service = YouTubeSubscriptionService()
print(json.dumps(service.list_all_subscriptions(), indent=2))
"
```

### Debug Workflow

```bash
# 1. Enter container shell
docker exec -it jupyter bash

# 2. Navigate to workspace
cd /home/jovyan/workspace

# 3. Check Python path
python3 -c "import sys; sys.path.insert(0, '/home/jovyan/workspace/src'); from feed.storage.neo4j_connection import get_connection; print('OK')"

# 4. Run init script
python3 init_youtube_subscriptions.py

# 5. Run tests
pytest tests/test_youtube_channel_subscription.py -v

# 6. Check Redis
redis-cli KEYS "creator:*"

# 7. Exit container
exit
```

### Production Deployment Workflow

```bash
# 1. Update code on host (if using volume mounts)
# 2. Restart containers (if needed)
docker restart jupyter

# 3. Run migrations/init
docker exec -w /home/jovyan/workspace jupyter python3 init_youtube_subscriptions.py

# 4. Verify health
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, '/home/jovyan/workspace/src')
from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService
health = YouTubeSubscriptionService().get_overall_health()
assert health['overall_status'] == 'healthy'
print('System healthy')
"
```

## File Access in Docker

All files are accessible in `/home/jovyan/workspace` inside the container:

```
/home/jovyan/workspace/
├── init_youtube_subscriptions.py
├── tests/
│   ├── conftest.py
│   └── test_youtube_channel_subscription.py
└── src/
    └── feed/
        └── services/
            └── youtube_subscription_service.py
```

Always use `/home/jovyan/workspace` as the base path when running commands in Docker.
