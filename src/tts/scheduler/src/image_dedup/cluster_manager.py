"""Cluster management for Neo4j image deduplication."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from feed.storage.neo4j_connection import get_connection
from .detector import DuplicateDetector


class ClusterManager:
    """Manages image clusters in Neo4j database."""

    def __init__(self):
        """Initialize cluster manager."""
        self.neo4j = get_connection()
        self.detector = DuplicateDetector()

    def create_image_file(
        self,
        image_id: str,
        sha256: str,
        phash: Optional[int],
        dhash: Optional[int],
        width: int,
        height: int,
        size_bytes: int,
        mime_type: str,
        storage_path: str,
        created_at: Optional[datetime] = None,
    ) -> None:
        """
        Create ImageFile node in Neo4j.

        Args:
            image_id: Unique image ID (UUID string)
            sha256: SHA-256 hash
            phash: 64-bit perceptual hash (integer)
            dhash: 64-bit difference hash (integer)
            width: Image width in pixels
            height: Image height in pixels
            size_bytes: File size in bytes
            mime_type: MIME type
            storage_path: Path to stored image file
            created_at: Creation timestamp (default: now)
        """
        if created_at is None:
            created_at = datetime.utcnow()

        query = """
        CREATE (i:ImageFile {
            id: $image_id,
            sha256: $sha256,
            phash: $phash,
            dhash: $dhash,
            width: $width,
            height: $height,
            size_bytes: $size_bytes,
            mime_type: $mime_type,
            storage_path: $storage_path,
            created_at: datetime($created_at),
            ingested_at: datetime()
        })
        RETURN i
        """

        created_at_str = created_at.isoformat()

        # Ensure hash values are within Neo4j's integer range (64-bit signed)
        # If hash is too large, convert to string representation
        phash_val = phash
        dhash_val = dhash
        max_int = 2**63 - 1
        min_int = -(2**63)
        
        if phash_val is not None and (phash_val > max_int or phash_val < min_int):
            # Store as string if out of range
            phash_val = str(phash_val)
        
        if dhash_val is not None and (dhash_val > max_int or dhash_val < min_int):
            # Store as string if out of range
            dhash_val = str(dhash_val)

        self.neo4j.execute_write(
            query,
            parameters={
                "image_id": image_id,
                "sha256": sha256,
                "phash": phash_val,
                "dhash": dhash_val,
                "width": width,
                "height": height,
                "size_bytes": size_bytes,
                "mime_type": mime_type,
                "storage_path": storage_path,
                "created_at": created_at_str,
            },
        )

    def create_cluster(
        self,
        cluster_id: str,
        canonical_sha256: str,
        first_seen: Optional[datetime] = None,
    ) -> None:
        """
        Create ImageCluster node in Neo4j.

        Args:
            cluster_id: Unique cluster ID (UUID string)
            canonical_sha256: SHA-256 of canonical image
            first_seen: First seen timestamp (default: now)
        """
        if first_seen is None:
            first_seen = datetime.utcnow()

        query = """
        CREATE (c:ImageCluster {
            id: $cluster_id,
            canonical_sha256: $canonical_sha256,
            first_seen: datetime($first_seen),
            last_seen: datetime($first_seen),
            repost_count: 1,
            created_at: datetime()
        })
        RETURN c
        """

        first_seen_str = first_seen.isoformat()

        self.neo4j.execute_write(
            query,
            parameters={
                "cluster_id": cluster_id,
                "canonical_sha256": canonical_sha256,
                "first_seen": first_seen_str,
            },
        )

    def assign_to_cluster(
        self,
        image_id: str,
        cluster_id: str,
        confidence: float,
        assigned_at: Optional[datetime] = None,
    ) -> None:
        """
        Assign ImageFile to ImageCluster via BELONGS_TO relationship.

        Args:
            image_id: Image ID
            cluster_id: Cluster ID
            confidence: Confidence score (0-1)
            assigned_at: Assignment timestamp (default: now)
        """
        if assigned_at is None:
            assigned_at = datetime.utcnow()

        query = """
        MATCH (i:ImageFile {id: $image_id})
        MATCH (c:ImageCluster {id: $cluster_id})
        MERGE (i)-[r:BELONGS_TO]->(c)
        SET r.confidence = $confidence,
            r.assigned_at = datetime($assigned_at)
        """

        assigned_at_str = assigned_at.isoformat()

        self.neo4j.execute_write(
            query,
            parameters={
                "image_id": image_id,
                "cluster_id": cluster_id,
                "confidence": confidence,
                "assigned_at": assigned_at_str,
            },
        )

        # Update cluster last_seen and repost_count
        self.update_cluster_stats(cluster_id)

    def update_cluster_stats(self, cluster_id: str) -> None:
        """
        Update cluster statistics (repost_count, last_seen).

        Args:
            cluster_id: Cluster ID
        """
        query = """
        MATCH (c:ImageCluster {id: $cluster_id})<-[:BELONGS_TO]-(i:ImageFile)
        WITH c, count(i) as member_count,
             min(i.created_at) as first_seen,
             max(i.created_at) as last_seen
        SET c.repost_count = member_count - 1,
            c.first_seen = first_seen,
            c.last_seen = last_seen
        """

        self.neo4j.execute_write(query, parameters={"cluster_id": cluster_id})

    def select_canonical(self, cluster_id: str) -> Optional[str]:
        """
        Select canonical image for cluster and create CANONICAL relationship.

        Args:
            cluster_id: Cluster ID

        Returns:
            Canonical image ID, or None if cluster is empty
        """
        query = """
        MATCH (c:ImageCluster {id: $cluster_id})<-[:BELONGS_TO]-(i:ImageFile)
        WITH i, (i.width * i.height) as resolution
        ORDER BY i.created_at ASC, resolution DESC
        LIMIT 1
        MATCH (c:ImageCluster {id: $cluster_id})
        MERGE (c)-[:CANONICAL]->(i)
        SET c.canonical_sha256 = i.sha256
        RETURN i.id as image_id, i.sha256 as sha256
        """

        result = self.neo4j.execute_write(
            query, parameters={"cluster_id": cluster_id}
        )

        if result:
            record = result[0]
            canonical_id = record.get("image_id")
            canonical_sha256 = record.get("sha256")

            # Update Valkey cache
            if canonical_id and canonical_sha256:
                cluster_meta = self.get_cluster_metadata(cluster_id)
                if cluster_meta:
                    self.detector.store_cluster_metadata(
                        cluster_id=cluster_id,
                        canonical_sha256=canonical_sha256,
                        canonical_image_id=canonical_id,
                        repost_count=cluster_meta.get("repost_count", 1),
                        first_seen=self._parse_datetime_value(cluster_meta.get("first_seen", datetime.utcnow())),
                    )

            return canonical_id

        return None

    @staticmethod
    def _parse_datetime_value(value):
        """Parse datetime from various formats (string, datetime, int, float)."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return datetime.utcnow()
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return datetime.utcnow()
        return datetime.utcnow()

    def get_cluster_metadata(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cluster metadata from Neo4j.

        Args:
            cluster_id: Cluster ID

        Returns:
            Dictionary with cluster metadata or None
        """
        query = """
        MATCH (c:ImageCluster {id: $cluster_id})
        RETURN c.id as id,
               c.canonical_sha256 as canonical_sha256,
               c.first_seen as first_seen,
               c.last_seen as last_seen,
               c.repost_count as repost_count
        LIMIT 1
        """

        result = self.neo4j.execute_read(
            query, parameters={"cluster_id": cluster_id}
        )

        if result:
            record = result[0]
            return {
                "id": record.get("id"),
                "canonical_sha256": record.get("canonical_sha256"),
                "first_seen": record.get("first_seen"),
                "last_seen": record.get("last_seen"),
                "repost_count": record.get("repost_count", 0),
            }

        return None

    def get_image_hashes_for_clusters(self, cluster_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get image hashes for candidate clusters for distance computation.

        Args:
            cluster_ids: List of cluster IDs

        Returns:
            List of dicts with image_id, cluster_id, phash, dhash
        """
        if not cluster_ids:
            return []

        query = """
        MATCH (c:ImageCluster)<-[:BELONGS_TO]-(i:ImageFile)
        WHERE c.id IN $cluster_ids
        RETURN i.id as image_id,
               c.id as cluster_id,
               i.phash as phash,
               i.dhash as dhash,
               i.sha256 as sha256
        """

        result = self.neo4j.execute_read(
            query, parameters={"cluster_ids": cluster_ids}
        )

        images = []
        for record in result:
            phash = record.get("phash")
            dhash = record.get("dhash")
            
            # Convert hex strings to integers if needed
            if isinstance(phash, str):
                try:
                    phash = int(phash, 16)
                except (ValueError, TypeError):
                    phash = None
            
            if isinstance(dhash, str):
                try:
                    dhash = int(dhash, 16)
                except (ValueError, TypeError):
                    dhash = None

            images.append({
                "image_id": record.get("image_id"),
                "cluster_id": record.get("cluster_id"),
                "phash": phash,
                "dhash": dhash,
                "sha256": record.get("sha256"),
            })

        return images

    def create_or_get_cluster(self, image_id: str, sha256: str) -> str:
        """
        Create new cluster or get existing cluster for an image.

        Args:
            image_id: Image ID
            sha256: SHA-256 hash

        Returns:
            Cluster ID
        """
        # Check if image already belongs to a cluster
        query = """
        MATCH (i:ImageFile {id: $image_id})-[:BELONGS_TO]->(c:ImageCluster)
        RETURN c.id as cluster_id
        LIMIT 1
        """

        result = self.neo4j.execute_read(
            query, parameters={"image_id": image_id}
        )

        if result:
            return result[0].get("cluster_id")

        # Create new cluster
        cluster_id = str(uuid.uuid4())
        self.create_cluster(cluster_id, sha256)
        self.assign_to_cluster(image_id, cluster_id, 1.0)
        self.select_canonical(cluster_id)

        return cluster_id

    def create_repost_relationship(
        self,
        new_image_id: str,
        original_image_id: str,
        method: str,
        confidence: float,
    ) -> None:
        """
        Create REPOST_OF relationship between images.

        Args:
            new_image_id: New/duplicate image ID
            original_image_id: Original image ID
            method: Detection method ('sha256', 'phash', 'dhash', 'clip')
            confidence: Confidence score (0-1)
        """
        query = """
        MATCH (new:ImageFile {id: $new_image_id})
        MATCH (original:ImageFile {id: $original_image_id})
        MERGE (new)-[r:REPOST_OF]->(original)
        SET r.confidence = $confidence,
            r.detected_method = $method,
            r.detected_at = datetime()
        """

        self.neo4j.execute_write(
            query,
            parameters={
                "new_image_id": new_image_id,
                "original_image_id": original_image_id,
                "method": method,
                "confidence": confidence,
            },
        )

    def link_to_post(
        self,
        image_id: str,
        post_id: str,
        metadata: Dict[str, Any],
        position: int = 0,
    ) -> None:
        """
        Link ImageFile to Post via APPEARED_IN relationship.

        Args:
            image_id: Image ID
            post_id: Post ID (e.g., 't3_abc123')
            metadata: Post metadata (subreddit, author, title, url, permalink, created_at, score)
            position: Position in post if multiple images (default: 0)
        """
        # Create or update Post node
        post_query = """
        MERGE (p:Post {id: $post_id})
        SET p.source = coalesce(p.source, $source),
            p.subreddit = coalesce(p.subreddit, $subreddit),
            p.author = coalesce(p.author, $author),
            p.title = coalesce(p.title, $title),
            p.url = coalesce(p.url, $url),
            p.permalink = coalesce(p.permalink, $permalink),
            p.score = coalesce(p.score, $score),
            p.created_at = coalesce(p.created_at, datetime($created_at)),
            p.ingested_at = datetime()
        """

        created_at = metadata.get("created_at")
        if isinstance(created_at, datetime):
            created_at_str = created_at.isoformat()
        elif created_at is not None:
            created_at_str = str(created_at)
        else:
            created_at_str = datetime.utcnow().isoformat()

        self.neo4j.execute_write(
            post_query,
            parameters={
                "post_id": post_id,
                "source": metadata.get("source", "reddit"),
                "subreddit": metadata.get("subreddit"),
                "author": metadata.get("author"),
                "title": metadata.get("title"),
                "url": metadata.get("url"),
                "permalink": metadata.get("permalink"),
                "score": metadata.get("score"),
                "created_at": created_at_str,
            },
        )

        # Create APPEARED_IN relationship
        link_query = """
        MATCH (i:ImageFile {id: $image_id})
        MATCH (p:Post {id: $post_id})
        MERGE (i)-[r:APPEARED_IN]->(p)
        SET r.position = $position
        """

        self.neo4j.execute_write(
            link_query,
            parameters={
                "image_id": image_id,
                "post_id": post_id,
                "position": position,
            },
        )

    def get_original_in_cluster(self, cluster_id: str) -> Optional[str]:
        """
        Get original (earliest) image ID in cluster.

        Args:
            cluster_id: Cluster ID

        Returns:
            Original image ID or None
        """
        query = """
        MATCH (c:ImageCluster {id: $cluster_id})<-[:BELONGS_TO]-(i:ImageFile)
        WITH i, (i.width * i.height) as resolution
        ORDER BY i.created_at ASC, resolution DESC
        LIMIT 1
        RETURN i.id as image_id
        """

        result = self.neo4j.execute_read(
            query, parameters={"cluster_id": cluster_id}
        )

        if result:
            return result[0].get("image_id")

        return None

