# Feed System Architecture

Clean architecture implementation for social media feed data management, inspired by Kuroba-Experimental's Android architecture patterns adapted for Python.

## Architecture Overview

```
src/feed/
├── interfaces/          # Abstract interfaces (contracts)
│   ├── repository.py   # Data access contracts
│   └── adapter.py      # Platform adapter contracts
├── repositories/       # Concrete repository implementations
│   └── cached_post_repository.py  # Cache-first data access
├── services/          # Business logic layer
│   └── post_service.py
├── adapters/          # Platform-specific implementations
│   └── reddit_adapter.py  # Reddit API integration
├── storage/           # Data storage layer
│   ├── cache_adapter.py    # Redis cache
│   └── neo4j_connection.py # Graph database
├── offline/           # Offline storage
│   └── offline_storage.py  # SQLite local cache
├── di/               # Dependency injection
│   └── container.py
└── models/           # Data models
    └── post.py
```

## Key Patterns

### Repository Pattern
Abstracts data access behind clean interfaces:
- `PostRepository` - Contract for post data operations
- `CachedPostRepository` - Implementation with cache-first logic
- Network, cache, and offline storage transparently handled

### Adapter Pattern
Standardizes integration with different platforms:
- `PlatformAdapter` - Interface for social media platforms
- `RedditAdapter` - Reddit-specific implementation
- Easy to add new platforms (YouTube, Twitter, etc.)

### Service Layer
Business logic that coordinates repositories and adapters:
- `PostService` - High-level post operations
- Syncs data from platforms to repositories
- Handles caching and offline sync

### Dependency Injection
`DIContainer` manages service lifecycles:
- Singleton services by default
- Easy testing with mock implementations
- Centralized configuration

## Usage Example

```python
import asyncio
from feed import setup_container

async def main():
    container = setup_container(
        redis_url="redis://localhost:6379",
        offline_db_path=Path("~/.cache/feed/offline.db")
    )
    
    post_service = container.get('post_service')
    
    # Sync posts from subreddit
    posts = await post_service.sync_posts('python', limit=50)
    
    # Get post (cache-first)
    post = await post_service.get_post('abc123')
    
    # Get posts by subreddit
    posts = await post_service.get_posts_by_subreddit('python')

asyncio.run(main())
```

## Cache-First Strategy

All data access goes through this flow:
1. Check Redis cache
2. If miss, query Neo4j
3. Update cache with results
4. Return data

This provides:
- Fast responses for frequently accessed data
- Reduced database load
- Offline capability when combined with SQLite storage

## Offline Support

`OfflineStorage` provides:
- Local SQLite database
- Sync/unsynced status tracking
- Automatic purging of old data
- Statistics and monitoring

## Benefits

1. **Testability** - Mock repositories and adapters easily
2. **Maintainability** - Clear separation of concerns
3. **Scalability** - Easy to add new platforms and features
4. **Performance** - Cache-first data access
5. **Reliability** - Offline support and error handling

## Migration from Legacy Code

The legacy `RedditCrawler` can be refactored to use the new architecture:

```python
# Old: Direct coupling
crawler = RedditCrawler(config)
posts = crawler.reddit.fetch_posts(subreddit)

# New: Clean architecture
container = setup_container()
post_service = container.get('post_service')
posts = await post_service.sync_posts(subreddit)
```

## Next Steps

- Implement additional platform adapters (YouTube, Twitter)
- Add full-text search capability
- Implement background sync workers
- Add comprehensive tests
- Create monitoring and metrics
