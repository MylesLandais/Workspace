"""Reverse image search service for finding images in feed and checking duplicates.

This service provides multiple lookup strategies:
1. URL-based lookup (exact URL match)
2. Hash-based lookup (SHA-256 for exact duplicates, dHash for near-duplicates)
3. Vector similarity search (CLIP embeddings for visual similarity)
4. External reverse image search APIs (optional)
"""

from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import redis
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from ..storage.neo4j_connection import Neo4jConnection
from ..storage.valkey_connection import get_valkey_connection
from ..utils.image_hash import (
    download_and_hash_image,
    hash_image_url,
    compute_sha256_hash,
    compute_dhash
)
from ...image_dedup.clip_embedder import CLIPEmbedder


@dataclass
class ImageMatch:
    """Represents a match found for an image."""
    image_url: str
    match_type: str  # 'url', 'sha256', 'dhash', 'vector', 'external'
    confidence: float  # 0.0 to 1.0
    source_post_id: Optional[str] = None
    source_comment_id: Optional[str] = None
    source_product_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ImageLookupResult:
    """Result of an image lookup operation."""
    image_url: str
    found: bool
    matches: List[ImageMatch]
    hashes: Optional[Dict[str, str]] = None  # sha256, dhash
    embedding_computed: bool = False


class ReverseImageSearch:
    """Reverse image search service for feed management."""

    # Valkey/Redis configuration
    INDEX_NAME = "image_embeddings_idx"
    VECTOR_DIM = 512  # CLIP ViT-B/32 dimension
    DOC_PREFIX = "img:"
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        valkey: Optional[redis.Redis] = None,
        enable_vector_search: bool = True,
        enable_external_apis: bool = False
    ):
        """
        Initialize reverse image search service.
        
        Args:
            neo4j: Neo4j connection for graph queries
            valkey: Optional Valkey/Redis connection for vector search
            enable_vector_search: Enable CLIP-based vector similarity search
            enable_external_apis: Enable external reverse image search APIs
        """
        self.neo4j = neo4j
        self.valkey = valkey or (get_valkey_connection().client if enable_vector_search else None)
        self.enable_vector_search = enable_vector_search and self.valkey is not None
        self.enable_external_apis = enable_external_apis
        
        # Initialize CLIP embedder if vector search is enabled
        self.clip_embedder: Optional[CLIPEmbedder] = None
        if self.enable_vector_search:
            try:
                self.clip_embedder = CLIPEmbedder()
                self._ensure_vector_index()
            except ImportError:
                print("Warning: CLIP embedder not available. Vector search disabled.")
                self.enable_vector_search = False
    
    def _ensure_vector_index(self) -> None:
        """Create ValkeySearch index for image embeddings if it doesn't exist."""
        if not self.valkey:
            return
        
        try:
            self.valkey.ft(self.INDEX_NAME).info()
        except redis.exceptions.ResponseError:
            # Index doesn't exist, create it
            schema = (
                TagField("image_url"),
                TagField("neo4j_id"),
                VectorField(
                    "embedding",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.VECTOR_DIM,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            definition = IndexDefinition(
                prefix=[self.DOC_PREFIX],
                index_type=IndexType.HASH
            )
            self.valkey.ft(self.INDEX_NAME).create_index(schema, definition=definition)
    
    def check_if_crawled(self, image_url: str) -> ImageLookupResult:
        """
        Check if an image URL has already been crawled/stored.
        
        This is the primary method for feed management - quickly check if we've
        seen this image before.
        
        Args:
            image_url: Image URL to check
            
        Returns:
            ImageLookupResult with matches found
        """
        matches: List[ImageMatch] = []
        
        # Strategy 1: URL-based lookup (fastest)
        url_matches = self._lookup_by_url(image_url)
        matches.extend(url_matches)
        
        # Strategy 2: Hash-based lookup (for exact/near-duplicates)
        if not matches:  # Only do expensive hash computation if URL lookup failed
            hash_matches = self._lookup_by_hash(image_url)
            matches.extend(hash_matches)
        
        # Strategy 3: Vector similarity search (for visual similarity)
        if self.enable_vector_search and not matches:
            vector_matches = self._lookup_by_vector(image_url)
            matches.extend(vector_matches)
        
        return ImageLookupResult(
            image_url=image_url,
            found=len(matches) > 0,
            matches=matches
        )
    
    def find_original_source(
        self,
        image_url: str,
        include_external: bool = False
    ) -> ImageLookupResult:
        """
        Find the original source of an image.
        
        This method:
        1. Checks our database for the earliest occurrence
        2. Optionally queries external reverse image search APIs
        
        Args:
            image_url: Image URL to find source for
            include_external: If True, also query external APIs (TinEye, etc.)
            
        Returns:
            ImageLookupResult with source information
        """
        matches: List[ImageMatch] = []
        
        # First, check our database
        db_matches = self._find_earliest_occurrence(image_url)
        matches.extend(db_matches)
        
        # Optionally query external APIs
        if include_external and self.enable_external_apis:
            external_matches = self._query_external_apis(image_url)
            matches.extend(external_matches)
        
        return ImageLookupResult(
            image_url=image_url,
            found=len(matches) > 0,
            matches=matches
        )
    
    def find_exact_matches(
        self,
        image_url: str,
        include_external: bool = False
    ) -> ImageLookupResult:
        """
        Find exact matches of an image across the internet.
        
        Uses multiple strategies:
        1. Hash-based matching in our database
        2. Vector similarity search for visually identical images
        3. External reverse image search APIs
        
        Args:
            image_url: Image URL to find matches for
            include_external: If True, query external APIs
            
        Returns:
            ImageLookupResult with all matches found
        """
        matches: List[ImageMatch] = []
        hashes: Optional[Dict[str, str]] = None
        
        # Download and hash the image
        sha256, dhash, image_bytes = download_and_hash_image(image_url)
        if sha256:
            hashes = {"sha256": sha256, "dhash": dhash or ""}
            
            # Strategy 1: Hash-based exact matches
            hash_matches = self._lookup_by_hash_values(sha256, dhash)
            matches.extend(hash_matches)
        
        # Strategy 2: Vector similarity for visually identical
        if self.enable_vector_search and image_bytes:
            vector_matches = self._lookup_by_vector_bytes(image_bytes)
            matches.extend(vector_matches)
        
        # Strategy 3: External APIs
        if include_external and self.enable_external_apis:
            external_matches = self._query_external_apis(image_url)
            matches.extend(external_matches)
        
        return ImageLookupResult(
            image_url=image_url,
            found=len(matches) > 0,
            matches=matches,
            hashes=hashes,
            embedding_computed=self.enable_vector_search and image_bytes is not None
        )
    
    def _lookup_by_url(self, image_url: str) -> List[ImageMatch]:
        """Look up image by exact URL match."""
        query = """
        MATCH (img:Image {url: $url})
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(p:Post)
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(c:Comment)
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(prod:Product)
        RETURN 
            img.url as url,
            collect(DISTINCT p.id) as post_ids,
            collect(DISTINCT c.id) as comment_ids,
            collect(DISTINCT prod.id) as product_ids,
            img.created_at as created_at
        LIMIT 1
        """
        
        result = self.neo4j.execute_read(query, parameters={"url": image_url})
        if not result:
            return []
        
        record = result[0]
        post_ids = [pid for pid in record.get("post_ids", []) if pid]
        comment_ids = [cid for cid in record.get("comment_ids", []) if cid]
        product_ids = [pid for pid in record.get("product_ids", []) if pid]
        
        matches = []
        for post_id in post_ids:
            matches.append(ImageMatch(
                image_url=image_url,
                match_type="url",
                confidence=1.0,
                source_post_id=post_id
            ))
        for comment_id in comment_ids:
            matches.append(ImageMatch(
                image_url=image_url,
                match_type="url",
                confidence=1.0,
                source_comment_id=comment_id
            ))
        for product_id in product_ids:
            matches.append(ImageMatch(
                image_url=image_url,
                match_type="url",
                confidence=1.0,
                source_product_id=product_id
            ))
        
        return matches
    
    def _lookup_by_hash(self, image_url: str) -> List[ImageMatch]:
        """Look up image by hash values (downloads image first)."""
        sha256, dhash, _ = download_and_hash_image(image_url)
        if not sha256:
            return []
        
        return self._lookup_by_hash_values(sha256, dhash)
    
    def _lookup_by_hash_values(
        self,
        sha256: str,
        dhash: Optional[str]
    ) -> List[ImageMatch]:
        """Look up images by hash values."""
        matches: List[ImageMatch] = []
        
        # Check for SHA-256 exact match
        if sha256:
            query = """
            MATCH (img:Image)
            WHERE img.sha256_hash = $sha256
            OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(p:Post)
            OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(c:Comment)
            OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(prod:Product)
            RETURN 
                img.url as url,
                collect(DISTINCT p.id) as post_ids,
                collect(DISTINCT c.id) as comment_ids,
                collect(DISTINCT prod.id) as product_ids
            """
            
            result = self.neo4j.execute_read(
                query,
                parameters={"sha256": sha256}
            )
            
            for record in result:
                url = record["url"]
                for post_id in record.get("post_ids", []):
                    if post_id:
                        matches.append(ImageMatch(
                            image_url=url,
                            match_type="sha256",
                            confidence=1.0,
                            source_post_id=post_id
                        ))
                for comment_id in record.get("comment_ids", []):
                    if comment_id:
                        matches.append(ImageMatch(
                            image_url=url,
                            match_type="sha256",
                            confidence=1.0,
                            source_comment_id=comment_id
                        ))
                for product_id in record.get("product_ids", []):
                    if product_id:
                        matches.append(ImageMatch(
                            image_url=url,
                            match_type="sha256",
                            confidence=1.0,
                            source_product_id=product_id
                        ))
        
        # Check for dHash near-duplicate (if available)
        if dhash and not matches:
            # Note: dHash comparison requires Hamming distance calculation
            # For now, we'll do exact dHash match. For fuzzy matching, you'd
            # need to store dHash and compute Hamming distance in query
            query = """
            MATCH (img:Image)
            WHERE img.dhash = $dhash
            OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(p:Post)
            RETURN 
                img.url as url,
                collect(DISTINCT p.id) as post_ids
            LIMIT 10
            """
            
            result = self.neo4j.execute_read(
                query,
                parameters={"dhash": dhash}
            )
            
            for record in result:
                url = record["url"]
                for post_id in record.get("post_ids", []):
                    if post_id:
                        matches.append(ImageMatch(
                            image_url=url,
                            match_type="dhash",
                            confidence=0.95,  # Near-duplicate, not exact
                            source_post_id=post_id
                        ))
        
        return matches
    
    def _lookup_by_vector(self, image_url: str) -> List[ImageMatch]:
        """Look up similar images using vector similarity search."""
        if not self.enable_vector_search or not self.clip_embedder:
            return []
        
        # Download image and compute embedding
        _, _, image_bytes = download_and_hash_image(image_url)
        if not image_bytes:
            return []
        
        return self._lookup_by_vector_bytes(image_bytes)
    
    def _lookup_by_vector_bytes(self, image_bytes: bytes) -> List[ImageMatch]:
        """Look up similar images using vector similarity search from bytes."""
        if not self.enable_vector_search or not self.clip_embedder or not self.valkey:
            return []
        
        # Compute embedding
        embedding = self.clip_embedder.compute_embedding(image_bytes)
        if embedding is None:
            return []
        
        # Search in Valkey
        query_bytes = embedding.astype(np.float32).tobytes()
        q = Query(f"*=>[KNN 10 @embedding $vec AS score]")\
            .sort_by("score")\
            .return_fields("image_url", "neo4j_id", "score")\
            .dialect(2)
        
        try:
            results = self.valkey.ft(self.INDEX_NAME).search(
                q,
                query_params={"vec": query_bytes}
            )
            
            matches: List[ImageMatch] = []
            for doc in results.docs:
                score = float(doc.score)
                if score >= 0.85:  # Similarity threshold
                    image_url = doc.image_url
                    neo4j_id = doc.neo4j_id if hasattr(doc, 'neo4j_id') else None
                    
                    # Fetch source information from Neo4j
                    source_info = self._get_image_source_info(image_url)
                    
                    matches.append(ImageMatch(
                        image_url=image_url,
                        match_type="vector",
                        confidence=score,
                        source_post_id=source_info.get("post_id"),
                        source_comment_id=source_info.get("comment_id"),
                        source_product_id=source_info.get("product_id"),
                        metadata={"neo4j_id": neo4j_id}
                    ))
            
            return matches
        except Exception:
            return []
    
    def _get_image_source_info(self, image_url: str) -> Dict[str, Optional[str]]:
        """Get source information for an image from Neo4j."""
        query = """
        MATCH (img:Image {url: $url})
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(p:Post)
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(c:Comment)
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(prod:Product)
        RETURN 
            head(collect(DISTINCT p.id)) as post_id,
            head(collect(DISTINCT c.id)) as comment_id,
            head(collect(DISTINCT prod.id)) as product_id
        LIMIT 1
        """
        
        result = self.neo4j.execute_read(query, parameters={"url": image_url})
        if result:
            record = result[0]
            return {
                "post_id": record.get("post_id"),
                "comment_id": record.get("comment_id"),
                "product_id": record.get("product_id")
            }
        return {"post_id": None, "comment_id": None, "product_id": None}
    
    def _find_earliest_occurrence(self, image_url: str) -> List[ImageMatch]:
        """Find the earliest occurrence of an image in our database."""
        query = """
        MATCH (img:Image {url: $url})
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(p:Post)
        OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(c:Comment)
        WITH img, p, c,
             COALESCE(p.created_utc, c.created_utc, img.created_at) as earliest_time
        ORDER BY earliest_time ASC
        LIMIT 1
        RETURN 
            img.url as url,
            p.id as post_id,
            c.id as comment_id,
            earliest_time
        """
        
        result = self.neo4j.execute_read(query, parameters={"url": image_url})
        if not result:
            return []
        
        record = result[0]
        return [ImageMatch(
            image_url=record["url"],
            match_type="url",
            confidence=1.0,
            source_post_id=record.get("post_id"),
            source_comment_id=record.get("comment_id"),
            metadata={"earliest_time": str(record.get("earliest_time"))}
        )]
    
    def _query_external_apis(self, image_url: str) -> List[ImageMatch]:
        """Query external reverse image search APIs (TinEye, Google, etc.)."""
        # Placeholder for external API integration
        # You would implement TinEye, Google Images, etc. here
        return []
    
    def index_image(
        self,
        image_url: str,
        image_bytes: Optional[bytes] = None,
        sha256: Optional[str] = None,
        dhash: Optional[str] = None
    ) -> bool:
        """
        Index an image for future reverse search.
        
        Stores:
        - Hash values in Neo4j Image node
        - CLIP embedding in Valkey for vector search
        
        Args:
            image_url: Image URL
            image_bytes: Optional image bytes (will download if not provided)
            sha256: Optional SHA-256 hash (will compute if not provided)
            dhash: Optional dHash (will compute if not provided)
            
        Returns:
            True if indexing succeeded
        """
        # Download and hash if needed
        if not image_bytes or not sha256:
            sha256_result, dhash_result, image_bytes_result = download_and_hash_image(image_url)
            if not image_bytes_result:
                return False
            
            image_bytes = image_bytes_result
            if not sha256:
                sha256 = sha256_result
            if not dhash:
                dhash = dhash_result
        
        # Update Neo4j Image node with hashes
        query = """
        MATCH (img:Image {url: $url})
        SET img.sha256_hash = $sha256,
            img.dhash = $dhash,
            img.indexed_at = datetime()
        RETURN img.url as url
        """
        
        try:
            self.neo4j.execute_write(
                query,
                parameters={
                    "url": image_url,
                    "sha256": sha256,
                    "dhash": dhash or ""
                }
            )
        except Exception:
            pass  # Image node might not exist yet
        
        # Index embedding in Valkey if vector search is enabled
        if self.enable_vector_search and self.clip_embedder and self.valkey:
            embedding = self.clip_embedder.compute_embedding(image_bytes)
            if embedding is not None:
                embedding_bytes = embedding.astype(np.float32).tobytes()
                key = f"{self.DOC_PREFIX}{image_url}"
                
                # Get Neo4j ID if available
                neo4j_query = """
                MATCH (img:Image {url: $url})
                RETURN id(img) as neo4j_id
                LIMIT 1
                """
                neo4j_result = self.neo4j.execute_read(
                    neo4j_query,
                    parameters={"url": image_url}
                )
                neo4j_id = str(neo4j_result[0]["neo4j_id"]) if neo4j_result else None
                
                self.valkey.hset(
                    key,
                    mapping={
                        "image_url": image_url,
                        "neo4j_id": neo4j_id or "",
                        "embedding": embedding_bytes,
                        "indexed_at": datetime.now().isoformat()
                    }
                )
        
        return True




