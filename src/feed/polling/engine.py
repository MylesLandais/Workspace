"""Polling engine for collecting social media posts."""

from typing import List, Optional
from datetime import datetime

from ..platforms.base import PlatformAdapter
from ..models.post import Post
from ..storage.neo4j_connection import Neo4jConnection


class PollingEngine:
    """Engine for polling and storing social media posts."""

    def __init__(
        self,
        platform: PlatformAdapter,
        neo4j: Neo4jConnection,
        dry_run: bool = False,
    ):
        """
        Initialize polling engine.
        
        Args:
            platform: Platform adapter instance
            neo4j: Neo4j connection instance
            dry_run: If True, don't write to database
        """
        self.platform = platform
        self.neo4j = neo4j
        self.dry_run = dry_run

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
            
            # Deduplicate by checking existing IDs
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
        """Remove posts that already exist in Neo4j."""
        if not posts or self.dry_run:
            return posts
        
        post_ids = [p.id for p in posts]
        
        # Check which posts already exist
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
        return new_posts

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

