"""Service layer for business logic."""

from typing import Optional, List
from datetime import datetime

from feed.interfaces.repository import PostRepository
from feed.interfaces.adapter import PlatformAdapter
from feed.models.post import Post


class PostService:
    """Service for post operations."""
    
    def __init__(
        self,
        repository: PostRepository,
        adapter: PlatformAdapter
    ):
        self.repository = repository
        self.adapter = adapter
    
    async def sync_posts(
        self,
        source: str,
        limit: int = 100,
        sort: str = 'new'
    ) -> List[Post]:
        """
        Fetch posts from platform and save to repository.
        
        Args:
            source: Source identifier (e.g., subreddit)
            limit: Maximum number of posts to fetch
            sort: Sort order
            
        Returns:
            List of saved posts
        """
        raw_posts = await self.adapter.fetch_posts(source, limit=limit, sort=sort)
        
        posts = []
        for raw_post in raw_posts:
            try:
                post = Post(**raw_post)
                await self.repository.save_post(post)
                posts.append(post)
            except Exception as e:
                print(f"Error processing post: {e}")
                continue
        
        return posts
    
    async def get_post(self, post_id: str) -> Optional[Post]:
        """
        Get post by ID.
        
        Uses repository's cache-first strategy.
        """
        return await self.repository.get_post(post_id)
    
    async def get_posts_by_subreddit(
        self,
        subreddit: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Get posts by subreddit."""
        return await self.repository.get_posts_by_subreddit(subreddit, limit, offset)
    
    async def get_posts_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Get posts by user."""
        return await self.repository.get_posts_by_user(user_id, limit, offset)
    
    async def delete_post(self, post_id: str) -> None:
        """Delete post."""
        await self.repository.delete_post(post_id)
    
    async def search_posts(
        self,
        query: str,
        limit: int = 50
    ) -> List[Post]:
        """
        Search for posts by title or content.
        
        Note: This is a placeholder - implement full-text search
        based on your database capabilities.
        """
        return []
