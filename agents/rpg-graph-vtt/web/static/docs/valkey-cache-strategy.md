# Valkey Cache Strategy for Dice Rolls

## Overview

Valkey (Redis 7.x compatible) is used for caching ephemeral data related to dice rolls, sessions, and hot-path queries. This document defines key patterns, TTL policies, and invalidation rules.

## Key Patterns

All keys use the `rpg:` namespace prefix to avoid collisions.

### Character Data Cache
- **Pattern**: `rpg:character:{uuid}`
- **Type**: Hash
- **TTL**: 3600 seconds (1 hour)
- **Contents**: 
  ```json
  {
    "uuid": "character-uuid",
    "name": "Character Name",
    "ability_modifiers": {"str": 3, "dex": 1, ...},
    "cached_at": "2024-01-01T00:00:00Z"
  }
  ```
- **Invalidation**: On character update, delete key

### Recent Roll History Cache
- **Pattern**: `rpg:character:{uuid}:rolls`
- **Type**: Sorted Set (ZSET)
- **TTL**: 3600 seconds (1 hour)
- **Score**: Timestamp (Unix epoch)
- **Member**: JSON string of roll data
- **Max Members**: 50 (keep last 50 rolls)
- **Contents**: 
  ```json
  {
    "roll_uuid": "roll-uuid",
    "notation": "1d20+5",
    "total": 18,
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```
- **Invalidation**: Expires after TTL, or manually delete on character deletion

### Session State Cache
- **Pattern**: `rpg:session:{session_id}`
- **Type**: Hash
- **TTL**: 86400 seconds (24 hours)
- **Contents**:
  ```json
  {
    "user_id": "user-uuid",
    "character_uuid": "character-uuid",
    "last_activity": "2024-01-01T00:00:00Z",
    "active_rolls": ["roll-uuid-1", "roll-uuid-2"]
  }
  ```
- **Invalidation**: Expires after TTL, or delete on logout

### Rate Limit Counters
- **Pattern**: `rpg:ratelimit:{endpoint}:{ip_address}`
- **Type**: String (counter)
- **TTL**: 60 seconds (1 minute)
- **Contents**: Integer count of requests
- **Invalidation**: Expires after TTL (sliding window)

### Roll Result Cache (Individual Rolls)
- **Pattern**: `rpg:roll:{roll_uuid}`
- **Type**: Hash
- **TTL**: 3600 seconds (1 hour)
- **Contents**:
  ```json
  {
    "roll_uuid": "roll-uuid",
    "notation": "1d20+5",
    "results": [{"die_type": "d20", "value": 15, "modifier": 5}],
    "total": 20,
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```
- **Invalidation**: Expires after TTL

## Data Structure Usage

### Strings
- Rate limit counters
- Simple flags/booleans

### Hashes
- Character data
- Session state
- Roll results
- Complex objects with multiple fields

### Sorted Sets (ZSET)
- Roll history (sorted by timestamp)
- Leaderboards (if implemented)
- Time-ordered lists

### Lists
- Queue for background processing (if needed)
- Recent activity feeds

## TTL Strategy

| Cache Type | TTL | Rationale |
|------------|-----|-----------|
| Character Data | 1 hour | Balance freshness vs. load |
| Recent Roll History | 1 hour | Hot-path data, recent enough |
| Session State | 24 hours | Active session duration |
| Rate Limit Counters | 1 minute | Sliding window for rate limiting |
| Roll Results | 1 hour | Recent rolls are frequently accessed |

## Invalidation Rules

### Character Updates
```python
# When character is updated:
redis.delete(f"rpg:character:{character_uuid}")
# Roll history remains cached (separate key)
```

### New Roll Created
```python
# Add to roll history cache:
roll_data = {
    "roll_uuid": roll_uuid,
    "notation": notation,
    "total": total,
    "timestamp": timestamp.isoformat()
}
redis.zadd(
    f"rpg:character:{character_uuid}:rolls",
    {json.dumps(roll_data): timestamp.timestamp()}
)
# Trim to last 50
redis.zremrangebyrank(f"rpg:character:{character_uuid}:rolls", 0, -51)
# Set TTL
redis.expire(f"rpg:character:{character_uuid}:rolls", 3600)

# Cache individual roll
redis.hset(f"rpg:roll:{roll_uuid}", mapping=roll_data)
redis.expire(f"rpg:roll:{roll_uuid}", 3600)
```

### Session Management
```python
# On login:
redis.hset(f"rpg:session:{session_id}", mapping=session_data)
redis.expire(f"rpg:session:{session_id}", 86400)

# On logout:
redis.delete(f"rpg:session:{session_id}")

# On activity:
redis.hset(f"rpg:session:{session_id}", "last_activity", now.isoformat())
redis.expire(f"rpg:session:{session_id}", 86400)  # Refresh TTL
```

### Rate Limiting
```python
# Check rate limit:
key = f"rpg:ratelimit:{endpoint}:{ip_address}"
count = redis.incr(key)
redis.expire(key, 60)  # 1 minute window

if count > limit:
    raise RateLimitExceeded()
```

## Cache Warming Strategy

### On Character Load
1. Check cache for character data
2. If miss, load from Neo4j and cache
3. Pre-load recent roll history (last 10 rolls)

### On Session Start
1. Load character data into cache
2. Pre-load recent roll history
3. Initialize session state

### Background Warming (Future)
- Pre-load roll history for active characters
- Warm cache for party members when one character loads

## Consistency Requirements

### Eventual Consistency (Acceptable)
- Roll history cache (can be slightly stale)
- Character data cache (updates within 1 hour)

### Immediate Consistency (Required)
- Active session state (must reflect current state)
- Rate limit counters (must be accurate)

## Cache Hit Rate Targets

- Character data: > 80% hit rate
- Recent roll history: > 70% hit rate
- Session state: > 90% hit rate
- Roll results: > 60% hit rate

## Monitoring

Track:
- Cache hit/miss rates per key pattern
- TTL expiration rates
- Memory usage
- Eviction rates (if memory limits reached)

## Example Implementation (Python)

```python
import redis
import json
from datetime import datetime, timedelta

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_character(character_uuid, character_data):
    key = f"rpg:character:{character_uuid}"
    redis_client.hset(key, mapping=character_data)
    redis_client.expire(key, 3600)  # 1 hour

def get_character(character_uuid):
    key = f"rpg:character:{character_uuid}"
    data = redis_client.hgetall(key)
    return data if data else None

def cache_roll(character_uuid, roll_uuid, roll_data):
    # Cache individual roll
    roll_key = f"rpg:roll:{roll_uuid}"
    redis_client.hset(roll_key, mapping=roll_data)
    redis_client.expire(roll_key, 3600)
    
    # Add to character's roll history
    history_key = f"rpg:character:{character_uuid}:rolls"
    timestamp = datetime.now().timestamp()
    redis_client.zadd(history_key, {json.dumps(roll_data): timestamp})
    redis_client.zremrangebyrank(history_key, 0, -51)  # Keep last 50
    redis_client.expire(history_key, 3600)

def get_recent_rolls(character_uuid, limit=10):
    key = f"rpg:character:{character_uuid}:rolls"
    rolls = redis_client.zrevrange(key, 0, limit - 1)
    return [json.loads(roll) for roll in rolls]
```

## Migration Notes

- All keys use `rpg:` prefix for namespacing
- TTLs are set on write operations
- Use `EXPIRE` to refresh TTL on access (if needed)
- Monitor memory usage and adjust TTLs if needed
- Consider Redis eviction policy: `allkeys-lru` for production



