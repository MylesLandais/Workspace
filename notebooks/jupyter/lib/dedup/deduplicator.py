"""Main image deduplication orchestrator."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from .hasher import ImageHasher
from .storage import ImageStorage
from .detector import DuplicateDetector
from .cluster_manager import ClusterManager
from .models import (
    ImageHashes,
    IngestRequest,
    IngestResponse,
    DuplicateMatch,
)
from .clip_embedder import CLIPEmbedder

try:
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False


class ImageDeduplicator:
    """Main orchestrator for image deduplication."""

    def __init__(
        self,
        storage_path: str,
        enable_clip: bool = True,
        phash_threshold: int = 10,
        dhash_threshold: int = 5,
        clip_threshold: float = 0.95,
    ):
        """
        Initialize image deduplicator.

        Args:
            storage_path: Path to storage directory
            enable_clip: Whether to enable CLIP embeddings (default: True)
            phash_threshold: pHash Hamming distance threshold (default: 10)
            dhash_threshold: dHash Hamming distance threshold (default: 5)
            clip_threshold: CLIP similarity threshold (default: 0.95)
        """
        self.hasher = ImageHasher()
        self.storage = ImageStorage(storage_path)
        self.detector = DuplicateDetector(
            phash_threshold=phash_threshold, dhash_threshold=dhash_threshold
        )
        self.cluster_manager = ClusterManager()

        # Initialize CLIP if available and enabled
        self.clip_enabled = enable_clip and CLIP_AVAILABLE
        self.clip_embedder = None
        if self.clip_enabled:
            try:
                self.clip_embedder = CLIPEmbedder()
                self.clip_embedder.threshold = clip_threshold
            except Exception:
                self.clip_enabled = False

    def ingest_image(
        self, request: IngestRequest
    ) -> IngestResponse:
        """
        Ingest an image and detect duplicates.

        Args:
            request: IngestRequest with image bytes and metadata

        Returns:
            IngestResponse with duplicate detection results
        """
        image_bytes = request.image_bytes

        # Compute hashes
        hashes = self.hasher.compute_all_hashes(image_bytes)
        width, height, mime_type = self.hasher.get_image_info(image_bytes)

        # Check for exact duplicate
        exact_match_id = self.detector.check_exact_duplicate(hashes.sha256)
        if exact_match_id:
            # Exact duplicate found
            cluster_id = self.cluster_manager.create_or_get_cluster(
                exact_match_id, hashes.sha256
            )

            return IngestResponse(
                image_id=exact_match_id,
                cluster_id=cluster_id,
                is_duplicate=True,
                is_repost=True,
                confidence=1.0,
                matched_method="sha256",
                original={
                    "image_id": exact_match_id,
                    "first_seen": datetime.utcnow().isoformat(),
                    "post_id": request.post_id,
                },
                hashes=hashes,
            )

        # Store image
        sha256, storage_path, width, height, size_bytes, mime_type = (
            self.storage.store_image(image_bytes, hashes.sha256)
        )

        # Create image ID
        image_id = str(uuid.uuid4())

        # Create ImageFile node in Neo4j
        self.cluster_manager.create_image_file(
            image_id=image_id,
            sha256=sha256,
            phash=hashes.phash,
            dhash=hashes.dhash,
            width=width,
            height=height,
            size_bytes=size_bytes,
            mime_type=mime_type,
            storage_path=storage_path,
            created_at=datetime.utcnow(),
        )

        # Store SHA-256 mapping in Valkey
        self.detector.store_sha256_mapping(sha256, image_id)

        # Check for near-duplicates
        duplicate_matches = []
        if hashes.phash is not None:
            # Get candidate clusters from buckets
            bucket_keys = self.detector.get_adjacent_bucket_keys(hashes.phash)
            candidate_clusters = set()
            for bucket_key in bucket_keys:
                clusters = self.detector.get_clusters_from_bucket(bucket_key)
                candidate_clusters.update(clusters)

            # Get image hashes for distance computation
            if candidate_clusters:
                image_hashes = self.cluster_manager.get_image_hashes_for_clusters(
                    list(candidate_clusters)
                )
                duplicate_matches = self.detector.find_near_duplicates(
                    hashes.phash, hashes.dhash, image_hashes
                )

        # If no hash matches, try CLIP if enabled
        if not duplicate_matches and self.clip_enabled and self.clip_embedder:
            # This would require storing CLIP embeddings and searching
            # For now, skip CLIP search during ingestion (compute embeddings later)
            pass

        # Process duplicate matches
        if duplicate_matches:
            # Found duplicates
            best_match = duplicate_matches[0]
            cluster_id = best_match.cluster_id

            # Assign to cluster
            self.cluster_manager.assign_to_cluster(
                image_id, cluster_id, best_match.confidence
            )

            # Update pHash bucket
            if hashes.phash is not None:
                self.detector.add_to_bucket(hashes.phash, cluster_id)

            # Get original image in cluster
            original_image_id = self.cluster_manager.get_original_in_cluster(
                cluster_id
            )

            # Create repost relationship
            if original_image_id and original_image_id != image_id:
                self.cluster_manager.create_repost_relationship(
                    image_id,
                    original_image_id,
                    best_match.method,
                    best_match.confidence,
                )

            # Update cluster stats and canonical
            self.cluster_manager.update_cluster_stats(cluster_id)
            self.cluster_manager.select_canonical(cluster_id)

            # Get original post info
            original_info = None
            if original_image_id:
                original_info = {
                    "image_id": original_image_id,
                    "first_seen": datetime.utcnow().isoformat(),
                }

            # Link to post if provided
            if request.post_id:
                self.cluster_manager.link_to_post(
                    image_id, request.post_id, request.metadata
                )

            return IngestResponse(
                image_id=image_id,
                cluster_id=cluster_id,
                is_duplicate=True,
                is_repost=True,
                confidence=best_match.confidence,
                matched_method=best_match.method,
                original=original_info,
                hashes=hashes,
            )
        else:
            # New image - create new cluster
            cluster_id = str(uuid.uuid4())
            self.cluster_manager.create_cluster(cluster_id, sha256)
            self.cluster_manager.assign_to_cluster(image_id, cluster_id, 1.0)
            self.cluster_manager.select_canonical(cluster_id)

            # Add to pHash bucket
            if hashes.phash is not None:
                self.detector.add_to_bucket(hashes.phash, cluster_id)

            # Store cluster metadata in Valkey
            cluster_meta = self.cluster_manager.get_cluster_metadata(cluster_id)
            if cluster_meta:
                self.detector.store_cluster_metadata(
                    cluster_id=cluster_id,
                    canonical_sha256=cluster_meta.get("canonical_sha256", sha256),
                    canonical_image_id=image_id,
                    repost_count=cluster_meta.get("repost_count", 1),
                    first_seen=datetime.utcnow(),
                )

            # Link to post if provided
            if request.post_id:
                self.cluster_manager.link_to_post(
                    image_id, request.post_id, request.metadata
                )

            return IngestResponse(
                image_id=image_id,
                cluster_id=cluster_id,
                is_duplicate=False,
                is_repost=False,
                confidence=None,
                matched_method=None,
                original=None,
                hashes=hashes,
            )

