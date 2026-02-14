"""Duplicate detection engine using Valkey for fast lookups."""

import uuid
from typing import Optional, List
from datetime import datetime, timedelta

from .models import DuplicateMatch, ImageHashes
from feed.storage.valkey_connection import get_valkey_connection


class DuplicateDetector:
    """Detects duplicate and near-duplicate images using Valkey cache."""

    # Valkey key patterns
    SHA256_KEY_PREFIX = "image:hashes:"
    PHASH_BUCKET_PREFIX = "phash:bucket:"
    PHASH_BUCKET8_PREFIX = "phash:bucket8:"
    CLUSTER_META_PREFIX = "cluster:meta:"
    RECENT_PHASH_PREFIX = "recent:phash:"
    RECENT_SHA256_PREFIX = "recent:sha256:"

    # Thresholds
    PHASH_THRESHOLD = 10  # Hamming distance threshold for pHash
    DHASH_THRESHOLD = 5   # Hamming distance threshold for dHash

    # TTLs (seconds)
    RECENT_SHA256_TTL = 86400  # 24 hours
    RECENT_PHASH_TTL = 3600    # 1 hour

    # Bucketing
    BUCKET_BITS = 16  # Use high 16 bits for bucket key

    def __init__(self, phash_threshold: int = None, dhash_threshold: int = None, bucket_bits: int = None):
        """
        Initialize duplicate detector.

        Args:
            phash_threshold: Hamming distance threshold for pHash (default: 10)
            dhash_threshold: Hamming distance threshold for dHash (default: 5)
            bucket_bits: Number of bits to use for bucketing (default: 16)
        """
        self.valkey = get_valkey_connection()
        self.client = self.valkey.client
        self.phash_threshold = phash_threshold or self.PHASH_THRESHOLD
        self.dhash_threshold = dhash_threshold or self.DHASH_THRESHOLD
        self.bucket_bits = bucket_bits or self.BUCKET_BITS

    def check_exact_duplicate(self, sha256: str) -> Optional[str]:
        """
        Check for exact duplicate using SHA-256 hash.

        Args:
            sha256: SHA-256 hash (hex string)

        Returns:
            Existing image_id if duplicate found, None otherwise
        """
        # Check recent cache first
        recent_key = f"{self.RECENT_SHA256_PREFIX}{sha256}"
        cached = self.client.get(recent_key)
        if cached:
            return cached

        # Check main index
        key = f"{self.SHA256_KEY_PREFIX}{sha256}"
        image_id = self.client.get(key)
        if image_id:
            # Update recent cache
            self.client.setex(recent_key, self.RECENT_SHA256_TTL, image_id)
            return image_id

        return None

    def store_sha256_mapping(self, sha256: str, image_id: str) -> None:
        """
        Store SHA-256 to image_id mapping in Valkey.

        Args:
            sha256: SHA-256 hash (hex string)
            image_id: Image ID (UUID string)
        """
        key = f"{self.SHA256_KEY_PREFIX}{sha256}"
        self.client.set(key, image_id)

        # Also update recent cache
        recent_key = f"{self.RECENT_SHA256_PREFIX}{sha256}"
        self.client.setex(recent_key, self.RECENT_SHA256_TTL, image_id)

    def get_bucket_key(self, phash: int, bits: Optional[int] = None) -> str:
        """
        Extract bucket key from pHash.

        Args:
            phash: 64-bit pHash (integer)
            bits: Number of bits to use (default: self.bucket_bits)

        Returns:
            Bucket key string
        """
        if bits is None:
            bits = self.bucket_bits

        mask = (1 << bits) - 1
        high_bits = (phash >> (64 - bits)) & mask
        return f"{high_bits:04x}"

    def get_adjacent_bucket_keys(self, phash: int, bits: Optional[int] = None) -> List[str]:
        """
        Get bucket key and adjacent buckets (single-bit flips).

        Args:
            phash: 64-bit pHash (integer)
            bits: Number of bits to use (default: self.bucket_bits)

        Returns:
            List of bucket keys to check
        """
        if bits is None:
            bits = self.bucket_bits

        base_key = self.get_bucket_key(phash, bits)
        bucket_keys = [base_key]

        # Generate adjacent buckets by flipping single bits
        base_bits = (phash >> (64 - bits)) & ((1 << bits) - 1)
        for i in range(bits):
            flipped = base_bits ^ (1 << i)
            bucket_keys.append(f"{flipped:04x}")

        return list(set(bucket_keys))  # Remove duplicates

    def add_to_bucket(self, phash: int, cluster_id: str) -> None:
        """
        Add cluster to pHash bucket.

        Args:
            phash: 64-bit pHash (integer)
            cluster_id: Cluster ID
        """
        bucket_key = self.get_bucket_key(phash)
        key = f"{self.PHASH_BUCKET_PREFIX}{bucket_key}"
        self.client.sadd(key, cluster_id)

    def get_clusters_from_bucket(self, bucket_key: str) -> List[str]:
        """
        Get all cluster IDs from a bucket.

        Args:
            bucket_key: Bucket key

        Returns:
            List of cluster IDs
        """
        key = f"{self.PHASH_BUCKET_PREFIX}{bucket_key}"
        members = self.client.smembers(key)
        return [m for m in members] if members else []

    def get_cluster_metadata(self, cluster_id: str) -> Optional[dict]:
        """
        Get cluster metadata from Valkey cache.

        Args:
            cluster_id: Cluster ID

        Returns:
            Dictionary with cluster metadata or None
        """
        key = f"{self.CLUSTER_META_PREFIX}{cluster_id}"
        data = self.client.hgetall(key)
        return data if data else None

    def store_cluster_metadata(
        self,
        cluster_id: str,
        canonical_sha256: str,
        canonical_image_id: str,
        repost_count: int,
        first_seen: datetime,
    ) -> None:
        """
        Store cluster metadata in Valkey cache.

        Args:
            cluster_id: Cluster ID
            canonical_sha256: Canonical image SHA-256
            canonical_image_id: Canonical image ID
            repost_count: Number of reposts
            first_seen: First seen timestamp
        """
        key = f"{self.CLUSTER_META_PREFIX}{cluster_id}"
        self.client.hset(
            key,
            mapping={
                "canonical_sha256": canonical_sha256,
                "canonical_image_id": canonical_image_id,
                "repost_count": str(repost_count),
                "first_seen": first_seen.isoformat(),
            },
        )

    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """
        Calculate Hamming distance between two integer hashes.

        Args:
            hash1: First hash (integer)
            hash2: Second hash (integer)

        Returns:
            Hamming distance (number of differing bits)
        """
        return bin(hash1 ^ hash2).count("1")

    def calculate_confidence(self, hamming_distance: int, max_distance: int = 64) -> float:
        """
        Calculate confidence score based on Hamming distance.

        Args:
            hamming_distance: Hamming distance
            max_distance: Maximum distance for full decay (default: 64)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        return max(0.0, 1.0 - (hamming_distance / max_distance))

    def find_near_duplicates(
        self, phash: int, dhash: Optional[int] = None, image_hashes_from_neo4j: Optional[List[dict]] = None
    ) -> List[DuplicateMatch]:
        """
        Find near-duplicate images using pHash bucketing.

        Args:
            phash: 64-bit perceptual hash
            dhash: Optional 64-bit difference hash for validation
            image_hashes_from_neo4j: Optional list of dicts with image_id, cluster_id, phash, dhash
                                     from Neo4j for distance computation

        Returns:
            List of DuplicateMatch objects sorted by confidence (highest first)
        """
        matches = []

        # Get bucket keys to check (base + adjacent)
        bucket_keys = self.get_adjacent_bucket_keys(phash)

        # Collect candidate cluster IDs from buckets
        candidate_clusters = set()
        for bucket_key in bucket_keys:
            clusters = self.get_clusters_from_bucket(bucket_key)
            candidate_clusters.update(clusters)

        if not candidate_clusters:
            return matches

        # If we have image hashes from Neo4j, compute actual distances
        if image_hashes_from_neo4j:
            for img_data in image_hashes_from_neo4j:
                candidate_phash = img_data.get("phash")
                candidate_dhash = img_data.get("dhash")
                image_id = img_data.get("image_id")
                cluster_id = img_data.get("cluster_id")

                if candidate_phash is None:
                    continue

                # Compute Hamming distance
                phash_distance = self.hamming_distance(phash, candidate_phash)

                # Check if within threshold
                if phash_distance <= self.phash_threshold:
                    # Validate with dHash if available
                    confidence = self.calculate_confidence(phash_distance, 64)

                    if dhash is not None and candidate_dhash is not None:
                        dhash_distance = self.hamming_distance(dhash, candidate_dhash)
                        if dhash_distance <= self.dhash_threshold:
                            # Both hashes match, boost confidence
                            dhash_confidence = self.calculate_confidence(dhash_distance, 64)
                            confidence = (confidence + dhash_confidence) / 2

                    matches.append(
                        DuplicateMatch(
                            image_id=image_id,
                            cluster_id=cluster_id,
                            confidence=confidence,
                            method="phash" if dhash is None or candidate_dhash is None else "phash+dhash",
                            hamming_distance=phash_distance,
                        )
                    )
        else:
            # Fallback: return cluster matches without distance computation
            # Caller should provide image_hashes_from_neo4j for accurate results
            for cluster_id in candidate_clusters:
                metadata = self.get_cluster_metadata(cluster_id)
                if metadata:
                    matches.append(
                        DuplicateMatch(
                            image_id=metadata.get("canonical_image_id", ""),
                            cluster_id=cluster_id,
                            confidence=0.8,  # Placeholder
                            method="phash",
                            hamming_distance=None,
                        )
                    )

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)

        return matches

    def find_duplicates_from_hashes(self, hashes: ImageHashes) -> List[DuplicateMatch]:
        """
        Find duplicates using all available hash types.

        Args:
            hashes: ImageHashes object with computed hashes

        Returns:
            List of DuplicateMatch objects
        """
        matches = []

        # Check exact duplicate first
        exact_match_id = self.check_exact_duplicate(hashes.sha256)
        if exact_match_id:
            matches.append(
                DuplicateMatch(
                    image_id=exact_match_id,
                    cluster_id="",  # Would fetch from Neo4j
                    confidence=1.0,
                    method="sha256",
                    hamming_distance=0,
                )
            )
            return matches  # Exact match found, return early

        # Check near-duplicates using pHash
        if hashes.phash is not None:
            phash_matches = self.find_near_duplicates(hashes.phash, hashes.dhash)
            matches.extend(phash_matches)

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)

        return matches

