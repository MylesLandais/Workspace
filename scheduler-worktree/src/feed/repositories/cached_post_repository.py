"""Cached post repository implementation."""

from typing import Optional, List
from datetime import timedelta
import json

from ..interfaces.repository import PostRepository
from ..models.post import Post
from ..storage.neo4j_connection import get_connection
from ..storage.cache_adapter import CacheAdapter


class CachedPostRepository(PostRepository):
    """Repository with cache-first data access for posts."""
    
    def __init__(
        self,
        neo4j=None,
        cache: CacheAdapter = None,
        cache_ttl: timedelta = timedelta(hours=1)
    ):
        self.neo4j = neo4j or get_connection()
        self.cache = cache or CacheAdapter()
        self.cache_ttl = cache_ttl
    
    def _cache_key(self, post_id: str) -> str:
        """Generate cache key for post."""
        return f"post:{post_id}"
    
    def _cache_key_subreddit(self, subreddit: str, limit: int, offset: int) -> str:
        """Generate cache key for subreddit posts."""
        return f"subreddit:{subreddit}:posts:{limit}:{offset}"
    
    def _cache_key_user(self, user_id: str, limit: int, offset: int) -> str:
        """Generate cache key for user posts."""
        return f"user:{user_id}:posts:{limit}:{offset}"
    
    async def get_post(self, post_id: str) -> Optional[Post]:
        """Get post with cache-first strategy."""
        cache_key = self._cache_key(post_id)
        
        cached = await self.cache.get(cache_key)
        if cached:
            return Post(**cached)
        
        with self.neo4j.get_session() as session:
            result = session.run(
                "MATCH (p:Post {id: $id}) RETURN p",
                {"id": post_id}
            )
            record = result.single()
            
            if not record:
                return None
            
            post_dict = dict(record["p"])
            post = Post(**post_dict)
            
            await self.cache.set(cache_key, post_dict, ttl=self.cache_ttl)
            
            return post
    
    async def get_posts_by_subreddit(
        self,
        subreddit: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Get posts by subreddit with cache."""
        cache_key = self._cache_key_subreddit(subreddit, limit, offset)
        
        cached = await self.cache.get(cache_key)
        if cached:
            return [Post(**p) for p in cached]
        
        with self.neo4j.get_session() as session:
            result = session.run(
                """
                MATCH (p:Post)-[:IN_SUBREDDIT]->(s:Subreddit {name: $name})
                RETURN p
                ORDER BY p.created_utc DESC
                SKIP $offset
                LIMIT $limit
                """,
                {"name": subreddit, "offset": offset, "limit": limit}
            )
            
            posts = [Post(**dict(record["p"])) for record in result.records()]
            posts_dict = [p.dict() for p in posts]
            
            await self.cache.set(cache_key, posts_dict, ttl=self.cache_ttl)
            
            return posts
    
    async def get_posts_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Get posts by user with cache."""
        cache_key = self._cache_key_user(user_id, limit, offset)
        
        cached = await self.cache.get(cache_key)
        if cached:
            return [Post(**p) for p in cached]
        
        with self.neo4j.get_session() as session:
            result = session.run(
                """
                MATCH (p:Post)-[:AUTHORED_BY]->(u:User {id: $id})
                RETURN p
                ORDER BY p.created_utc DESC
                SKIP $offset
                LIMIT $limit
                """,
                {"id": user_id, "offset": offset, "limit": limit}
            )
            
            posts = [Post(**dict(record["p"])) for record in result.records()]
            posts_dict = [p.dict() for p in posts]
            
            await self.cache.set(cache_key, posts_dict, ttl=self.cache_ttl)
            
            return posts
    
    async def save_post(self, post: Post) -> None:
        """Save or update post."""
        with self.neo4j.get_session() as session:
            session.run(
                """
                MERGE (p:Post {id: $id})
                SET p.title = $title,
                    p.url = $url,
                    p.score = $score,
                    p.num_comments = $num_comments,
                    p.upvote_ratio = $upvote_ratio,
                    p.over_18 = $over_18,
                    p.selftext = $selftext,
                    p.created_utc = $created_utc
                MERGE (s:Subreddit {name: $subreddit})
                MERGE (p)-[:IN_SUBREDDIT]->(s)
                """,
                post.dict()
            )
        
        cache_key = self._cache_key(post.id)
        await self.cache.delete(cache_key)
        
        await self.cache.invalidate_pattern(
            f"subreddit:{post.subreddit}:posts:*"
        )
        
        if post.author:
            await self.cache.invalidate_pattern(
                f"user:{post.author}:posts:*"
            )
    
    async def save_posts(self, posts: List[Post]) -> None:
        """Save multiple posts."""
        with self.neo4j.get_session() as session:
            for post in posts:
                session.run(
                    """
                    MERGE (p:Post {id: $id})
                    SET p.title = $title,
                        p.url = $url,
                        p.score = $score,
                        p.num_comments = $num_comments,
                        p.upvote_ratio = $upvote_ratio,
                        p.over_18 = $over_18,
                        p.selftext = $selftext,
                        p.created_utc = $created_utc
                    MERGE (s:Subreddit {name: $subreddit})
                    MERGE (p)-[:IN_SUBREDDIT]->(s)
                    """,
                    post.dict()
                )
        
        for post in posts:
            cache_key = self._cache_key(post.id)
            await self.cache.delete(cache_key)
            await self.cache.invalidate_pattern(
                f"subreddit:{post.subreddit}:posts:*"
            )
            if post.author:
                await self.cache.invalidate_pattern(
                    f"user:{post.author}:posts:*"
                )
    
    async def delete_post(self, post_id: str) -> None:
        """Delete post."""
        with self.neo4j.get_session() as session:
            result = session.run(
                "MATCH (p:Post {id: $id}) RETURN p",
                {"id": post_id}
            )
            record = result.single()
            
            if record:
                post = Post(**record["p"].properties)
                session.run(
                    "MATCH (p:Post {id: $id}) DETACH DELETE p",
                    {"id": post_id}
                )
                
                await self.cache.delete(self._cache_key(post_id))
                await self.cache.invalidate_pattern(
                    f"subreddit:{post.subreddit}:posts:*"
                )
                if post.author:
                    await self.cache.invalidate_pattern(
                        f"user:{post.author}:posts:*"
                    )
