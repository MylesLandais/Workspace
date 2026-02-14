"""Generic imageboard thread parser with HTML parsing, graph checking, and archival."""

import sys
import os
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urlparse, urljoin
import argparse

import requests
from bs4 import BeautifulSoup

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
from feed.utils.image_hash import download_and_hash_image, compute_sha256_hash
from feed.models.post import Post


class ImageboardThreadParser:
    """Parser for imageboard thread HTML pages."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        download_images: bool = True,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize parser.
        
        Args:
            cache_dir: Directory for caching images and HTML (default: ./cache/imageboard)
            download_images: Whether to download and cache images
            user_agent: Custom User-Agent string
        """
        # Use workspace mount for shared access with host
        # Check both workspace (singular) and workspaces (plural) for compatibility
        workspace_cache = Path("/home/jovyan/workspace/cache/imageboard")
        workspaces_cache = Path("/home/jovyan/workspaces/cache/imageboard")
        if workspace_cache.exists() or Path("/home/jovyan/workspace").exists():
            self.cache_dir = cache_dir or workspace_cache
        else:
            self.cache_dir = cache_dir or workspaces_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.cache_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir = self.cache_dir / "html"
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.download_images = download_images
        
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (compatible; imageboard-archiver/1.0)"
        }
    
    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Parse an imageboard thread URL to extract board, thread ID.
        
        Args:
            url: Thread URL (e.g., https://boards.4chan.org/b/thread/943980267)
            
        Returns:
            Dictionary with board and thread_id
        """
        # Pattern: https://boards.4chan.org/{board}/thread/{thread_id}
        pattern = r"boards\.4chan\.org/([^/]+)/thread/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(f"Invalid imageboard thread URL: {url}")
        
        return {
            "board": match.group(1),
            "thread_id": int(match.group(2)),
            "url": url,
        }
    
    def fetch_thread_html(self, url: str) -> Tuple[str, bytes]:
        """
        Fetch thread HTML and return content.
        
        Args:
            url: Thread URL
            
        Returns:
            Tuple of (html_content, raw_bytes)
        """
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text, response.content
    
    def parse_thread_html(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse imageboard thread HTML to extract posts and metadata.
        
        Args:
            html: HTML content
            url: Original URL
            
        Returns:
            Dictionary with thread metadata and posts
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract board and thread ID from URL
        url_info = self.parse_url(url)
        board = url_info["board"]
        thread_id = url_info["thread_id"]
        
        # Find all post containers
        posts = []
        post_containers = soup.find_all("div", class_="postContainer")
        
        if not post_containers:
            # Try alternative selector
            post_containers = soup.find_all("div", class_="post")
        
        for container in post_containers:
            post_data = self._parse_post(container, board, thread_id)
            if post_data:
                posts.append(post_data)
        
        # Extract thread title from first post or page title
        title = ""
        if posts:
            title = posts[0].get("subject", "") or posts[0].get("comment", "")[:100]
        
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()
        
        return {
            "board": board,
            "thread_id": thread_id,
            "url": url,
            "title": title,
            "posts": posts,
            "post_count": len(posts),
            "parsed_at": datetime.utcnow().isoformat(),
        }
    
    def _parse_post(self, container, board: str, thread_id: int) -> Optional[Dict[str, Any]]:
        """Parse a single post container."""
        try:
            # Extract post number
            post_info = container.find("span", class_="postNum")
            if not post_info:
                post_info = container.find("a", class_="postNum")
            
            post_no = None
            if post_info:
                post_no_text = post_info.get_text().strip()
                # Extract number from text like "No.943980267"
                match = re.search(r"(\d+)", post_no_text)
                if match:
                    post_no = int(match.group(1))
            
            if not post_no:
                return None
            
            # Extract subject
            subject = ""
            subject_elem = container.find("span", class_="subject")
            if subject_elem:
                subject = subject_elem.get_text().strip()
            
            # Extract comment
            comment = ""
            comment_elem = container.find("blockquote", class_="postMessage")
            linked_thread_ids = []
            if comment_elem:
                # Extract text (removing HTML tags)
                comment = comment_elem.get_text(separator="\n").strip()
                
                # Extract links to other threads (for "New" thread tracking)
                links = comment_elem.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    link_text = link.get_text().strip().lower()
                    
                    # Check if this is a thread link (for "New" thread tracking)
                    # Pattern: links to /b/thread/THREAD_ID or boards.4chan.org/b/thread/THREAD_ID
                    # Detect all thread links, especially continuation/new threads
                    thread_match = re.search(r'/([^/]+)/thread/(\d+)', href)
                    if thread_match:
                        linked_board = thread_match.group(1)
                        linked_thread_id = int(thread_match.group(2))
                        # Include if it's a different thread (continuation/new thread)
                        # or if link text suggests it's a new thread
                        if linked_thread_id != thread_id:
                            linked_thread_ids.append(linked_thread_id)
            
            # Extract file/image
            image_url = None
            image_filename = None
            file_info = container.find("div", class_="file")
            if file_info:
                file_link = file_info.find("a")
                if file_link:
                    href = file_link.get("href", "")
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith("//"):
                            image_url = "https:" + href
                        elif href.startswith("/"):
                            image_url = f"https://i.4cdn.org{href}"
                        else:
                            image_url = href
                    
                    # Extract filename
                    filename_elem = file_link.find("span", class_="fileText")
                    if filename_elem:
                        image_filename = filename_elem.get_text().strip()
            
            # Extract timestamp
            post_time = None
            time_elem = container.find("span", class_="dateTime")
            if time_elem:
                time_text = time_elem.get_text().strip()
                # Try to parse imageboard date format
                # Format: MM/DD/YY(Day)HH:MM:SS
                # Example: 12/23/25(Tue)11:22:14
                time_match = re.search(
                    r"(\d{2})/(\d{2})/(\d{2})\([^)]+\)(\d{2}):(\d{2}):(\d{2})",
                    time_text
                )
                if time_match:
                    try:
                        month, day, year, hour, minute, second = time_match.groups()
                        # Convert 2-digit year to 4-digit (assuming 2000s)
                        year_int = 2000 + int(year)
                        post_time = datetime(
                            year_int, int(month), int(day),
                            int(hour), int(minute), int(second)
                        )
                    except ValueError:
                        pass
            
            return {
                "post_no": post_no,
                "subject": subject,
                "comment": comment,
                "image_url": image_url,
                "image_filename": image_filename,
                "post_time": post_time.isoformat() if post_time else None,
                "linked_thread_ids": linked_thread_ids,  # Thread IDs this post links to
            }
        except Exception as e:
            print(f"Error parsing post: {e}")
            return None
    
    def cache_html(self, url: str, html_content: bytes) -> Path:
        """
        Cache HTML content to disk.
        
        Args:
            url: Original URL
            html_content: HTML bytes
            
        Returns:
            Path to cached file
        """
        url_info = self.parse_url(url)
        filename = f"{url_info['board']}_{url_info['thread_id']}.html"
        filepath = self.html_dir / filename
        
        filepath.write_bytes(html_content)
        return filepath
    
    def cache_image(self, image_url: str, board: str = None, thread_id: int = None) -> Optional[Tuple[Path, str]]:
        """
        Download and cache an image with organized directory structure.
        
        Args:
            image_url: Image URL
            board: Board name (e.g., 'b') for organization
            thread_id: Thread ID for organization
            
        Returns:
            Tuple of (filepath, sha256_hash) or None on error
        """
        if not self.download_images:
            return None
        
        try:
            # Download image
            response = requests.get(image_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            image_bytes = response.content
            
            # Compute hash
            sha256_hash = compute_sha256_hash(image_bytes)
            
            # Determine file extension from URL or content type
            ext = ".jpg"
            if ".png" in image_url.lower():
                ext = ".png"
            elif ".gif" in image_url.lower():
                ext = ".gif"
            elif ".webm" in image_url.lower():
                ext = ".webm"
            
            # Organize by board/thread for better structure
            # Structure: images/{board}/{thread_id}/{hash}.{ext}
            if board and thread_id:
                thread_dir = self.images_dir / board / str(thread_id)
                thread_dir.mkdir(parents=True, exist_ok=True)
                filepath = thread_dir / f"{sha256_hash}{ext}"
            else:
                # Fallback to flat structure if board/thread not provided
                filepath = self.images_dir / f"{sha256_hash}{ext}"
            
            # Also maintain a hash-indexed flat structure for deduplication
            # Create symlink from flat structure to organized location
            flat_path = self.images_dir / f"{sha256_hash}{ext}"
            
            if not filepath.exists():
                filepath.write_bytes(image_bytes)
            
            # Create symlink in flat directory for easy lookup by hash
            if board and thread_id and not flat_path.exists():
                try:
                    # Calculate relative path from flat_path to filepath
                    rel_path = filepath.relative_to(flat_path.parent)
                    flat_path.symlink_to(rel_path)
                except (OSError, FileExistsError):
                    # Symlink already exists or can't create, that's fine
                    pass
            
            return filepath, sha256_hash
        except Exception as e:
            print(f"Error caching image {image_url}: {e}")
            return None
    
    def check_thread_exists(self, neo4j, board: str, thread_id: int) -> Optional[Dict[str, Any]]:
        """
        Check if thread already exists in graph.
        
        Args:
            neo4j: Neo4j connection
            board: Board name
            thread_id: Thread ID
            
        Returns:
            Existing thread node data or None
        """
        query = """
        MATCH (t:Thread {board: $board, thread_id: $thread_id})
        RETURN t, t.last_crawled_at as last_crawled_at,
               t.post_count as post_count,
               t.content_hash as content_hash
        LIMIT 1
        """
        result = neo4j.execute_read(
            query,
            parameters={"board": board, "thread_id": thread_id}
        )
        
        if result:
            record = result[0]
            thread_data = dict(record["t"])
            return {
                **thread_data,
                "last_crawled_at": record.get("last_crawled_at"),
                "post_count": record.get("post_count"),
                "content_hash": record.get("content_hash"),
            }
        return None
    
    def compute_content_hash(self, thread_data: Dict[str, Any]) -> str:
        """
        Compute content hash for diff checking.
        
        Args:
            thread_data: Parsed thread data
            
        Returns:
            SHA-256 hash of thread content
        """
        # Create a canonical representation for hashing
        # Include post count, post numbers, and image URLs
        content_parts = [
            str(thread_data["post_count"]),
        ]
        
        for post in thread_data.get("posts", []):
            content_parts.append(str(post.get("post_no")))
            if post.get("image_url"):
                content_parts.append(post["image_url"])
        
        content_str = "|".join(content_parts)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def store_thread(
        self,
        neo4j,
        thread_data: Dict[str, Any],
        html_path: Optional[Path] = None,
    ) -> None:
        """
        Store thread in Neo4j graph.
        
        Args:
            neo4j: Neo4j connection
            thread_data: Parsed thread data
            html_path: Path to cached HTML file
        """
        board = thread_data["board"]
        thread_id = thread_data["thread_id"]
        content_hash = self.compute_content_hash(thread_data)
        
        # Check if thread exists
        existing = self.check_thread_exists(neo4j, board, thread_id)
        
        # Determine if content changed
        changed = True
        if existing:
            existing_hash = existing.get("content_hash")
            if existing_hash == content_hash:
                changed = False
        
        # Store thread node
        # Check if thread exists first to handle created_at properly
        existing = self.check_thread_exists(neo4j, board, thread_id)
        is_new = existing is None
        
        query = """
        MERGE (t:Thread {board: $board, thread_id: $thread_id})
        SET t.title = $title,
            t.url = $url,
            t.post_count = $post_count,
            t.content_hash = $content_hash,
            t.html_path = $html_path,
            t.changed = $changed,
            t.last_crawled_at = datetime(),
            t.updated_at = datetime()
        RETURN t
        """
        
        # If new thread, set created_at in a separate query
        if is_new:
            query_create = """
            MATCH (t:Thread {board: $board, thread_id: $thread_id})
            WHERE t.created_at IS NULL
            SET t.created_at = datetime()
            RETURN t
            """
            neo4j.execute_write(
                query_create,
                parameters={"board": board, "thread_id": thread_id}
            )
        
        neo4j.execute_write(
            query,
            parameters={
                "board": board,
                "thread_id": thread_id,
                "title": thread_data.get("title", ""),
                "url": thread_data["url"],
                "post_count": thread_data["post_count"],
                "content_hash": content_hash,
                "html_path": str(html_path) if html_path else None,
                "changed": changed,
            }
        )
        
        # Store posts
        for post_data in thread_data.get("posts", []):
            self._store_post(neo4j, board, thread_id, post_data)
        
        # Store thread relationships (for "New" thread links)
        for post_data in thread_data.get("posts", []):
            linked_thread_ids = post_data.get("linked_thread_ids", [])
            for linked_thread_id in linked_thread_ids:
                self._store_thread_relationship(
                    neo4j, board, thread_id, linked_thread_id
                )
        
        print(f"Stored thread /{board}/{thread_id} (changed: {changed})")
    
    def _store_post(
        self,
        neo4j,
        board: str,
        thread_id: int,
        post_data: Dict[str, Any],
    ) -> None:
        """Store a single post in the graph."""
        post_no = post_data["post_no"]
        post_id = f"{board}_{thread_id}_{post_no}"
        
        # Process image if present
        image_hash = None
        image_path = None
        
        if post_data.get("image_url"):
            cached = self.cache_image(post_data["image_url"], board=board, thread_id=thread_id)
            if cached:
                image_path, image_hash = cached
        
        # Store post - check if post exists first
        check_query = """
        MATCH (p:Post {id: $post_id})
        RETURN p
        LIMIT 1
        """
        existing_post = neo4j.execute_read(
            check_query,
            parameters={"post_id": post_id}
        )
        is_new_post = not existing_post
        
        # Store post
        query = """
        MATCH (t:Thread {board: $board, thread_id: $thread_id})
        MERGE (p:Post {id: $post_id})
        SET p.post_no = $post_no,
            p.subject = $subject,
            p.comment = $comment,
            p.image_url = $image_url,
            p.image_filename = $image_filename,
            p.image_hash = $image_hash,
            p.image_path = $image_path,
            p.post_time = $post_time,
            p.updated_at = datetime()
        MERGE (p)-[:POSTED_IN]->(t)
        """
        
        neo4j.execute_write(
            query,
            parameters={
                "board": board,
                "thread_id": thread_id,
                "post_id": post_id,
                "post_no": post_no,
                "subject": post_data.get("subject", ""),
                "comment": post_data.get("comment", ""),
                "image_url": post_data.get("image_url"),
                "image_filename": post_data.get("image_filename"),
                "image_hash": image_hash,
                "image_path": str(image_path) if image_path else None,
                "post_time": post_data.get("post_time"),
            }
        )
        
        # If new post, set created_at
        if is_new_post:
            query_create = """
            MATCH (p:Post {id: $post_id})
            WHERE p.created_at IS NULL
            SET p.created_at = datetime()
            RETURN p
            """
            neo4j.execute_write(
                query_create,
                parameters={"post_id": post_id}
            )
    
    def _store_thread_relationship(
        self,
        neo4j,
        board: str,
        from_thread_id: int,
        to_thread_id: int,
    ) -> None:
        """
        Store a relationship between threads (for continuation/new threads).
        
        Creates: (:Thread)-[:CONTINUES_TO]->(:Thread)
        """
        # Only create relationship if threads are different
        if from_thread_id == to_thread_id:
            return
        
        query = """
        MATCH (from:Thread {board: $board, thread_id: $from_thread_id})
        MERGE (to:Thread {board: $board, thread_id: $to_thread_id})
        MERGE (from)-[r:CONTINUES_TO]->(to)
        SET r.created_at = CASE WHEN r.created_at IS NULL THEN datetime() ELSE r.created_at END,
            r.updated_at = datetime()
        RETURN r
        """
        
        try:
            neo4j.execute_write(
                query,
                parameters={
                    "board": board,
                    "from_thread_id": from_thread_id,
                    "to_thread_id": to_thread_id,
                }
            )
            print(f"  -> Linked thread /{board}/{from_thread_id} -> /{board}/{to_thread_id}")
        except Exception as e:
            print(f"  -> Warning: Could not create thread relationship: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse imageboard thread HTML and store in graph"
    )
    parser.add_argument(
        "url",
        help="Imageboard thread URL (e.g., https://boards.4chan.org/b/thread/943980267)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/home/jovyan/workspace/cache/imageboard"),
        help="Cache directory for images and HTML (default: ./cache/imageboard)"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't download images"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("IMAGEBOARD THREAD PARSER")
    print("=" * 70)
    print(f"URL: {args.url}")
    print(f"Cache dir: {args.cache_dir}")
    print(f"Download images: {not args.no_images}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    # Initialize parser
    parser_obj = ImageboardThreadParser(
        cache_dir=args.cache_dir,
        download_images=not args.no_images,
    )
    
    # Parse URL
    try:
        url_info = parser_obj.parse_url(args.url)
        print(f"Board: /{url_info['board']}/")
        print(f"Thread ID: {url_info['thread_id']}")
        print()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Connect to Neo4j
    if not args.dry_run:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
        print()
        
        # Check if thread exists
        existing = parser_obj.check_thread_exists(
            neo4j, url_info["board"], url_info["thread_id"]
        )
        if existing:
            print(f"Thread already exists in graph")
            print(f"  Last crawled: {existing.get('last_crawled_at')}")
            print(f"  Post count: {existing.get('post_count')}")
            print(f"  Content hash: {existing.get('content_hash')}")
            print()
    
    # Fetch HTML
    print("Fetching thread HTML...")
    try:
        html_text, html_bytes = parser_obj.fetch_thread_html(args.url)
        print(f"Fetched {len(html_bytes)} bytes")
    except Exception as e:
        print(f"Error fetching HTML: {e}")
        return 1
    
    # Cache HTML
    html_path = parser_obj.cache_html(args.url, html_bytes)
    print(f"Cached HTML to: {html_path}")
    print()
    
    # Parse HTML
    print("Parsing thread HTML...")
    try:
        thread_data = parser_obj.parse_thread_html(html_text, args.url)
        print(f"Parsed {thread_data['post_count']} posts")
        print(f"Title: {thread_data.get('title', 'N/A')[:60]}")
        print()
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Compute content hash
    content_hash = parser_obj.compute_content_hash(thread_data)
    print(f"Content hash: {content_hash}")
    
    if not args.dry_run:
        existing_hash = existing.get("content_hash") if existing else None
        if existing_hash == content_hash:
            print("Content unchanged (no diff)")
        else:
            print("Content changed (diff detected)")
    print()
    
    # Store in graph
    if not args.dry_run:
        print("Storing thread in graph...")
        try:
            parser_obj.store_thread(neo4j, thread_data, html_path)
            print("Done!")
        except Exception as e:
            print(f"Error storing thread: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print("DRY RUN - Would store thread in graph")
        print(f"  Posts: {thread_data['post_count']}")
        print(f"  Images: {sum(1 for p in thread_data['posts'] if p.get('image_url'))}")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Thread: /{thread_data['board']}/{thread_data['thread_id']}")
    print(f"Posts: {thread_data['post_count']}")
    print(f"Images: {sum(1 for p in thread_data['posts'] if p.get('image_url'))}")
    print(f"HTML cached: {html_path}")
    print(f"Content hash: {content_hash}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


