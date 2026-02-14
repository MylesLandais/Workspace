#!/usr/bin/env python3
"""
Historical Tumblr Data Importer

Pulls full historical posts from Tumblr sources and adds them to:
1. Source management tables (URL Frontier)
2. Knowledge graph (Neo4j) with full semantic data
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.tumblr import TumblrAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.thread_storage import store_blog_post
from feed.crawler.frontier import URLFrontier


class TumblrHistoricalImporter:
    """Imports historical Tumblr posts to knowledge graph and source management."""

    def __init__(
        self,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        batch_size: int = 50,
    ):
        """
        Initialize importer.

        Args:
            delay_min: Minimum delay between requests
            delay_max: Maximum delay between requests
            batch_size: Number of posts to process per batch
        """
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.batch_size = batch_size

        # Initialize connections
        self.neo4j = get_connection()
        self.frontier = URLFrontier(self.neo4j)
        self.adapter = TumblrAdapter(
            delay_min=delay_min,
            delay_max=delay_max,
        )

        # Track statistics
        self.stats = {
            'total_posts': 0,
            'total_images': 0,
            'total_tags': 0,
            'sources_added': 0,
            'sources_existing': 0,
            'posts_stored': 0,
            'posts_skipped': 0,
            'errors': [],
        }

    def add_source_to_management(self, blog_url: str, priority: float = 1.0) -> bool:
        """
        Add Tumblr blog to URL Frontier for ongoing crawling.

        Args:
            blog_url: Tumblr blog URL
            priority: Priority for crawling

        Returns:
            True if source was added, False if already exists
        """
        print(f"\n📋 Adding source to management: {blog_url}")

        # Add to URL frontier
        added = self.frontier.add_url(blog_url, priority=priority)

        if added:
            print(f"   ✓ Source added to crawl queue")
            self.stats['sources_added'] += 1
        else:
            print(f"   ℹ Source already exists in queue")
            self.stats['sources_existing'] += 1

        return added

    def fetch_historical_posts(
        self,
        blog_url: str,
        limit: int = 1000,
        creator_slug: Optional[str] = None,
    ) -> List[Any]:
        """
        Fetch historical posts from Tumblr blog.

        Args:
            blog_url: Tumblr blog URL
            limit: Maximum posts to fetch (Tumblr RSS returns ~20-50 per call)
            creator_slug: Optional creator slug to link posts to

        Returns:
            List of Post objects
        """
        print(f"\n📥 Fetching historical posts from: {blog_url}")
        print(f"   Limit: {limit} posts")

        try:
            # Fetch posts with full content scraping
            posts, _ = self.adapter.fetch_posts(
                source=blog_url,
                limit=limit,
                scrape_content=True,
            )

            print(f"   ✓ Fetched {len(posts)} posts")

            # Store creator slug in post metadata for linking
            if creator_slug:
                for post in posts:
                    metadata = self.adapter.get_post_metadata(post.id)
                    if metadata is None:
                        metadata = {}
                    metadata['creator_slug'] = creator_slug
                    self.adapter._post_metadata[post.id] = metadata

            self.stats['total_posts'] += len(posts)
            return posts

        except Exception as e:
            error_msg = f"Error fetching posts from {blog_url}: {e}"
            print(f"   ✗ {error_msg}")
            self.stats['errors'].append(error_msg)
            return []

    def import_posts_to_graph(
        self,
        posts: List[Any],
        creator_slug: Optional[str] = None,
    ) -> None:
        """
        Import posts to Neo4j knowledge graph.

        Args:
            posts: List of Post objects
            creator_slug: Optional creator slug to link posts to
        """
        print(f"\n💾 Importing {len(posts)} posts to Neo4j...")

        for idx, post in enumerate(posts, 1):
            try:
                # Get extended metadata
                metadata = self.adapter.get_post_metadata(post.id) or {}

                images = metadata.get('images', [])
                tags = metadata.get('tags', [])

                # Store post with images
                store_blog_post(
                    neo4j=self.neo4j,
                    post=post,
                    images=images,
                    creator_slug=creator_slug,
                )

                # Store tags separately
                for tag in tags:
                    self._store_tag(post.id, tag)

                # Update statistics
                self.stats['posts_stored'] += 1
                self.stats['total_images'] += len(images)
                self.stats['total_tags'] += len(tags)

                # Progress
                if idx % 10 == 0:
                    print(f"   Progress: {idx}/{len(posts)} posts stored")

            except Exception as e:
                error_msg = f"Error storing post {post.id}: {e}"
                print(f"   ✗ {error_msg}")
                self.stats['errors'].append(error_msg)
                self.stats['posts_skipped'] += 1

        print(f"   ✓ Completed: {self.stats['posts_stored']} posts stored")

    def _store_tag(self, post_id: str, tag: str) -> None:
        """
        Store tag and link to post.

        Args:
            post_id: Post ID
            tag: Tag name
        """
        # Create tag node
        tag_query = """
        MERGE (t:Tag {name: $tag})
        ON CREATE SET t.created_at = datetime()
        WITH t
        MATCH (p:Post {id: $post_id})
        MERGE (p)-[r:HAS_TAG]->(t)
        ON CREATE SET r.created_at = datetime()
        RETURN r
        """

        self.neo4j.execute_write(
            tag_query,
            parameters={
                "tag": tag,
                "post_id": post_id,
            }
        )

    def import_source(
        self,
        blog_url: str,
        limit: int = 1000,
        creator_slug: Optional[str] = None,
        priority: float = 1.0,
    ) -> None:
        """
        Complete import workflow for a single Tumblr source.

        Args:
            blog_url: Tumblr blog URL
            limit: Maximum posts to fetch
            creator_slug: Optional creator slug
            priority: Priority for crawl queue
        """
        print(f"\n" + "=" * 70)
        print(f"🎯 Importing Source: {blog_url}")
        print("=" * 70)

        # Step 1: Add to source management
        self.add_source_to_management(blog_url, priority)

        # Step 2: Fetch historical posts
        posts = self.fetch_historical_posts(blog_url, limit, creator_slug)

        if not posts:
            print(f"\n⚠ No posts found, skipping import")
            return

        # Step 3: Import to knowledge graph
        self.import_posts_to_graph(posts, creator_slug)

        # Summary for this source
        print(f"\n📊 Source Import Summary:")
        print(f"   Posts fetched: {len(posts)}")
        print(f"   Posts stored: {self.stats['posts_stored'] - self.stats['posts_stored'] + len([p for p in posts if True])}")
        print(f"   Images extracted: {sum([len(self.adapter.get_post_metadata(p.id).get('images', [])) for p in posts])}")

    def print_final_summary(self) -> None:
        """Print final import statistics."""
        print("\n" + "=" * 70)
        print("📊 FINAL IMPORT SUMMARY")
        print("=" * 70)

        print(f"\n📋 Source Management:")
        print(f"   Sources added: {self.stats['sources_added']}")
        print(f"   Sources already exists: {self.stats['sources_existing']}")

        print(f"\n📥 Data Fetched:")
        print(f"   Total posts fetched: {self.stats['total_posts']}")
        print(f"   Total images extracted: {self.stats['total_images']}")
        print(f"   Total tags extracted: {self.stats['total_tags']}")

        print(f"\n💾 Data Stored:")
        print(f"   Posts stored to graph: {self.stats['posts_stored']}")
        print(f"   Posts skipped (errors): {self.stats['posts_skipped']}")

        print(f"\n❌ Errors:")
        if self.stats['errors']:
            print(f"   Total errors: {len(self.stats['errors'])}")
            for i, error in enumerate(self.stats['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more")
        else:
            print(f"   No errors!")

        print("\n" + "=" * 70)


def main():
    """Main execution with predefined Tumblr sources."""

    # Define sources to import
    sources = [
        {
            'url': 'https://blackswandive.tumblr.com',
            'limit': 1000,
            'priority': 1.0,
            'creator_slug': None,  # Add if you have creator entities
        },
        {
            'url': 'https://barbie-expectations.tumblr.com',
            'limit': 1000,
            'priority': 1.0,
            'creator_slug': None,
        },
    ]

    # Initialize importer
    importer = TumblrHistoricalImporter(
        delay_min=2.0,
        delay_max=5.0,
    )

    print("🚀 TUMBLR HISTORICAL DATA IMPORTER")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"   Delay: {importer.delay_min}-{importer.delay_max}s between requests")
    print(f"   Sources to import: {len(sources)}")

    # Import each source
    for source in sources:
        importer.import_source(
            blog_url=source['url'],
            limit=source['limit'],
            creator_slug=source['creator_slug'],
            priority=source['priority'],
        )

    # Print final summary
    importer.print_final_summary()

    # Check Neo4j stats
    print(f"\n📊 Neo4j Statistics:")

    # Count posts
    count_query = """
    MATCH (p:Post) RETURN count(p) as post_count
    """
    result = importer.neo4j.execute_read(count_query)
    if result:
        print(f"   Total posts in graph: {result[0]['post_count']}")

    # Count images
    image_query = """
    MATCH (p:Post)-[:HAS_IMAGE]->(i:Image) RETURN count(i) as image_count
    """
    result = importer.neo4j.execute_read(image_query)
    if result:
        print(f"   Total images in graph: {result[0]['image_count']}")

    # Count tags
    tag_query = """
    MATCH (p:Post)-[:HAS_TAG]->(t:Tag) RETURN count(t) as tag_count
    """
    result = importer.neo4j.execute_read(tag_query)
    if result:
        print(f"   Total tags in graph: {result[0]['tag_count']}")

    print("\n✅ Import complete!")
    print("\nNext steps:")
    print("  1. Verify data in Neo4j: MATCH (p:Post) RETURN p LIMIT 10")
    print("  2. Start crawler: Crawler will pick up sources from frontier")
    print("  3. Query semantic layer: MATCH (p:Post)-[:HAS_TAG]->(t:Tag) RETURN p, t")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
