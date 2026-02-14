"""Main application entry point."""

from feed.di.container import DIContainer
from feed.repositories.cached_post_repository import CachedPostRepository
from feed.services.post_service import PostService
from feed.storage.neo4j_connection import get_connection
from feed.storage.cache_adapter import CacheAdapter
from pathlib import Path


def setup_container(
    redis_url: str = "redis://localhost:6379",
    offline_db_path: Path = None
) -> DIContainer:
    """
    Setup and configure dependency injection container.
    
    Args:
        redis_url: Redis connection URL
        offline_db_path: Path to offline SQLite database
        
    Returns:
        Configured DIContainer
    """
    if offline_db_path is None:
        offline_db_path = Path.home() / ".cache" / "feed" / "offline.db"
        offline_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    container = DIContainer()
    
    container.register(
        'cache',
        lambda: CacheAdapter(redis_url=redis_url),
        singleton=True
    )
    
    container.register(
        'neo4j',
        lambda: get_connection(),
        singleton=True
    )
    
    container.register(
        'post_repo',
        lambda: CachedPostRepository(
            neo4j=container.get('neo4j'),
            cache=container.get('cache')
        ),
        singleton=True
    )
    
    container.register(
        'post_service',
        lambda: PostService(
            repository=container.get('post_repo'),
            adapter=None
        ),
        singleton=True
    )
    
    return container


async def main():
    """Main entry point."""
    container = setup_container()
    
    post_service = container.get('post_service')
    
    print("Feed system initialized")
    print("Available services:")
    print("  - post_service: Manage posts")
    print("  - post_repo: Data access layer")
    print("  - cache: Redis cache")
    print("  - neo4j: Neo4j database")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
