"""User moderation and feedback service for imageboard posts."""

from typing import Dict, List, Optional
from enum import Enum
from ..storage.neo4j_connection import get_connection


class ModerationAction(str, Enum):
    """Types of moderation actions."""
    HIDE = "hide"
    UNHIDE = "unhide"
    FLAG = "flag"
    UNFLAG = "unflag"


class ModerationReason(str, Enum):
    """Common moderation reasons."""
    BOT_CONTENT = "bot_content"
    LOW_QUALITY = "low_quality"
    SPAM = "spam"
    OFF_TOPIC = "off_topic"
    DUPLICATE = "duplicate"
    NSFW_MISLABELED = "nsfw_mislabeled"
    HARASSMENT = "harassment"
    CUSTOM = "custom"


class PostModerationService:
    """Service for moderating imageboard posts."""
    
    def __init__(self, neo4j=None):
        self.neo4j = neo4j or get_connection()
    
    def hide_post(
        self,
        post_id: str,
        reason: str,
        flag: Optional[str] = None
    ) -> bool:
        """
        Hide a post with moderation reason.
        
        Args:
            post_id: Post ID (e.g., "b_944358701_944358701")
            reason: Moderation reason
            flag: Optional flag label (e.g., "bot and low-quality noise")
            
        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (p:Post {id: $post_id})
            SET p.hidden = true,
                p.moderation_reason = $reason,
                p.hidden_flag = $flag,
                p.moderated_at = datetime(),
                p.updated_at = datetime()
            RETURN p.id as id
            """
            
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "post_id": post_id,
                    "reason": reason,
                    "flag": flag or reason
                }
            )
            
            return len(result) > 0
        except Exception as e:
            print(f"Error hiding post {post_id}: {e}")
            return False
    
    def unhide_post(self, post_id: str) -> bool:
        """
        Unhide a post (remove hidden status).
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (p:Post {id: $post_id})
            SET p.hidden = false,
                p.moderation_reason = null,
                p.hidden_flag = null,
                p.updated_at = datetime()
            RETURN p.id as id
            """
            
            result = self.neo4j.execute_write(
                query,
                parameters={"post_id": post_id}
            )
            
            return len(result) > 0
        except Exception as e:
            print(f"Error unhiding post {post_id}: {e}")
            return False
    
    def add_user_flag(
        self,
        post_id: str,
        user_id: str,
        flag_type: str
    ) -> bool:
        """
        Add a user flag to a post.
        
        Args:
            post_id: Post ID
            user_id: User ID/identifier
            flag_type: Type of flag (e.g., "bot", "spam", etc.)
            
        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (p:Post {id: $post_id})
            SET p.user_flags = COALESCE(p.user_flags, []) + $flag_info,
                p.updated_at = datetime()
            RETURN p.id as id
            """
            
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "post_id": post_id,
                    "flag_info": {
                        "user_id": user_id,
                        "flag_type": flag_type,
                        "timestamp": "datetime()"
                    }
                }
            )
            
            return len(result) > 0
        except Exception as e:
            print(f"Error adding flag to post {post_id}: {e}")
            return False
    
    def get_hidden_posts(
        self,
        board: Optional[str] = None,
        thread_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get list of hidden posts.
        
        Args:
            board: Optional board filter
            thread_id: Optional thread ID filter
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of hidden post data
        """
        try:
            where_clauses = ["p.hidden = true"]
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if board:
                where_clauses.append("t.board = $board")
                params["board"] = board
            
            if thread_id:
                where_clauses.append("t.thread_id = $thread_id")
                params["thread_id"] = thread_id
            
            where_clause = " AND ".join(where_clauses)
            
            query = f"""
            MATCH (p:Post)-[:POSTED_IN]->(t:Thread)
            WHERE {where_clause}
            RETURN p.id as id,
                   p.post_no as post_no,
                   p.comment as comment,
                   p.moderation_reason as moderation_reason,
                   p.hidden_flag as hidden_flag,
                   p.moderated_at as moderated_at,
                   p.user_flags as user_flags,
                   t.board as board,
                   t.thread_id as thread_id
            ORDER BY p.moderated_at DESC
            SKIP $offset
            LIMIT $limit
            """
            
            result = self.neo4j.execute_read(query, parameters=params)
            return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting hidden posts: {e}")
            return []
    
    def get_post_moderation_history(self, post_id: str) -> Dict:
        """
        Get moderation status for a post.
        
        Args:
            post_id: Post ID
            
        Returns:
            Moderation status dictionary
        """
        try:
            query = """
            MATCH (p:Post {id: $post_id})
            OPTIONAL MATCH (p)-[:POSTED_IN]->(t:Thread)
            RETURN p.hidden as hidden,
                   p.moderation_reason as moderation_reason,
                   p.hidden_flag as hidden_flag,
                   p.moderated_at as moderated_at,
                   p.user_flags as user_flags,
                   t.board as board,
                   t.thread_id as thread_id
            LIMIT 1
            """
            
            result = self.neo4j.execute_read(
                query,
                parameters={"post_id": post_id}
            )
            
            if result:
                return dict(result[0])
            return {}
        except Exception as e:
            print(f"Error getting moderation history: {e}")
            return {}
    
    def mark_thread_posts_as_hidden(
        self,
        board: str,
        thread_id: int,
        post_nos: List[int],
        reason: str,
        flag: Optional[str] = None
    ) -> int:
        """
        Mark multiple posts in a thread as hidden (batch operation).
        
        Args:
            board: Board name (e.g., "b")
            thread_id: Thread ID
            post_nos: List of post numbers to hide
            reason: Moderation reason
            flag: Optional flag label
            
        Returns:
            Number of posts marked as hidden
        """
        try:
            count = 0
            for post_no in post_nos:
                post_id = f"{board}_{thread_id}_{post_no}"
                if self.hide_post(post_id, reason, flag):
                    count += 1
            
            return count
        except Exception as e:
            print(f"Error batch hiding posts: {e}")
            return 0
