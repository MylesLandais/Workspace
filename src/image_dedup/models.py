"""Pydantic models for image deduplication system."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ImageHashes(BaseModel):
    """Image hash values for duplicate detection."""

    sha256: str = Field(..., description="SHA-256 content hash (hex string)")
    phash: Optional[int] = Field(None, description="64-bit perceptual hash (integer)")
    dhash: Optional[int] = Field(None, description="64-bit difference hash (integer)")

    def phash_hex(self) -> Optional[str]:
        """Return pHash as hex string."""
        if self.phash is None:
            return None
        return format(self.phash, "016x")

    def dhash_hex(self) -> Optional[str]:
        """Return dHash as hex string."""
        if self.dhash is None:
            return None
        return format(self.dhash, "016x")


class DuplicateMatch(BaseModel):
    """Information about a duplicate image match."""

    image_id: str = Field(..., description="Matched image ID")
    cluster_id: str = Field(..., description="Cluster ID of the match")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    method: str = Field(..., description="Detection method: 'sha256', 'phash', 'dhash', 'clip'")
    hamming_distance: Optional[int] = Field(None, description="Hamming distance for hash matches")
    similarity_score: Optional[float] = Field(None, description="Similarity score for CLIP matches")


class IngestRequest(BaseModel):
    """Request to ingest an image."""

    image_bytes: bytes = Field(..., description="Raw image bytes")
    post_id: Optional[str] = Field(None, description="Reddit post ID (e.g., 't3_abc123')")
    source: str = Field("reddit", description="Source platform")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (subreddit, author, title, created_at, etc.)",
    )


class IngestResponse(BaseModel):
    """Response from image ingestion."""

    image_id: str = Field(..., description="Unique image ID")
    cluster_id: str = Field(..., description="Cluster ID (may be new or existing)")
    is_duplicate: bool = Field(..., description="Whether this is a duplicate")
    is_repost: bool = Field(..., description="Whether this is a repost")
    confidence: Optional[float] = Field(None, description="Confidence score if duplicate")
    matched_method: Optional[str] = Field(None, description="Method used for match")
    original: Optional[Dict[str, Any]] = Field(None, description="Original image info if repost")
    hashes: ImageHashes = Field(..., description="Computed hash values")


class PostMetadata(BaseModel):
    """Post metadata for tracking."""

    subreddit: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    permalink: Optional[str] = None
    created_at: Optional[datetime] = None
    score: Optional[int] = None


class ClusterMember(BaseModel):
    """Member of an image cluster."""

    image_id: str
    sha256: str
    width: int
    height: int
    created_at: datetime
    post_ids: List[str] = Field(default_factory=list)


class ClusterInfo(BaseModel):
    """Information about an image cluster."""

    cluster_id: str
    canonical_image_id: str
    canonical_sha256: str
    first_seen: datetime
    last_seen: datetime
    repost_count: int
    member_count: int
    canonical_image: Optional[Dict[str, Any]] = None
    members: List[ClusterMember] = Field(default_factory=list)


class LineageNode(BaseModel):
    """A node in the image lineage chain."""

    image_id: str
    post_id: Optional[str] = None
    created_at: datetime
    confidence: Optional[float] = None
    method: Optional[str] = None
    post_metadata: Optional[PostMetadata] = None


class LineageResult(BaseModel):
    """Image lineage tracing result."""

    image_id: str
    cluster_id: str
    original: LineageNode
    reposts: List[LineageNode] = Field(default_factory=list)







