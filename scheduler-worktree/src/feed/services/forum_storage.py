"""Storage utilities for forum threads and images in Neo4j."""

from typing import List, Dict, Optional
from ..storage.neo4j_connection import Neo4jConnection
from .forum_parser import ForumThread, ForumPost


class ForumStorage:
    """Store forum threads and images in Neo4j."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize forum storage.
        
        Args:
            neo4j: Neo4j connection
        """
        self.neo4j = neo4j
    
    def store_thread(
        self,
        thread: ForumThread,
        index_images: bool = True
    ) -> bool:
        """
        Store forum thread in Neo4j.
        
        Args:
            thread: ForumThread object
            index_images: If True, index images for reverse search
            
        Returns:
            True if stored successfully
        """
        try:
            # Create Forum node
            forum_query = """
            MERGE (f:Forum {url: $base_url})
            ON CREATE SET
                f.name = $forum_name,
                f.url = $base_url,
                f.created_at = datetime()
            RETURN f.url as url
            """
            
            base_url = '/'.join(thread.url.split('/')[:3])
            self.neo4j.execute_write(
                forum_query,
                parameters={
                    "base_url": base_url,
                    "forum_name": thread.forum_name
                }
            )
            
            # Create ForumThread node
            thread_query = """
            MATCH (f:Forum {url: $base_url})
            MERGE (t:ForumThread {thread_id: $thread_id})
            ON CREATE SET
                t.uuid = randomUUID(),
                t.thread_id = $thread_id,
                t.title = $title,
                t.url = $url,
                t.author = $author,
                t.created_at = datetime(),
                t.updated_at = datetime()
            ON MATCH SET
                t.updated_at = datetime()
            WITH t, f
            MERGE (f)-[:HAS_THREAD]->(t)
            RETURN t.uuid as uuid
            """
            
            self.neo4j.execute_write(
                thread_query,
                parameters={
                    "base_url": base_url,
                    "thread_id": thread.thread_id,
                    "title": thread.title,
                    "url": thread.url,
                    "author": thread.author
                }
            )
            
            # Store posts
            for post in (thread.posts or []):
                self._store_post(post, thread.thread_id)
            
            # Store images
            if thread.images and index_images:
                for img_url in thread.images:
                    self._store_thread_image(img_url, thread.thread_id)
            
            # Store tags
            if thread.tags:
                for tag in thread.tags:
                    self._store_tag(tag, thread.thread_id)
            
            return True
        except Exception as e:
            print(f"Error storing thread: {e}")
            return False
    
    def _store_post(
        self,
        post: ForumPost,
        thread_id: str
    ) -> None:
        """Store forum post."""
        query = """
        MATCH (t:ForumThread {thread_id: $thread_id})
        MERGE (p:ForumPost {post_id: $post_id})
        ON CREATE SET
            p.uuid = randomUUID(),
            p.post_id = $post_id,
            p.content = $content,
            p.author = $author,
            p.post_date = $post_date,
            p.created_at = datetime()
        ON MATCH SET
            p.updated_at = datetime()
        WITH p, t
        MERGE (t)-[:HAS_POST]->(p)
        RETURN p.uuid as uuid
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "thread_id": thread_id,
                "post_id": post.post_id,
                "content": post.content[:1000],  # Limit content length
                "author": post.author,
                "post_date": post.post_date
            }
        )
        
        # Store post images
        if post.images:
            for img_url in post.images:
                self._store_post_image(img_url, post.post_id)
    
    def _store_thread_image(
        self,
        img_url: str,
        thread_id: str
    ) -> None:
        """Store thread image and link to thread."""
        query = """
        MATCH (t:ForumThread {thread_id: $thread_id})
        MERGE (img:Image {url: $url})
        ON CREATE SET
            img.url = $url,
            img.source = 'forum',
            img.created_at = datetime()
        WITH img, t
        MERGE (t)-[:HAS_IMAGE]->(img)
        RETURN img.url as url
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "thread_id": thread_id,
                "url": img_url
            }
        )
    
    def _store_post_image(
        self,
        img_url: str,
        post_id: str
    ) -> None:
        """Store post image and link to post."""
        query = """
        MATCH (p:ForumPost {post_id: $post_id})
        MERGE (img:Image {url: $url})
        ON CREATE SET
            img.url = $url,
            img.source = 'forum_post',
            img.created_at = datetime()
        WITH img, p
        MERGE (p)-[:HAS_IMAGE]->(img)
        RETURN img.url as url
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "post_id": post_id,
                "url": img_url
            }
        )
    
    def _store_tag(
        self,
        tag: str,
        thread_id: str
    ) -> None:
        """Store tag and link to thread."""
        query = """
        MATCH (t:ForumThread {thread_id: $thread_id})
        MERGE (tag:Tag {name: $tag})
        ON CREATE SET
            tag.name = $tag,
            tag.created_at = datetime()
        WITH tag, t
        MERGE (t)-[:HAS_TAG]->(tag)
        RETURN tag.name as name
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "thread_id": thread_id,
                "tag": tag.lower()
            }
        )
    
    def get_thread_images(
        self,
        thread_id: str
    ) -> List[str]:
        """
        Get all images from a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List of image URLs
        """
        query = """
        MATCH (t:ForumThread {thread_id: $thread_id})-[:HAS_IMAGE]->(img:Image)
        RETURN collect(DISTINCT img.url) as images
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"thread_id": thread_id}
        )
        
        if result:
            return result[0].get("images", [])
        return []




