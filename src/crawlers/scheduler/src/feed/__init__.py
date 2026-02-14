"""Feed system - Clean architecture implementation.

This package provides a clean architecture for managing social media feed data
with caching, offline support, and multiple platform integrations.

Note: For Celery task scheduling, imports are deferred to task functions to avoid
loading heavy dependencies at Celery startup. This allows Celery to run tasks via
nix-shell execution rather than importing Python modules directly.
"""

__version__ = "1.0.0"

# Lazy imports - only imported when explicitly requested
# This prevents circular imports and allows Celery to start without
# loading the entire feed ecosystem

__all__ = [
    'DIContainer',
    'CachedPostRepository',
    'PostService',
    'OfflineStorage'
]


def __getattr__(name):
    """Lazy-load modules on demand."""
    if name == 'DIContainer':
        from .di import DIContainer
        return DIContainer
    elif name == 'CachedPostRepository':
        from .repositories import CachedPostRepository
        return CachedPostRepository
    elif name == 'PostService':
        from .services.post_service import PostService
        return PostService
    elif name == 'OfflineStorage':
        from .offline import OfflineStorage
        return OfflineStorage
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
