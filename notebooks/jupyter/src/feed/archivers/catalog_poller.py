"""Catalog poller service for imageboard boards - continuously monitors board catalogs."""

import asyncio
import time
import random
import json
from datetime import datetime
from typing import Dict, Set, Optional, List, Any
import aiohttp
import re

from ..storage.valkey_connection import get_valkey_connection
from ..storage.neo4j_connection import get_connection


class CatalogPoller:
    """
    Polls imageboard board catalogs continuously, tracks new/live threads,
    and publishes events via Valkey pubsub.
    """

    def __init__(
        self,
        board: str,
        poll_interval: int = 45,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize catalog poller.
        
        Args:
            board: Board name (e.g., "b")
            poll_interval: Seconds between catalog polls (default: 45)
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            user_agent: Custom User-Agent string
        """
        self.board = board
        self.poll_interval = poll_interval
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; imageboard-archiver/1.0)"
        
        self.base_url = "https://a.4cdn.org"
        self.catalog_url = f"{self.base_url}/{board}/catalog.json"
        
        self.valkey = get_valkey_connection()
        self.neo4j = get_connection()
        
        # Track known thread IDs
        self.known_threads: Set[int] = set()
        self.running = False
        
        # Valkey keys
        self.thread_queue_key = f"imageboard:{board}:threads:queue"
        self.seen_threads_key = f"imageboard:{board}:threads:seen"
        self.pubsub_channel = f"imageboard:{board}:events"

    async def _fetch_catalog(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """
        Fetch catalog JSON from imageboard API.
        
        Args:
            session: aiohttp session
            
        Returns:
            List of thread dictionaries
        """
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with session.get(self.catalog_url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                catalog = await response.json()
                
                # Catalog is a list of pages, each containing threads
                all_threads = []
                for page in catalog:
                    threads = page.get("threads", [])
                    all_threads.extend(threads)
                
                return all_threads
        except Exception as e:
            print(f"Error fetching catalog: {e}")
            return []

    def _extract_quotes(self, comment: str) -> List[int]:
        """
        Extract quoted post numbers from comment text.
        
        Args:
            comment: Post comment text (may contain HTML)
            
        Returns:
            List of quoted post numbers
        """
        if not comment:
            return []
        
        # Pattern: >>123456 or >>123456789
        pattern = r'>>(\d+)'
        matches = re.findall(pattern, comment)
        return [int(m) for m in matches if m.isdigit()]

    async def _process_thread(
        self,
        thread_data: Dict[str, Any],
        session: aiohttp.ClientSession,
    ) -> Dict[str, Any]:
        """
        Process a thread: fetch full data, extract metadata.
        
        Args:
            thread_data: Thread data from catalog
            session: aiohttp session
            
        Returns:
            Enriched thread data
        """
        thread_id = thread_data.get("no")
        if not thread_id:
            return {}
        
        # Fetch full thread JSON
        thread_url = f"{self.base_url}/{self.board}/thread/{thread_id}.json"
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with session.get(thread_url, headers=headers, timeout=10) as response:
                if response.status == 404:
                    # Thread archived or deleted
                    return {"thread_id": thread_id, "archived": True}
                
                response.raise_for_status()
                thread_json = await response.json()
                
                posts = thread_json.get("posts", [])
                if not posts:
                    return {"thread_id": thread_id, "archived": True}
                
                op_post = posts[0]
                
                # Extract quotes from all posts
                all_quotes = []
                for post in posts:
                    comment = post.get("com", "")
                    quotes = self._extract_quotes(comment)
                    all_quotes.extend(quotes)
                
                return {
                    "thread_id": thread_id,
                    "archived": False,
                    "post_count": len(posts),
                    "replies": thread_data.get("replies", 0),
                    "images": thread_data.get("images", 0),
                    "subject": op_post.get("sub", ""),
                    "timestamp": op_post.get("time", 0),
                    "quotes": list(set(all_quotes)),  # Unique quotes
                }
        except Exception as e:
            print(f"Error processing thread {thread_id}: {e}")
            return {"thread_id": thread_id, "error": str(e)}

    async def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish event to Valkey pubsub.
        
        Args:
            event_type: Event type (e.g., "new_thread", "thread_updated", "thread_archived")
            data: Event data
        """
        try:
            client = self.valkey.client
            event = {
                "type": event_type,
                "board": self.board,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            client.publish(self.pubsub_channel, json.dumps(event))
        except Exception as e:
            print(f"Error publishing event: {e}")

    async def _queue_thread(self, thread_id: int) -> None:
        """
        Add thread ID to processing queue.
        
        Args:
            thread_id: Thread ID
        """
        try:
            client = self.valkey.client
            # Add to queue (list)
            client.lpush(self.thread_queue_key, str(thread_id))
            # Mark as seen
            client.sadd(self.seen_threads_key, str(thread_id))
        except Exception as e:
            print(f"Error queueing thread {thread_id}: {e}")

    async def poll_once(self) -> Dict[str, Any]:
        """
        Perform a single catalog poll.
        
        Returns:
            Poll results dictionary
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling /{self.board}/ catalog...")
        
        async with aiohttp.ClientSession() as session:
            # Fetch catalog
            threads = await self._fetch_catalog(session)
            
            if not threads:
                return {"success": False, "error": "No threads found"}
            
            # Get current thread IDs from catalog
            current_thread_ids = {t.get("no") for t in threads if t.get("no")}
            
            # Load known threads from Valkey
            try:
                client = self.valkey.client
                seen_threads = client.smembers(self.seen_threads_key)
                known_thread_ids = {int(tid) for tid in seen_threads if tid.isdigit()}
            except Exception:
                known_thread_ids = set()
            
            # Find new threads
            new_thread_ids = current_thread_ids - known_thread_ids
            archived_thread_ids = known_thread_ids - current_thread_ids
            
            print(f"  Found {len(current_thread_ids)} active threads")
            print(f"  New threads: {len(new_thread_ids)}")
            print(f"  Archived threads: {len(archived_thread_ids)}")
            
            # Process new threads
            new_threads = []
            for thread_id in new_thread_ids:
                thread_data = next((t for t in threads if t.get("no") == thread_id), None)
                if thread_data:
                    # Add delay between thread fetches
                    await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))
                    
                    enriched = await self._process_thread(thread_data, session)
                    if enriched and not enriched.get("archived"):
                        new_threads.append(enriched)
                        await self._queue_thread(thread_id)
                        await self._publish_event("new_thread", enriched)
            
            # Mark archived threads
            for thread_id in archived_thread_ids:
                await self._publish_event("thread_archived", {"thread_id": thread_id})
            
            # Update known threads
            self.known_threads = current_thread_ids
            
            return {
                "success": True,
                "active_threads": len(current_thread_ids),
                "new_threads": len(new_thread_ids),
                "archived_threads": len(archived_thread_ids),
                "processed": len(new_threads),
            }

    async def run(self):
        """Run continuous polling loop."""
        self.running = True
        print("=" * 70)
        print(f"IMAGEBOARD CATALOG POLLER - /{self.board}/")
        print("=" * 70)
        print(f"Poll interval: {self.poll_interval} seconds")
        print(f"Valkey: {self.valkey.host}:{self.valkey.port}")
        print(f"Neo4j: {self.neo4j.uri}")
        print()
        
        poll_count = 0
        
        while self.running:
            try:
                result = await self.poll_once()
                poll_count += 1
                
                if result.get("success"):
                    print(f"  Poll #{poll_count} complete")
                else:
                    print(f"  Poll #{poll_count} failed: {result.get('error')}")
                
                # Wait for next poll
                if self.running:
                    await asyncio.sleep(self.poll_interval)
                    
            except KeyboardInterrupt:
                print("\nShutdown signal received")
                break
            except Exception as e:
                print(f"Error in polling loop: {e}")
                import traceback
                traceback.print_exc()
                # Continue polling even on error
                await asyncio.sleep(self.poll_interval)
        
        print("\n" + "=" * 70)
        print("POLLING STOPPED")
        print("=" * 70)
        print(f"Total polls: {poll_count}")

    def stop(self):
        """Stop polling loop."""
        self.running = False


async def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Poll imageboard board catalog continuously")
    parser.add_argument("board", help="Board name (e.g., 'b')")
    parser.add_argument("--interval", type=int, default=45, help="Poll interval in seconds")
    
    args = parser.parse_args()
    
    poller = CatalogPoller(board=args.board, poll_interval=args.interval)
    
    try:
        await poller.run()
    except KeyboardInterrupt:
        poller.stop()


if __name__ == "__main__":
    asyncio.run(main())

