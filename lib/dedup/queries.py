"""Query functions for image deduplication system."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from feed.storage.neo4j_connection import get_connection
from .models import ClusterInfo, ClusterMember, LineageResult, LineageNode, PostMetadata


class ImageQueries:
    """Query functions for image deduplication data."""

    def __init__(self):
        """Initialize query handler."""
        self.neo4j = get_connection()

    def get_cluster_info(
        self, cluster_id: str, include_members: bool = False, member_limit: int = 10
    ) -> Optional[ClusterInfo]:
        """
        Get cluster information with canonical image and optionally members.

        Args:
            cluster_id: Cluster ID
            include_members: Whether to include member images
            member_limit: Maximum number of members to return

        Returns:
            ClusterInfo object or None
        """
        query = """
        MATCH (c:ImageCluster {id: $cluster_id})
        OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:ImageFile)
        OPTIONAL MATCH (c)<-[:BELONGS_TO]-(members:ImageFile)
        WITH c, canonical,
             collect(DISTINCT members) as member_nodes,
             min(members.created_at) as first_seen,
             max(members.created_at) as last_seen,
             count(DISTINCT members) as member_count
        RETURN c.id as cluster_id,
               c.canonical_sha256 as canonical_sha256,
               c.repost_count as repost_count,
               first_seen,
               last_seen,
               member_count,
               canonical.id as canonical_image_id,
               canonical.sha256 as canonical_sha256_val,
               canonical.width as canonical_width,
               canonical.height as canonical_height,
               canonical.storage_path as canonical_storage_path,
               member_nodes
        LIMIT 1
        """

        result = self.neo4j.execute_read(
            query, parameters={"cluster_id": cluster_id}
        )

        if not result:
            return None

        record = result[0]
        cluster_id_val = record.get("cluster_id")
        canonical_image_id = record.get("canonical_image_id")
        canonical_sha256 = record.get("canonical_sha256") or record.get("canonical_sha256_val")

        # Build canonical image info
        canonical_image = None
        if canonical_image_id:
            canonical_image = {
                "image_id": canonical_image_id,
                "sha256": canonical_sha256,
                "width": record.get("canonical_width"),
                "height": record.get("canonical_height"),
                "storage_path": record.get("canonical_storage_path"),
            }

        # Build member list
        members = []
        if include_members:
            member_nodes = record.get("member_nodes", [])
            for member in member_nodes[:member_limit]:
                # Get post IDs for this image
                post_query = """
                MATCH (i:ImageFile {id: $image_id})-[:APPEARED_IN]->(p:Post)
                RETURN collect(p.id) as post_ids
                """
                post_result = self.neo4j.execute_read(
                    post_query, parameters={"image_id": member.get("id")}
                )
                post_ids = post_result[0].get("post_ids", []) if post_result else []

                members.append(
                    ClusterMember(
                        image_id=member.get("id"),
                        sha256=member.get("sha256"),
                        width=member.get("width"),
                        height=member.get("height"),
                        created_at=member.get("created_at"),
                        post_ids=post_ids,
                    )
                )

        first_seen = record.get("first_seen")
        last_seen = record.get("last_seen")

        # Convert Neo4j datetime to Python datetime if needed
        if isinstance(first_seen, str):
            try:
                first_seen = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                first_seen = datetime.utcnow()

        if isinstance(last_seen, str):
            try:
                last_seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                last_seen = datetime.utcnow()

        return ClusterInfo(
            cluster_id=cluster_id_val,
            canonical_image_id=canonical_image_id or "",
            canonical_sha256=canonical_sha256 or "",
            first_seen=first_seen,
            last_seen=last_seen,
            repost_count=record.get("repost_count", 0),
            member_count=record.get("member_count", 0),
            canonical_image=canonical_image,
            members=members,
        )

    def get_image_lineage(self, image_id: str) -> Optional[LineageResult]:
        """
        Get image lineage (original and all reposts).

        Args:
            image_id: Image ID

        Returns:
            LineageResult object or None
        """
        # First, get cluster for this image
        cluster_query = """
        MATCH (i:ImageFile {id: $image_id})-[:BELONGS_TO]->(c:ImageCluster)
        RETURN c.id as cluster_id
        LIMIT 1
        """

        cluster_result = self.neo4j.execute_read(
            cluster_query, parameters={"image_id": image_id}
        )

        if not cluster_result:
            return None

        cluster_id = cluster_result[0].get("cluster_id")

        # Get all images in cluster with their posts and repost relationships
        lineage_query = """
        MATCH (c:ImageCluster {id: $cluster_id})<-[:BELONGS_TO]-(i:ImageFile)
        OPTIONAL MATCH (i)-[:APPEARED_IN]->(p:Post)
        OPTIONAL MATCH (i)-[r:REPOST_OF]->(original:ImageFile)
        WITH i, collect(DISTINCT p) as posts, collect(DISTINCT r) as repost_rels, original
        ORDER BY i.created_at ASC
        RETURN i.id as image_id,
               i.created_at as created_at,
               posts,
               repost_rels,
               original.id as original_id,
               original.created_at as original_created_at
        """

        result = self.neo4j.execute_read(
            lineage_query, parameters={"cluster_id": cluster_id}
        )

        if not result:
            return None

        # Find original (first image)
        original_record = result[0]
        original_image_id = original_record.get("image_id")
        original_created_at = original_record.get("created_at")

        # Convert datetime if needed
        if isinstance(original_created_at, str):
            try:
                original_created_at = datetime.fromisoformat(
                    original_created_at.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                original_created_at = datetime.utcnow()

        # Get post metadata for original
        original_posts = original_record.get("posts", [])
        original_post_id = None
        original_post_metadata = None

        if original_posts and len(original_posts) > 0:
            original_post = original_posts[0]
            original_post_id = original_post.get("id")
            original_post_metadata = PostMetadata(
                subreddit=original_post.get("subreddit"),
                author=original_post.get("author"),
                title=original_post.get("title"),
                url=original_post.get("url"),
                permalink=original_post.get("permalink"),
                created_at=original_post.get("created_at"),
                score=original_post.get("score"),
            )

        original_node = LineageNode(
            image_id=original_image_id,
            post_id=original_post_id,
            created_at=original_created_at,
            confidence=1.0,
            method=None,
            post_metadata=original_post_metadata,
        )

        # Build repost list (all images after the first)
        reposts = []
        for record in result[1:]:
            repost_image_id = record.get("image_id")
            if repost_image_id == original_image_id:
                continue

            repost_created_at = record.get("created_at")
            if isinstance(repost_created_at, str):
                try:
                    repost_created_at = datetime.fromisoformat(
                        repost_created_at.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    repost_created_at = datetime.utcnow()

            # Get repost relationship info
            repost_rels = record.get("repost_rels", [])
            confidence = None
            method = None

            if repost_rels and len(repost_rels) > 0:
                repost_rel = repost_rels[0]
                confidence = repost_rel.get("confidence")
                method = repost_rel.get("detected_method")

            # Get post metadata
            repost_posts = record.get("posts", [])
            repost_post_id = None
            repost_post_metadata = None

            if repost_posts and len(repost_posts) > 0:
                repost_post = repost_posts[0]
                repost_post_id = repost_post.get("id")
                repost_post_metadata = PostMetadata(
                    subreddit=repost_post.get("subreddit"),
                    author=repost_post.get("author"),
                    title=repost_post.get("title"),
                    url=repost_post.get("url"),
                    permalink=repost_post.get("permalink"),
                    created_at=repost_post.get("created_at"),
                    score=repost_post.get("score"),
                )

            reposts.append(
                LineageNode(
                    image_id=repost_image_id,
                    post_id=repost_post_id,
                    created_at=repost_created_at,
                    confidence=confidence,
                    method=method,
                    post_metadata=repost_post_metadata,
                )
            )

        return LineageResult(
            image_id=image_id,
            cluster_id=cluster_id,
            original=original_node,
            reposts=reposts,
        )

    def search_similar_images(
        self, image_id: str, limit: int = 10, min_confidence: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Search for similar images across clusters.

        Args:
            image_id: Source image ID
            limit: Maximum number of results
            min_confidence: Minimum confidence score

        Returns:
            List of similar image records
        """
        # Get image hashes and cluster
        image_query = """
        MATCH (i:ImageFile {id: $image_id})-[:BELONGS_TO]->(c:ImageCluster)
        RETURN i.phash as phash,
               i.dhash as dhash,
               i.sha256 as sha256,
               c.id as cluster_id
        LIMIT 1
        """

        image_result = self.neo4j.execute_read(
            image_query, parameters={"image_id": image_id}
        )

        if not image_result:
            return []

        record = image_result[0]
        source_phash = record.get("phash")
        source_dhash = record.get("dhash")
        source_cluster_id = record.get("cluster_id")

        # Convert to integers if needed
        if source_phash is not None:
            if isinstance(source_phash, str):
                try:
                    source_phash = int(source_phash, 16)
                except (ValueError, TypeError):
                    try:
                        source_phash = int(source_phash)
                    except (ValueError, TypeError):
                        source_phash = None
            elif not isinstance(source_phash, int):
                source_phash = None
            
            # Normalize to signed 64-bit range
            if source_phash is not None:
                max_int = 2**63 - 1
                if source_phash > max_int:
                    source_phash = source_phash - (2**64)

        if source_dhash is not None:
            if isinstance(source_dhash, str):
                try:
                    source_dhash = int(source_dhash, 16)
                except (ValueError, TypeError):
                    try:
                        source_dhash = int(source_dhash)
                    except (ValueError, TypeError):
                        source_dhash = None
            elif not isinstance(source_dhash, int):
                source_dhash = None
            
            # Normalize to signed 64-bit range
            if source_dhash is not None:
                max_int = 2**63 - 1
                if source_dhash > max_int:
                    source_dhash = source_dhash - (2**64)

        if source_phash is None:
            return []

        # Find images in other clusters with similar hashes
        # This is a simplified search - in production, use bucketing
        similarity_query = """
        MATCH (other:ImageFile)-[:BELONGS_TO]->(other_cluster:ImageCluster)
        WHERE other.id <> $image_id
          AND other_cluster.id <> $cluster_id
          AND other.phash IS NOT NULL
        RETURN other.id as image_id,
               other.sha256 as sha256,
               other.phash as phash,
               other.dhash as dhash,
               other.width as width,
               other.height as height,
               other.storage_path as storage_path,
               other_cluster.id as cluster_id,
               other.created_at as created_at
        LIMIT $limit * 10
        """

        candidates = self.neo4j.execute_read(
            similarity_query,
            parameters={
                "image_id": image_id,
                "cluster_id": source_cluster_id,
                "limit": limit,
            },
        )

        # Compute Hamming distances and filter
        similar = []
        for candidate in candidates:
            candidate_phash = candidate.get("phash")
            if candidate_phash is not None:
                if isinstance(candidate_phash, str):
                    try:
                        candidate_phash = int(candidate_phash, 16)
                    except (ValueError, TypeError):
                        try:
                            candidate_phash = int(candidate_phash)
                        except (ValueError, TypeError):
                            continue
                elif not isinstance(candidate_phash, int):
                    continue
                
                # Normalize to signed 64-bit range
                max_int = 2**63 - 1
                if candidate_phash > max_int:
                    candidate_phash = candidate_phash - (2**64)
            else:
                continue

            # Compute Hamming distance
            distance = bin(source_phash ^ candidate_phash).count("1")
            confidence = max(0.0, 1.0 - (distance / 64.0))

            if confidence >= min_confidence:
                similar.append(
                    {
                        "image_id": candidate.get("image_id"),
                        "cluster_id": candidate.get("cluster_id"),
                        "sha256": candidate.get("sha256"),
                        "similarity_score": confidence,
                        "hamming_distance": distance,
                        "width": candidate.get("width"),
                        "height": candidate.get("height"),
                        "storage_path": candidate.get("storage_path"),
                        "created_at": candidate.get("created_at"),
                    }
                )

        # Sort by similarity and return top results
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar[:limit]

    def get_cluster_members(
        self, cluster_id: str, limit: int = 100
    ) -> List[ClusterMember]:
        """
        Get all members of a cluster.

        Args:
            cluster_id: Cluster ID
            limit: Maximum number of members to return

        Returns:
            List of ClusterMember objects
        """
        query = """
        MATCH (c:ImageCluster {id: $cluster_id})<-[:BELONGS_TO]-(i:ImageFile)
        OPTIONAL MATCH (i)-[:APPEARED_IN]->(p:Post)
        WITH i, collect(DISTINCT p.id) as post_ids
        ORDER BY i.created_at ASC
        RETURN i.id as image_id,
               i.sha256 as sha256,
               i.width as width,
               i.height as height,
               i.created_at as created_at,
               post_ids
        LIMIT $limit
        """

        result = self.neo4j.execute_read(
            query, parameters={"cluster_id": cluster_id, "limit": limit}
        )

        members = []
        for record in result:
            created_at = record.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    created_at = datetime.utcnow()

            members.append(
                ClusterMember(
                    image_id=record.get("image_id"),
                    sha256=record.get("sha256"),
                    width=record.get("width"),
                    height=record.get("height"),
                    created_at=created_at,
                    post_ids=record.get("post_ids", []),
                )
            )

        return members

