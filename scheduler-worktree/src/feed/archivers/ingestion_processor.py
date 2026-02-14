"""Ingestion processor - parses imageboard posts and stores in Neo4j graph."""

import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import aiohttp

from ..storage.valkey_connection import get_valkey_connection
from ..storage.neo4j_connection import get_connection
from ..storage.minio_connection import get_minio_connection


class IngestionProcessor:
    """
    Processes imageboard thread data, extracts relationships (quotes/replies),
    and stores in Neo4j graph database.
    """

    def __init__(self, board: str, user_agent: Optional[str] = None):
        """
        Initialize ingestion processor.
        
        Args:
            board: Board name (e.g., "b")
            user_agent: Custom User-Agent string
        """
        self.board = board
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; imageboard-archiver/1.0)"
        
        self.valkey = get_valkey_connection()
        self.neo4j = get_connection()
        self.minio = get_minio_connection()
        
        # Valkey keys
        self.thread_queue_key = f"imageboard:{board}:threads:queue"
        self.processed_threads_key = f"imageboard:{board}:threads:processed"
        
        self.running = False

    def _extract_quotes(self, comment: str) -> List[int]:
        """
        Extract quoted post numbers from comment.
        
        Args:
            comment: Post comment text (may contain HTML)
            
        Returns:
            List of quoted post numbers
        """
        if not comment:
            return []
        
        # Pattern: >>123456
        pattern = r'>>(\d+)'
        matches = re.findall(pattern, comment)
        return [int(m) for m in matches if m.isdigit()]

    def _clean_comment(self, comment: str) -> str:
        """
        Clean HTML from comment text.
        
        Args:
            comment: Raw comment text
            
        Returns:
            Cleaned text
        """
        if not comment:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', comment)
        # Decode HTML entities (basic)
        text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
        return text.strip()

    def _store_thread(self, thread_data: Dict[str, Any]) -> bool:
        """
        Store thread in Neo4j.
        
        Args:
            thread_data: Thread data dictionary
            
        Returns:
            True if successful
        """
        thread_id = thread_data.get("thread_id")
        if not thread_id:
            return False
        
        posts = thread_data.get("posts", [])
        if not posts:
            return False
        
        op_post = posts[0]
        
        # Store thread node
        thread_query = """
        MERGE (t:Thread {board: $board, thread_id: $thread_id})
        SET t.subject = $subject,
            t.post_count = $post_count,
            t.replies = $replies,
            t.images = $images,
            t.created_at = datetime({epochSeconds: $created_at}),
            t.last_updated = datetime(),
            t.archived = $archived
        ON CREATE SET t.created_at = datetime({epochSeconds: $created_at})
        RETURN t
        """
        
        try:
            self.neo4j.execute_write(
                thread_query,
                parameters={
                    "board": self.board,
                    "thread_id": thread_id,
                    "subject": op_post.get("sub", ""),
                    "post_count": len(posts),
                    "replies": thread_data.get("replies", 0),
                    "images": thread_data.get("images", 0),
                    "created_at": op_post.get("time", 0),
                    "archived": thread_data.get("archived", False),
                }
            )
        except Exception as e:
            print(f"Error storing thread: {e}")
            return False
        
        # Store posts and relationships
        for post in posts:
            self._store_post(thread_id, post, posts)
        
        return True

    def _store_post(
        self,
        thread_id: int,
        post: Dict[str, Any],
        all_posts: List[Dict[str, Any]],
    ) -> None:
        """
        Store post and create quote/reply relationships.
        
        Args:
            thread_id: Thread ID
            post: Post data dictionary
            all_posts: All posts in thread (for resolving quotes)
        """
        post_no = post.get("no")
        if not post_no:
            return
        
        post_id = f"{self.board}_{thread_id}_{post_no}"
        comment = self._clean_comment(post.get("com", ""))
        quotes = self._extract_quotes(post.get("com", ""))
        
        # Get media info
        tim = post.get("tim")
        ext = post.get("ext")
        media_url = None
        media_hash = None
        media_bucket = None
        media_object = None
        
        if tim:
            media_url = f"https://i.4cdn.org/{self.board}/{tim}{ext or '.jpg'}"
            
            # Try to find media in MinIO
            try:
                client = self.valkey.client
                hash_index_key = f"imageboard:{self.board}:media:hash_index"
                # We'd need to store hash when downloading, for now just use URL
            except Exception:
                pass
        
        # Store post node
        post_query = """
        MATCH (t:Thread {board: $board, thread_id: $thread_id})
        MERGE (p:Post {id: $post_id})
        SET p.post_no = $post_no,
            p.subject = $subject,
            p.comment = $comment,
            p.media_url = $media_url,
            p.media_hash = $media_hash,
            p.media_bucket = $media_bucket,
            p.media_object = $media_object,
            p.created_at = datetime({epochSeconds: $created_at}),
            p.updated_at = datetime(),
            p.name = $name,
            p.tripcode = $tripcode
        ON CREATE SET p.created_at = datetime({epochSeconds: $created_at})
        MERGE (p)-[:POSTED_IN]->(t)
        RETURN p
        """
        
        try:
            self.neo4j.execute_write(
                post_query,
                parameters={
                    "board": self.board,
                    "thread_id": thread_id,
                    "post_id": post_id,
                    "post_no": post_no,
                    "subject": post.get("sub", ""),
                    "comment": comment,
                    "media_url": media_url,
                    "media_hash": media_hash,
                    "media_bucket": media_bucket,
                    "media_object": media_object,
                    "created_at": post.get("time", 0),
                    "name": post.get("name", ""),
                    "tripcode": post.get("trip", ""),
                }
            )
        except Exception as e:
            print(f"Error storing post {post_no}: {e}")
            return
        
        # Create quote relationships
        for quoted_no in quotes:
            # Find quoted post in thread
            quoted_post = next((p for p in all_posts if p.get("no") == quoted_no), None)
            if quoted_post:
                quoted_post_id = f"{self.board}_{thread_id}_{quoted_no}"
                
                quote_query = """
                MATCH (p:Post {id: $post_id})
                MATCH (q:Post {id: $quoted_post_id})
                MERGE (p)-[r:QUOTES]->(q)
                ON CREATE SET r.created_at = datetime()
                RETURN r
                """
                
                try:
                    self.neo4j.execute_write(
                        quote_query,
                        parameters={
                            "post_id": post_id,
                            "quoted_post_id": quoted_post_id,
                        }
                    )
                except Exception as e:
                    print(f"Error creating quote relationship: {e}")
        
        # Create reply relationship (if not OP)
        if post_no != all_posts[0].get("no"):
            op_post_id = f"{self.board}_{thread_id}_{all_posts[0].get('no')}"
            
            reply_query = """
            MATCH (p:Post {id: $post_id})
            MATCH (op:Post {id: $op_post_id})
            MERGE (p)-[r:REPLIES_TO]->(op)
            ON CREATE SET r.created_at = datetime()
            RETURN r
            """
            
            try:
                self.neo4j.execute_write(
                    reply_query,
                    parameters={
                        "post_id": post_id,
                        "op_post_id": op_post_id,
                    }
                )
            except Exception as e:
                print(f"Error creating reply relationship: {e}")

    async def _process_thread(self, thread_id: int) -> Dict[str, Any]:
        """
        Fetch and process a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Processing results
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing thread {thread_id}...")
        
        thread_url = f"https://a.4cdn.org/{self.board}/thread/{thread_id}.json"
        headers = {"User-Agent": self.user_agent}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(thread_url, headers=headers, timeout=10) as response:
                    if response.status == 404:
                        return {"success": False, "error": "Thread not found (archived)"}
                    
                    response.raise_for_status()
                    thread_json = await response.json()
                    
                    posts = thread_json.get("posts", [])
                    if not posts:
                        return {"success": False, "error": "No posts"}
                    
                    op_post = posts[0]
                    
                    thread_data = {
                        "thread_id": thread_id,
                        "posts": posts,
                        "replies": op_post.get("replies", 0),
                        "images": op_post.get("images", 0),
                        "archived": False,
                    }
                    
                    # Store in Neo4j
                    success = self._store_thread(thread_data)
                    
                    if success:
                        # Mark as processed
                        try:
                            client = self.valkey.client
                            client.sadd(self.processed_threads_key, str(thread_id))
                        except Exception:
                            pass
                        
                        return {
                            "success": True,
                            "thread_id": thread_id,
                            "post_count": len(posts),
                        }
                    else:
                        return {"success": False, "error": "Storage failed"}
                        
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def _worker_loop(self):
        """Worker loop that processes threads from queue."""
        print(f"Ingestion processor worker started for /{self.board}/")
        
        while self.running:
            try:
                client = self.valkey.client
                
                # Pop thread ID from queue
                result = client.brpop(self.thread_queue_key, timeout=5)
                
                if result:
                    # brpop returns (key, value) tuple
                    thread_id = int(result[1])
                    result = await self._process_thread(thread_id)
                    
                    if result.get("success"):
                        print(f"  Stored {result.get('post_count', 0)} posts")
                    else:
                        print(f"  Error: {result.get('error')}")
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Error in worker loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)

    async def run(self, num_workers: int = 2):
        """
        Run ingestion processor with multiple workers.
        
        Args:
            num_workers: Number of parallel workers
        """
        self.running = True
        print("=" * 70)
        print(f"IMAGEBOARD INGESTION PROCESSOR - /{self.board}/")
        print("=" * 70)
        print(f"Workers: {num_workers}")
        print(f"Neo4j: {self.neo4j.uri}")
        print()
        
        workers = [asyncio.create_task(self._worker_loop()) for _ in range(num_workers)]
        
        try:
            await asyncio.gather(*workers)
        except KeyboardInterrupt:
            print("\nShutdown signal received")
            self.running = False
            for worker in workers:
                worker.cancel()

    def stop(self):
        """Stop processor."""
        self.running = False


async def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process imageboard threads into Neo4j")
    parser.add_argument("board", help="Board name (e.g., 'b')")
    parser.add_argument("--workers", type=int, default=2, help="Number of workers")
    
    args = parser.parse_args()
    
    processor = IngestionProcessor(board=args.board)
    
    try:
        await processor.run(num_workers=args.workers)
    except KeyboardInterrupt:
        processor.stop()


if __name__ == "__main__":
    asyncio.run(main())

