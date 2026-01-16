"""Comment threading and hierarchy support for YouTube comments."""

from typing import Dict, List, Optional
from collections import defaultdict

from feed.storage.neo4j_connection import get_connection

class CommentThread:
    """Service for managing comment threads and hierarchies."""
    
    def __init__(self):
        self.neo4j = get_connection()
    
    def get_comment_thread(self, video_id: str, root_comment_id: Optional[str] = None) -> List[Dict]:
        """
        Get comment thread for a video, optionally starting from a specific comment.
        
        Args:
            video_id: Video ID
            root_comment_id: If provided, only fetch this thread. Otherwise fetch all top-level comments.
        
        Returns:
            List of comments with nested replies
        """
        
        if root_comment_id:
            # Fetch single thread starting from root comment
            query = """
            MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(root:YouTubeComment {comment_id: $root_id})
            WITH root
            MATCH (root)<-[:PARENT_OF*0..]-(c:YouTubeComment)
            RETURN c {
                .comment_id, .text, .author, .author_id,
                .like_count, .reply_count, .is_reply, .parent_id,
                .timestamp
            } as comment
            ORDER BY c.timestamp
            """
            
            result = self.neo4j.execute_read(query, parameters={
                "video_id": video_id,
                "root_id": root_comment_id
            })
        else:
            # Fetch all top-level comments
            query = """
            MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
            WHERE c.is_reply = false OR c.parent_id = ''
            RETURN c {
                .comment_id, .text, .author, .author_id,
                .like_count, .reply_count, .is_reply, .parent_id,
                .timestamp
            } as comment
            ORDER BY c.like_count DESC, c.timestamp DESC
            LIMIT 100
            """
            
            result = self.neo4j.execute_read(query, parameters={"video_id": video_id})
        
        comments = [dict(r["comment"]) for r in result]
        
        # Build thread hierarchy
        thread_map = {c["comment_id"]: c for c in comments}
        thread_tree = []
        
        for comment in comments:
            comment["replies"] = []
            parent_id = comment.get("parent_id", "")
            
            if parent_id and parent_id in thread_map:
                # This is a reply, add to parent's replies
                thread_map[parent_id]["replies"].append(comment)
            else:
                # This is a top-level comment
                thread_tree.append(comment)
        
        return thread_tree
    
    def store_comment_thread(self, video_id: str, comments: List[Dict]) -> bool:
        """
        Store comments with proper parent-child relationships.
        
        Args:
            video_id: Video ID
            comments: List of comments with parent_id for replies
        
        Returns:
            True if successful
        """
        
        # Store comments and create PARENT_OF relationships
        for comment in comments:
            comment_id = comment["comment_id"]
            parent_id = comment.get("parent_id", "")
            text = comment.get("text", "")
            
            # Store the comment
            store_query = """
            MATCH (v:YouTubeVideo {video_id: $video_id})
            MERGE (c:YouTubeComment {comment_id: $comment_id})
            ON CREATE SET
                c.uuid = $uuid,
                c.text = $text,
                c.author = $author,
                c.author_id = $author_id,
                c.like_count = $like_count,
                c.reply_count = $reply_count,
                c.is_reply = $is_reply,
                c.parent_id = $parent_id,
                c.timestamp = datetime($timestamp),
                c.created_at = datetime(),
                c.video_id = $video_id
            ON MATCH SET
                c.text = $text,
                c.like_count = $like_count,
                c.reply_count = $reply_count,
                c.updated_at = datetime()
            MERGE (v)-[:HAS_COMMENT]->(c)
            RETURN c
            """
            
            self.neo4j.execute_write(store_query, parameters={
                "video_id": video_id,
                "comment_id": comment_id,
                "uuid": comment.get("uuid", ""),
                "text": text,
                "author": comment.get("author", ""),
                "author_id": comment.get("author_id", ""),
                "like_count": comment.get("like_count", 0),
                "reply_count": comment.get("reply_count", 0),
                "is_reply": comment.get("is_reply", False),
                "parent_id": parent_id,
                "timestamp": comment.get("timestamp", "")
            })
        
        # Create PARENT_OF relationships
        for comment in comments:
            comment_id = comment["comment_id"]
            parent_id = comment.get("parent_id", "")
            
            if parent_id and parent_id != comment_id:
                relationship_query = """
                MATCH (parent:YouTubeComment {comment_id: $parent_id})
                MATCH (child:YouTubeComment {comment_id: $comment_id})
                MERGE (parent)-[:PARENT_OF]->(child)
                RETURN count(*) > 0 as created
                """
                
                self.neo4j.execute_write(relationship_query, parameters={
                    "parent_id": parent_id,
                    "comment_id": comment_id
                })
        
        return True
    
    def get_comment_context(self, comment_id: str, depth: int = 2) -> Dict:
        """
        Get comment with parent comments for context.
        
        Args:
            comment_id: Comment ID to fetch
            depth: How many levels up to fetch (default: 2)
        
        Returns:
            Comment with context (parent comments)
        """
        
        query = f"""
        MATCH (target:YouTubeComment {{comment_id: $comment_id}})
        OPTIONAL MATCH (target)<-[:PARENT_OF*1..{depth}]-(parent:YouTubeComment)
        WITH target, collect(DISTINCT parent) as parents
        RETURN {{
            comment_id: target.comment_id,
            text: target.text,
            author: target.author,
            author_id: target.author_id,
            like_count: target.like_count,
            reply_count: target.reply_count,
            timestamp: target.timestamp,
            parent_id: target.parent_id,
            context: [p IN parents | {{
                comment_id: p.comment_id,
                text: p.text,
                author: p.author,
                like_count: p.like_count,
                timestamp: p.timestamp
            }}]
        }} as comment_with_context
        """
        
        result = self.neo4j.execute_read(query, parameters={"comment_id": comment_id})
        
        if result:
            return dict(result[0]["comment_with_context"])
        
        return None
    
    def get_comment_replies(self, comment_id: str, limit: int = 20) -> List[Dict]:
        """Get direct replies to a comment."""
        query = """
        MATCH (parent:YouTubeComment {comment_id: $comment_id})
        MATCH (parent)-[:PARENT_OF]->(reply:YouTubeComment)
        RETURN reply {
            .comment_id, .text, .author, .author_id,
            .like_count, .reply_count, .timestamp
        } as reply
        ORDER BY reply.like_count DESC, reply.timestamp DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(query, parameters={
            "comment_id": comment_id,
            "limit": limit
        })
        
        return [dict(r["reply"]) for r in result]
    
    def get_longest_threads(self, video_id: str, limit: int = 10) -> List[Dict]:
        """Get longest comment threads by depth."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(root:YouTubeComment)
        WHERE NOT root.is_reply OR root.parent_id = ''
        MATCH path = (root)<-[:PARENT_OF*0..]-(leaf:YouTubeComment)
        WITH root, length(path) as thread_depth, 
             count(path) as total_comments
        RETURN {
            comment_id: root.comment_id,
            text: root.text,
            author: root.author,
            like_count: root.like_count,
            reply_count: root.reply_count,
            thread_depth: thread_depth,
            total_comments: total_comments
        } as thread
        ORDER BY thread.total_comments DESC, thread.thread_depth DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(query, parameters={
            "video_id": video_id,
            "limit": limit
        })
        
        return [dict(r["thread"]) for r in result]
    
    def update_reply_counts(self, video_id: str) -> None:
        """Update reply counts for all comments in a video."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        MATCH (c)<-[:PARENT_OF]-(reply:YouTubeComment)
        WITH c, count(reply) as reply_count
        SET c.reply_count = reply_count,
            c.updated_at = datetime()
        RETURN count(*) as updated
        """
        
        result = self.neo4j.execute_write(query, parameters={"video_id": video_id})
        print(f"Updated reply counts for {result[0]['updated']} comments")
