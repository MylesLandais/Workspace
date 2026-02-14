"""Offline storage for local caching."""

import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json

from feed.models.post import Post


class OfflineStorage:
    """SQLite-based offline storage for posts."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                score INTEGER,
                num_comments INTEGER,
                upvote_ratio REAL,
                over_18 BOOLEAN,
                selftext TEXT,
                author TEXT,
                subreddit TEXT,
                created_utc TEXT,
                synced BOOLEAN DEFAULT FALSE,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_subreddit 
            ON posts(subreddit)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_author 
            ON posts(author)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_synced 
            ON posts(synced)
        """)
        conn.commit()
        conn.close()
    
    def save_offline(self, post: Post) -> None:
        """Save post for offline access."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO posts 
            (id, title, url, score, num_comments, upvote_ratio, over_18,
             selftext, author, subreddit, created_utc, synced, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE, ?)
            """,
            (
                post.id,
                post.title,
                post.url,
                post.score,
                post.num_comments,
                post.upvote_ratio,
                post.over_18,
                post.selftext,
                post.author,
                post.subreddit,
                post.created_utc.isoformat() if post.created_utc else None,
                datetime.now().isoformat()
            )
        )
        conn.commit()
        conn.close()
    
    def get_offline(self, post_id: str) -> Optional[Post]:
        """Get post from offline storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM posts WHERE id = ?",
            (post_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_post(row)
    
    def get_unsynced(self, limit: int = 100) -> List[Post]:
        """Get posts that haven't been synced to server."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM posts WHERE synced = FALSE LIMIT ?",
            (limit,)
        )
        posts = [self._row_to_post(row) for row in cursor.fetchall()]
        conn.close()
        return posts
    
    def mark_synced(self, post_id: str) -> None:
        """Mark post as synced."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE posts SET synced = TRUE WHERE id = ?",
            (post_id,)
        )
        conn.commit()
        conn.close()
    
    def get_by_subreddit(
        self,
        subreddit: str,
        limit: int = 100,
        synced_only: bool = False
    ) -> List[Post]:
        """Get posts by subreddit from offline storage."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM posts 
            WHERE subreddit = ?
        """
        params = [subreddit]
        
        if synced_only:
            query += " AND synced = TRUE"
        
        query += " ORDER BY cached_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        posts = [self._row_to_post(row) for row in cursor.fetchall()]
        conn.close()
        return posts
    
    def purge_old(self, days: int = 30) -> int:
        """Remove posts older than specified days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            DELETE FROM posts 
            WHERE cached_at < datetime('now', ?) 
            AND synced = TRUE
            """,
            (f'-{days} days',)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    
    def get_stats(self) -> dict:
        """Get offline storage statistics."""
        conn = sqlite3.connect(self.db_path)
        
        total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        synced = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE synced = TRUE"
        ).fetchone()[0]
        unsynced = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE synced = FALSE"
        ).fetchone()[0]
        
        size = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        conn.close()
        
        return {
            "total_posts": total,
            "synced_posts": synced,
            "unsynced_posts": unsynced,
            "storage_size_bytes": size
        }
    
    def _row_to_post(self, row: tuple) -> Post:
        """Convert database row to Post object."""
        return Post(
            id=row[0],
            title=row[1],
            url=row[2],
            score=row[3],
            num_comments=row[4],
            upvote_ratio=row[5],
            over_18=bool(row[6]),
            selftext=row[7],
            author=row[8],
            subreddit=row[9],
            created_utc=datetime.fromisoformat(row[10]) if row[10] else None
        )
