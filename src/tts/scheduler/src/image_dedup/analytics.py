"""Analytics functions for image deduplication system."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from feed.storage.neo4j_connection import get_connection


class ImageAnalytics:
    """Analytics functions for repost statistics and cluster analysis."""

    def __init__(self):
        """Initialize analytics handler."""
        self.neo4j = get_connection()

    def get_most_reposted_images(
        self, limit: int = 50, min_reposts: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get most reposted images by cluster repost count.

        Args:
            limit: Maximum number of results
            min_reposts: Minimum repost count to include

        Returns:
            List of cluster records with repost statistics
        """
        query = """
        MATCH (c:ImageCluster)
        WHERE c.repost_count >= $min_reposts
        OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:ImageFile)
        OPTIONAL MATCH (canonical)-[:APPEARED_IN]->(first_post:Post)
        WITH c, canonical, first_post,
             min((canonical)-[:APPEARED_IN]->(p:Post) | p.created_at) as first_seen_post
        RETURN c.id as cluster_id,
               c.canonical_sha256 as canonical_sha256,
               c.repost_count as repost_count,
               c.first_seen as first_seen,
               c.last_seen as last_seen,
               canonical.id as canonical_image_id,
               canonical.storage_path as canonical_storage_path,
               canonical.width as width,
               canonical.height as height,
               first_post.id as first_post_id,
               first_post.subreddit as first_subreddit,
               first_post.title as first_title,
               first_seen_post
        ORDER BY c.repost_count DESC
        LIMIT $limit
        """

        result = self.neo4j.execute_read(
            query,
            parameters={"limit": limit, "min_reposts": min_reposts},
        )

        results = []
        for record in result:
            results.append({
                "cluster_id": record.get("cluster_id"),
                "canonical_sha256": record.get("canonical_sha256"),
                "repost_count": record.get("repost_count", 0),
                "first_seen": record.get("first_seen"),
                "last_seen": record.get("last_seen"),
                "canonical_image_id": record.get("canonical_image_id"),
                "canonical_storage_path": record.get("canonical_storage_path"),
                "width": record.get("width"),
                "height": record.get("height"),
                "first_post_id": record.get("first_post_id"),
                "first_subreddit": record.get("first_subreddit"),
                "first_title": record.get("first_title"),
                "first_seen_post": record.get("first_seen_post"),
            })

        return results

    def get_daily_statistics(
        self, date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get daily statistics for image ingestion and duplicate detection.

        Args:
            date: Target date (default: today)

        Returns:
            Dictionary with statistics
        """
        if date is None:
            date = datetime.utcnow()

        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        query = """
        MATCH (i:ImageFile)
        WHERE i.ingested_at >= datetime($start_date) AND i.ingested_at < datetime($end_date)
        WITH count(i) as images_ingested
        
        MATCH (i:ImageFile)-[:BELONGS_TO]->(c:ImageCluster)
        WHERE i.ingested_at >= datetime($start_date) AND i.ingested_at < datetime($end_date)
        WITH images_ingested,
             count(DISTINCT CASE WHEN c.repost_count > 1 THEN i END) as duplicates_detected,
             count(DISTINCT CASE WHEN c.repost_count = 1 THEN c.id END) as new_clusters
        
        RETURN images_ingested,
               duplicates_detected,
               new_clusters,
               CASE WHEN images_ingested > 0 
                    THEN toFloat(duplicates_detected) / toFloat(images_ingested)
                    ELSE 0.0 
               END as duplicate_rate
        """

        result = self.neo4j.execute_read(
            query,
            parameters={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        if result:
            record = result[0]
            return {
                "date": date.date().isoformat(),
                "images_ingested": record.get("images_ingested", 0),
                "duplicates_detected": record.get("duplicates_detected", 0),
                "new_clusters": record.get("new_clusters", 0),
                "duplicate_rate": record.get("duplicate_rate", 0.0),
            }

        return {
            "date": date.date().isoformat(),
            "images_ingested": 0,
            "duplicates_detected": 0,
            "new_clusters": 0,
            "duplicate_rate": 0.0,
        }

    def get_subreddit_statistics(
        self, subreddit: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get repost statistics by subreddit.

        Args:
            subreddit: Filter by specific subreddit (optional)
            limit: Maximum number of results

        Returns:
            List of subreddit statistics
        """
        if subreddit:
            query = """
            MATCH (p:Post {subreddit: $subreddit})<-[:APPEARED_IN]-(i:ImageFile)-[:BELONGS_TO]->(c:ImageCluster)
            RETURN $subreddit as subreddit,
                   count(DISTINCT i) as total_images,
                   count(DISTINCT CASE WHEN c.repost_count > 1 THEN i END) as reposted_images,
                   count(DISTINCT c) as unique_clusters,
                   avg(c.repost_count) as avg_reposts_per_cluster,
                   max(c.repost_count) as max_reposts
            """
            params = {"subreddit": subreddit}
        else:
            query = """
            MATCH (p:Post)<-[:APPEARED_IN]-(i:ImageFile)-[:BELONGS_TO]->(c:ImageCluster)
            WHERE p.subreddit IS NOT NULL
            WITH p.subreddit as subreddit,
                 count(DISTINCT i) as total_images,
                 count(DISTINCT CASE WHEN c.repost_count > 1 THEN i END) as reposted_images,
                 count(DISTINCT c) as unique_clusters,
                 avg(c.repost_count) as avg_reposts_per_cluster,
                 max(c.repost_count) as max_reposts
            RETURN subreddit,
                   total_images,
                   reposted_images,
                   unique_clusters,
                   avg_reposts_per_cluster,
                   max_reposts
            ORDER BY reposted_images DESC
            LIMIT $limit
            """
            params = {"limit": limit}

        result = self.neo4j.execute_read(query, parameters=params)

        statistics = []
        for record in result:
            statistics.append({
                "subreddit": record.get("subreddit"),
                "total_images": record.get("total_images", 0),
                "reposted_images": record.get("reposted_images", 0),
                "unique_clusters": record.get("unique_clusters", 0),
                "avg_reposts_per_cluster": record.get("avg_reposts_per_cluster", 0.0),
                "max_reposts": record.get("max_reposts", 0),
                "repost_rate": (
                    record.get("reposted_images", 0) / record.get("total_images", 1)
                    if record.get("total_images", 0) > 0
                    else 0.0
                ),
            })

        return statistics

    def get_cluster_size_distribution(self) -> Dict[str, int]:
        """
        Get distribution of cluster sizes.

        Returns:
            Dictionary mapping cluster size (as string) to count
        """
        query = """
        MATCH (c:ImageCluster)<-[:BELONGS_TO]-(i:ImageFile)
        WITH c, count(i) as cluster_size
        WITH cluster_size, count(c) as cluster_count
        RETURN cluster_size, cluster_count
        ORDER BY cluster_size ASC
        """

        result = self.neo4j.execute_read(query)

        distribution = {}
        for record in result:
            size = record.get("cluster_size")
            count = record.get("cluster_count")
            distribution[str(size)] = count

        return distribution

    def get_total_statistics(self) -> Dict[str, Any]:
        """
        Get overall system statistics.

        Returns:
            Dictionary with total statistics
        """
        query = """
        MATCH (i:ImageFile)
        WITH count(i) as total_images
        
        MATCH (c:ImageCluster)
        WITH total_images,
             count(c) as total_clusters,
             sum(c.repost_count) as total_reposts
        
        MATCH (p:Post)
        WITH total_images, total_clusters, total_reposts, count(p) as total_posts
        
        MATCH (c:ImageCluster)
        WHERE c.repost_count > 1
        WITH total_images, total_clusters, total_reposts, total_posts,
             count(c) as clusters_with_reposts
        
        RETURN total_images,
               total_clusters,
               total_reposts,
               total_posts,
               clusters_with_reposts,
               CASE WHEN total_images > 0
                    THEN toFloat(total_reposts) / toFloat(total_images)
                    ELSE 0.0
               END as overall_repost_rate
        """

        result = self.neo4j.execute_read(query)

        if result:
            record = result[0]
            return {
                "total_images": record.get("total_images", 0),
                "total_clusters": record.get("total_clusters", 0),
                "total_reposts": record.get("total_reposts", 0),
                "total_posts": record.get("total_posts", 0),
                "clusters_with_reposts": record.get("clusters_with_reposts", 0),
                "overall_repost_rate": record.get("overall_repost_rate", 0.0),
            }

        return {
            "total_images": 0,
            "total_clusters": 0,
            "total_reposts": 0,
            "total_posts": 0,
            "clusters_with_reposts": 0,
            "overall_repost_rate": 0.0,
        }







