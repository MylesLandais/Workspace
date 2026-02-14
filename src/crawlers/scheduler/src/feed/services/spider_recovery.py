"""Spider recovery utilities for handling missed images.

This module provides tools to:
1. Check if images were missed due to spider downtime
2. Recover and ingest missed images
3. Verify spider ingestion status
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from ..storage.neo4j_connection import Neo4jConnection
from .reverse_image_search import ReverseImageSearch
from ..platforms.reddit import RedditAdapter
from ..storage.thread_storage import store_thread
from ..utils.reddit_url_extractor import extract_post_id_from_url, parse_reddit_url


class SpiderRecovery:
    """Utilities for recovering images missed by spider downtime."""

    def __init__(
        self,
        neo4j: Neo4jConnection,
        reverse_search: Optional[ReverseImageSearch] = None
    ):
        """
        Initialize spider recovery service.
        
        Args:
            neo4j: Neo4j connection
            reverse_search: Optional ReverseImageSearch instance (will create if None)
        """
        self.neo4j = neo4j
        self.reverse_search = reverse_search or ReverseImageSearch(neo4j=neo4j)
        self.reddit = RedditAdapter()

    def check_image_status(
        self,
        image_url: str,
        use_vector_search: bool = True
    ) -> Dict[str, any]:
        """
        Check if an image exists in the database and provide recovery options.
        
        Args:
            image_url: Image URL to check
            use_vector_search: If True, also try vector similarity search
            
        Returns:
            Dictionary with status and recovery information
        """
        result = {
            "image_url": image_url,
            "found": False,
            "match_type": None,
            "matches": [],
            "recovery_needed": False,
            "similar_images": [],
        }

        # Check if image exists
        lookup_result = self.reverse_search.check_if_crawled(image_url)
        
        if lookup_result.found:
            result["found"] = True
            result["matches"] = [
                {
                    "type": m.match_type,
                    "confidence": m.confidence,
                    "source_post_id": m.source_post_id,
                    "source_comment_id": m.source_comment_id,
                    "source_product_id": m.source_product_id,
                }
                for m in lookup_result.matches
            ]
            result["match_type"] = lookup_result.matches[0].match_type
        else:
            result["recovery_needed"] = True
            
            # Try vector search to find similar images
            if use_vector_search and self.reverse_search.enable_vector_search:
                vector_result = self.reverse_search.find_exact_matches(image_url)
                similar = [
                    m for m in vector_result.matches
                    if m.match_type == "vector" and m.confidence >= 0.85
                ]
                if similar:
                    result["similar_images"] = [
                        {
                            "url": m.image_url,
                            "similarity": m.confidence,
                            "source_post_id": m.source_post_id,
                        }
                        for m in similar
                    ]

        return result

    def recover_post(
        self,
        post_url: str,
        index_images: bool = True
    ) -> Dict[str, any]:
        """
        Recover a missed Reddit post and ingest it into the database.
        
        Args:
            post_url: Reddit post URL
            index_images: If True, index images for future search
            
        Returns:
            Dictionary with recovery status and results
        """
        result = {
            "post_url": post_url,
            "success": False,
            "post_id": None,
            "images_found": 0,
            "images_indexed": 0,
            "error": None,
        }

        # Extract post ID
        post_id = extract_post_id_from_url(post_url)
        
        # Check if post already exists
        check_query = """
        MATCH (p:Post {id: $post_id})
        RETURN p.id as id, p.title as title, p.created_utc as created_utc
        LIMIT 1
        """
        existing = self.neo4j.execute_read(
            check_query,
            parameters={"post_id": post_id}
        )

        if existing:
            result["success"] = True
            result["post_id"] = post_id
            result["error"] = "Post already exists in database"
            return result

        # Fetch the post
        try:
            parsed = parse_reddit_url(post_url)
            if not parsed or not parsed.get('permalink'):
                result["error"] = "Could not extract permalink from URL"
                return result

            permalink = parsed['permalink']
            post, comments, raw_post_data = self.reddit.fetch_thread(permalink)

            if not post:
                result["error"] = "Failed to fetch post from Reddit"
                return result

            # Extract images
            images = []
            post_images = self.reddit.extract_all_images(post, raw_post_data)
            for img_url in post_images:
                images.append({
                    "url": img_url,
                    "source": "post",
                    "post_id": post.id,
                })

            # Store in Neo4j
            store_thread(self.neo4j, post, comments, images, raw_post_data)
            result["success"] = True
            result["post_id"] = post.id
            result["images_found"] = len(post_images)

            # Index images
            if index_images:
                indexed = 0
                for img_url in post_images:
                    if self.reverse_search.index_image(img_url):
                        indexed += 1
                result["images_indexed"] = indexed

        except Exception as e:
            result["error"] = str(e)

        return result

    def batch_recover_posts(
        self,
        post_urls: List[str],
        index_images: bool = True
    ) -> Dict[str, any]:
        """
        Recover multiple missed posts in batch.
        
        Args:
            post_urls: List of Reddit post URLs
            index_images: If True, index images for future search
            
        Returns:
            Dictionary with batch recovery results
        """
        results = {
            "total": len(post_urls),
            "successful": 0,
            "failed": 0,
            "already_existed": 0,
            "posts": [],
        }

        for post_url in post_urls:
            recovery_result = self.recover_post(post_url, index_images=index_images)
            results["posts"].append(recovery_result)

            if recovery_result["success"]:
                if recovery_result.get("error") == "Post already exists in database":
                    results["already_existed"] += 1
                else:
                    results["successful"] += 1
            else:
                results["failed"] += 1

        return results

    def check_spider_gaps(
        self,
        subreddit: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, any]:
        """
        Check for potential gaps in spider coverage for a subreddit.
        
        Args:
            subreddit: Subreddit name
            start_time: Start of time period to check
            end_time: End of time period to check
            
        Returns:
            Dictionary with gap analysis
        """
        # Query posts in time range
        query = """
        MATCH (p:Post)
        WHERE p.subreddit = $subreddit
          AND p.created_utc >= datetime({epochSeconds: $start_epoch})
          AND p.created_utc <= datetime({epochSeconds: $end_epoch})
        RETURN p.id as id, p.title as title, p.created_utc as created_utc
        ORDER BY p.created_utc ASC
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={
                "subreddit": subreddit,
                "start_epoch": int(start_time.timestamp()),
                "end_epoch": int(end_time.timestamp()),
            }
        )

        posts = [dict(record) for record in result]
        
        # Analyze gaps (simplified - would need more sophisticated analysis)
        gaps = []
        if len(posts) > 1:
            for i in range(len(posts) - 1):
                current_time = posts[i]["created_utc"]
                next_time = posts[i + 1]["created_utc"]
                # If gap is more than 1 hour, might indicate spider downtime
                if isinstance(current_time, datetime) and isinstance(next_time, datetime):
                    gap = (next_time - current_time).total_seconds()
                    if gap > 3600:  # 1 hour
                        gaps.append({
                            "start": current_time,
                            "end": next_time,
                            "duration_seconds": gap,
                        })

        return {
            "subreddit": subreddit,
            "start_time": start_time,
            "end_time": end_time,
            "posts_found": len(posts),
            "potential_gaps": gaps,
        }

    def find_missing_images_in_post(
        self,
        post_id: str
    ) -> Dict[str, any]:
        """
        Check if a post's images are properly indexed.
        
        Args:
            post_id: Reddit post ID
            
        Returns:
            Dictionary with indexing status
        """
        # Get post images
        query = """
        MATCH (p:Post {id: $post_id})-[:HAS_IMAGE]->(img:Image)
        RETURN img.url as url, img.sha256_hash as sha256, img.dhash as dhash
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"post_id": post_id}
        )

        images = [dict(record) for record in result]
        
        indexed = 0
        missing_hashes = []
        missing_embeddings = []

        for img in images:
            url = img["url"]
            has_hash = bool(img.get("sha256"))
            
            if has_hash:
                indexed += 1
            else:
                missing_hashes.append(url)
            
            # Check if embedding exists in Valkey (if vector search enabled)
            if self.reverse_search.enable_vector_search and self.reverse_search.valkey:
                key = f"{self.reverse_search.DOC_PREFIX}{url}"
                if not self.reverse_search.valkey.exists(key):
                    missing_embeddings.append(url)

        return {
            "post_id": post_id,
            "total_images": len(images),
            "indexed_images": indexed,
            "missing_hashes": missing_hashes,
            "missing_embeddings": missing_embeddings,
        }




