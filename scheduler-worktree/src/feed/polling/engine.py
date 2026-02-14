"""Polling engine for collecting social media posts."""

import os
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from ..platforms.base import PlatformAdapter
from ..models.post import Post
from ..storage.neo4j_connection import Neo4jConnection
from ..utils import is_image_url, hash_image_url, download_and_hash_image
try:
    from image_dedup import ImageDeduplicator, IngestRequest
except (ImportError, ValueError):
    ImageDeduplicator = None
    IngestRequest = None


class PollingEngine:
    """Engine for polling and storing social media posts."""

    def __init__(
        self,
        platform: PlatformAdapter,
        neo4j: Neo4jConnection,
        dry_run: bool = False,
        hash_images: bool = True,
        enable_deduplication: bool = True,
        deduplication_storage_path: Optional[str] = None,
    ):
        """
        Initialize polling engine.
        
        Args:
            platform: Platform adapter instance
            neo4j: Neo4j connection instance
            dry_run: If True, don't write to database
            hash_images: If True, compute image hashes for duplicate detection
            enable_deduplication: If True, use full image deduplication system
            deduplication_storage_path: Path for image storage (default: from env or /tmp)
        """
        self.platform = platform
        self.neo4j = neo4j
        self.dry_run = dry_run
        self.hash_images = hash_images
        self.enable_deduplication = enable_deduplication and not dry_run

        # Initialize deduplicator if enabled
        self.deduplicator = None
        if self.enable_deduplication:
            storage_path = deduplication_storage_path or os.getenv(
                "IMAGE_DEDUP_STORAGE_PATH", "/tmp/image_dedup_storage"
            )
            try:
                if ImageDeduplicator is None:
                    raise ImportError("ImageDeduplicator module not found")
                self.deduplicator = ImageDeduplicator(storage_path=storage_path)
            except Exception as e:
                print(f"Warning: Could not initialize image deduplicator: {e}")
                print("Falling back to basic image hashing")
                self.enable_deduplication = False

    def poll_source(
        self,
        source: str,
        sort: str = "new",
        max_pages: Optional[int] = None,
        limit_per_page: int = 100,
    ) -> List[Post]:
        """
        Poll a source (e.g., subreddit) and collect posts.
        
        Args:
            source: Source identifier (e.g., subreddit name)
            sort: Sort order
            max_pages: Maximum number of pages to fetch (None = all available)
            limit_per_page: Posts per page (max 100)
        
        Returns:
            List of collected posts
        """
        all_posts = []
        after = None
        page = 0
        
        print(f"Starting poll for {source}...")
        if self.dry_run:
            print("DRY RUN MODE - No data will be written to database")
        
        while True:
            if max_pages and page >= max_pages:
                break
            
            page += 1
            print(f"--- Page {page} ---")
            
            posts, next_after = self.platform.fetch_posts(
                source=source,
                sort=sort,
                limit=limit_per_page,
                after=after,
            )
            
            if not posts:
                print("No more posts available")
                break
            
            print(f"Fetched {len(posts)} posts this page (total so far: {len(all_posts) + len(posts)})")
            
            # Deduplicate by checking existing IDs and image hashes
            new_posts = self._deduplicate_posts(posts)
            if new_posts:
                print(f"  -> {len(new_posts)} new posts (after deduplication)")
                if not self.dry_run:
                    self._store_posts(new_posts, source)
                all_posts.extend(new_posts)
            else:
                print("  -> All posts already exist, stopping")
                break
            
            after = next_after
            if not after:
                print("Reached end of available posts")
                break
        
        print(f"\nTotal posts collected: {len(all_posts)}")
        if all_posts:
            date_range = (
                min(p.created_utc for p in all_posts),
                max(p.created_utc for p in all_posts),
            )
            print(f"Date range: {date_range[0]} to {date_range[1]}")
        
        return all_posts

    def _deduplicate_posts(self, posts: List[Post]) -> List[Post]:
        """
        Remove posts that already exist in Neo4j.
        Checks both post IDs and image hashes for duplicates.
        """
        if not posts or self.dry_run:
            return posts
        
        post_ids = [p.id for p in posts]
        
        # Check which posts already exist by ID
        query = """
        MATCH (p:Post)
        WHERE p.id IN $post_ids
        RETURN p.id as id
        """
        existing = self.neo4j.execute_read(
            query,
            parameters={"post_ids": post_ids},
        )
        existing_ids = {record["id"] for record in existing}
        
        new_posts = [p for p in posts if p.id not in existing_ids]
        
        # If image hashing is enabled, also check for duplicate images
        if self.hash_images and new_posts:
            new_posts = self._deduplicate_by_image_hash(new_posts)
        
        return new_posts
    
    def _deduplicate_by_image_hash(self, posts: List[Post]) -> List[Post]:
        """
        Remove posts with duplicate image hashes.
        Only processes image posts.
        """
        image_posts = [p for p in posts if is_image_url(p.url)]
        if not image_posts:
            return posts
        
        # Hash images and check for duplicates
        unique_posts = []
        seen_hashes = set()
        
        for post in image_posts:
            sha256, dhash = hash_image_url(post.url, timeout=5)
            
            if sha256:
                # Check if we've seen this hash in this batch
                if sha256 in seen_hashes:
                    continue
                seen_hashes.add(sha256)
                
                # Check if hash exists in database
                query = """
                MATCH (p:Post {image_hash: $hash})
                RETURN p.id as id
                LIMIT 1
                """
                existing = self.neo4j.execute_read(
                    query,
                    parameters={"hash": sha256},
                )
                if existing:
                    continue
            
            unique_posts.append(post)
        
        # Add non-image posts back
        non_image_posts = [p for p in posts if not is_image_url(p.url)]
        return unique_posts + non_image_posts

    def _store_posts(self, posts: List[Post], source: str) -> None:
        """Store posts in Neo4j."""
        if not posts:
            return
        
        # Create subreddit node if it doesn't exist
        subreddit_query = """
        MERGE (s:Subreddit {name: $name})
        ON CREATE SET s.created_at = datetime()
        RETURN s
        """
        self.neo4j.execute_write(
            subreddit_query,
            parameters={"name": source.replace("r/", "").replace("/r/", "")},
        )
        
        # Create post nodes and relationships
        for post in posts:
            # Convert datetime to Unix timestamp for Neo4j
            created_timestamp = int(post.created_utc.timestamp())
            
            # Process image if this is an image post
            image_hash = None
            image_dhash = None
            dedup_result = None

            if self.hash_images and is_image_url(post.url):
                if self.enable_deduplication and self.deduplicator:
                    # Use full deduplication system
                    try:
                        sha256_hash, dhash, image_bytes = download_and_hash_image(
                            post.url, timeout=10
                        )
                        if image_bytes and sha256_hash and IngestRequest:
                            # Ingest image into deduplication system
                            ingest_request = IngestRequest(
                                image_bytes=image_bytes,
                                post_id=post.id,
                                source="reddit",
                                metadata={
                                    "subreddit": post.subreddit,
                                    "author": post.author,
                                    "title": post.title,
                                    "url": post.url,
                                    "permalink": post.permalink,
                                    "created_at": post.created_utc,
                                    "score": post.score,
                                },
                            )
                            dedup_result = self.deduplicator.ingest_image(
                                ingest_request
                            )
                            image_hash = sha256_hash
                            # Store dhash for backward compatibility
                            if dedup_result.hashes.dhash:
                                image_dhash = dedup_result.hashes.dhash_hex()
                    except Exception as e:
                        print(f"Error in image deduplication for post {post.id}: {e}")
                        # Fallback to basic hashing
                        try:
                            image_hash, image_dhash = hash_image_url(post.url, timeout=5)
                        except Exception:
                            pass
                else:
                    # Use basic image hashing
                    try:
                        image_hash, image_dhash = hash_image_url(post.url, timeout=5)
                    except Exception:
                        pass
            
            post_query = """
            MERGE (p:Post {id: $id})
            SET p.title = $title,
                p.created_utc = datetime({epochSeconds: $created_utc}),
                p.score = $score,
                p.num_comments = $num_comments,
                p.upvote_ratio = $upvote_ratio,
                p.over_18 = $over_18,
                p.url = $url,
                p.selftext = $selftext,
                p.permalink = $permalink,
                p.image_hash = $image_hash,
                p.image_dhash = $image_dhash,
                p.updated_at = datetime()
            WITH p
            MATCH (s:Subreddit {name: $subreddit})
            MERGE (p)-[:POSTED_IN]->(s)
            """
            
            self.neo4j.execute_write(
                post_query,
                parameters={
                    "id": post.id,
                    "title": post.title,
                    "created_utc": created_timestamp,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "upvote_ratio": post.upvote_ratio,
                    "over_18": post.over_18,
                    "url": post.url,
                    "selftext": post.selftext,
                    "permalink": post.permalink,
                    "image_hash": image_hash,
                    "image_dhash": image_dhash,
                    "subreddit": post.subreddit,
                },
            )
            
            # Create user node and relationship if author exists
            if post.author:
                user_query = """
                MERGE (u:User {username: $username})
                ON CREATE SET u.created_at = datetime()
                WITH u
                MATCH (p:Post {id: $post_id})
                MERGE (u)-[:POSTED]->(p)
                """
                self.neo4j.execute_write(
                    user_query,
                    parameters={"username": post.author, "post_id": post.id},
                )

