"""Image deduplication system for Reddit content.

This module provides image deduplication capabilities using:
- Valkey (in-memory cache) for fast hash lookups
- Neo4j (graph database) for relationship and lineage tracking
- Perceptual hashing (pHash, dHash) for near-duplicate detection
- SHA-256 for exact duplicate detection
- CLIP embeddings for semantic similarity (optional)
"""

from .hasher import ImageHasher
from .storage import ImageStorage
from .models import (
    ImageHashes,
    IngestRequest,
    IngestResponse,
    DuplicateMatch,
    ClusterInfo,
    LineageResult,
)
from .detector import DuplicateDetector
from .cluster_manager import ClusterManager
from .deduplicator import ImageDeduplicator
from .queries import ImageQueries
from .analytics import ImageAnalytics
from .clip_embedder import CLIPEmbedder
from .batch_process import BatchProcessor

__all__ = [
    "ImageHasher",
    "ImageStorage",
    "ImageDeduplicator",
    "DuplicateDetector",
    "ClusterManager",
    "ImageQueries",
    "ImageAnalytics",
    "CLIPEmbedder",
    "BatchProcessor",
    "ImageHashes",
    "IngestRequest",
    "IngestResponse",
    "DuplicateMatch",
    "ClusterInfo",
    "LineageResult",
]

