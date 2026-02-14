"""GraphQL schema for reverse image search functionality."""

from typing import List, Optional
import strawberry
from datetime import datetime

from ..storage.neo4j_connection import get_connection
from ..services.reverse_image_search import ReverseImageSearch, ImageLookupResult, ImageMatch
from ..services.spider_recovery import SpiderRecovery
from ..services.video_watermark_detection import (
    VideoIdentificationService,
    VideoIdentificationResult,
    WatermarkDetection,
    FaceMatch,
    SceneMatch,
)
from ..services.stash_integration import StashClient, StashScene, StashPerformer


@strawberry.type
class ImageMatchType:
    """Image match result."""
    image_url: str
    match_type: str  # 'url', 'sha256', 'dhash', 'vector', 'external'
    confidence: float
    source_post_id: Optional[str] = None
    source_comment_id: Optional[str] = None
    source_product_id: Optional[str] = None
    metadata: Optional[str] = None  # JSON string


@strawberry.type
class ImageHashes:
    """Image hash values."""
    sha256: Optional[str] = None
    dhash: Optional[str] = None


@strawberry.type
class ImageLookupResultType:
    """Result of image lookup operation."""
    image_url: str
    found: bool
    matches: List[ImageMatchType]
    hashes: Optional[ImageHashes] = None
    embedding_computed: bool = False


@strawberry.type
class SimilarImageResult:
    """Result of visual similarity search."""
    image_url: str
    matches: List[ImageMatchType]
    total_found: int


@strawberry.type
class ImageStatusResult:
    """Status check result for image."""
    image_url: str
    found: bool
    match_type: Optional[str] = None
    matches: List[ImageMatchType]
    recovery_needed: bool
    similar_images: List[ImageMatchType]


@strawberry.type
class PublicSearchProvider:
    """Public search provider result."""
    provider: str
    results: List[ImageMatchType]
    total_results: int


@strawberry.type
class PublicSearchResult:
    """Result from public image search APIs."""
    image_url: str
    providers: List[PublicSearchProvider]


@strawberry.type
class GarmentStyleMatch:
    """Garment style match for an image."""
    uuid: str
    name: str
    features: List[str]
    confidence: float
    matched_products: List[str]  # Product IDs


@strawberry.type
class ImageMatchResult:
    """Complete image match result with ontology."""
    image_url: str
    found: bool
    matches: List[ImageMatchType]
    garment_styles: List[GarmentStyleMatch]


@strawberry.type
class RecoveryResult:
    """Result of post recovery operation."""
    post_url: str
    success: bool
    post_id: Optional[str] = None
    images_found: int = 0
    images_indexed: int = 0
    error: Optional[str] = None


@strawberry.type
class IndexResult:
    """Result of image indexing operation."""
    image_url: str
    success: bool
    hashes_stored: bool = False
    embedding_stored: bool = False
    error: Optional[str] = None


@strawberry.type
class WatermarkDetectionType:
    """Watermark detection result."""
    text: str
    confidence: float
    bbox: str  # JSON string of [x, y, width, height]
    frame_number: int
    timestamp: float


@strawberry.type
class FaceMatchType:
    """Face recognition match result."""
    actor_id: str
    actor_name: str
    confidence: float
    frame_number: int
    bbox: str  # JSON string


@strawberry.type
class SceneMatchType:
    """Scene match from database."""
    scene_id: str
    scene_title: str
    studio: str
    actors: List[str]
    url: str
    confidence: float
    match_type: str


@strawberry.type
class VideoIdentificationResultType:
    """Complete video identification result."""
    video_path: str
    identified: bool
    studio: Optional[str] = None
    watermarks: List[WatermarkDetectionType]
    face_matches: List[FaceMatchType]
    scene_matches: List[SceneMatchType]
    metadata: Optional[str] = None  # JSON string


@strawberry.type
class StashPerformerType:
    """Stash performer."""
    id: str
    name: str
    url: Optional[str] = None
    stash_id: Optional[str] = None
    scene_count: Optional[int] = None


@strawberry.type
class StashSceneType:
    """Stash scene."""
    id: str
    title: str
    url: str
    date: Optional[str] = None
    studio: Optional[str] = None
    performers: List[StashPerformerType]
    tags: List[str]
    stash_id: Optional[str] = None
    phash: Optional[str] = None


@strawberry.enum
class ImageSearchProvider:
    """Public image search providers."""
    TINEYE = "tineye"
    GOOGLE_IMAGES = "google_images"
    BING_VISUAL = "bing_visual"


def _convert_image_match(match: ImageMatch) -> ImageMatchType:
    """Convert ImageMatch to GraphQL type."""
    import json
    metadata_str = None
    if match.metadata:
        metadata_str = json.dumps(match.metadata)
    
    return ImageMatchType(
        image_url=match.image_url,
        match_type=match.match_type,
        confidence=match.confidence,
        source_post_id=match.source_post_id,
        source_comment_id=match.source_comment_id,
        source_product_id=match.source_product_id,
        metadata=metadata_str,
    )


def _convert_lookup_result(result: ImageLookupResult) -> ImageLookupResultType:
    """Convert ImageLookupResult to GraphQL type."""
    matches = [_convert_image_match(m) for m in result.matches]
    
    hashes = None
    if result.hashes:
        hashes = ImageHashes(
            sha256=result.hashes.get("sha256"),
            dhash=result.hashes.get("dhash"),
        )
    
    return ImageLookupResultType(
        image_url=result.image_url,
        found=result.found,
        matches=matches,
        hashes=hashes,
        embedding_computed=result.embedding_computed,
    )


class ImageSearchQuery:
    """GraphQL queries for reverse image search."""
    
    def __init__(self):
        """Initialize image search query handler."""
        self.neo4j = get_connection()
        self.reverse_search = ReverseImageSearch(
            neo4j=self.neo4j,
            enable_vector_search=True,
            enable_external_apis=False,  # External APIs handled separately
        )
        self.recovery = SpiderRecovery(
            neo4j=self.neo4j,
            reverse_search=self.reverse_search,
        )
    
    @strawberry.field
    def check_image_crawled(self, image_url: str) -> ImageLookupResultType:
        """
        Check if an image URL has already been crawled/stored.
        
        Fast lookup to avoid duplicate work in feed crawlers.
        """
        result = self.reverse_search.check_if_crawled(image_url)
        return _convert_lookup_result(result)
    
    @strawberry.field
    def find_image_source(
        self,
        image_url: str,
        include_external: bool = False
    ) -> ImageLookupResultType:
        """
        Find the original source of an image.
        
        Returns the earliest occurrence in our database.
        """
        result = self.reverse_search.find_original_source(
            image_url,
            include_external=include_external
        )
        return _convert_lookup_result(result)
    
    @strawberry.field
    def find_exact_matches(
        self,
        image_url: str,
        include_external: bool = False
    ) -> ImageLookupResultType:
        """
        Find all exact and near-exact matches of an image.
        
        Uses multiple strategies:
        - SHA-256 hash for exact duplicates
        - dHash for near-duplicates (cropped, resized)
        - CLIP embeddings for visually similar images
        - External APIs (if include_external is True)
        """
        result = self.reverse_search.find_exact_matches(
            image_url,
            include_external=include_external
        )
        return _convert_lookup_result(result)
    
    @strawberry.field
    def find_similar_images(
        self,
        image_url: str,
        min_similarity: float = 0.85,
        limit: int = 10
    ) -> SimilarImageResult:
        """
        Find visually similar images using CLIP embeddings.
        
        Args:
            image_url: Image URL to search for
            min_similarity: Minimum similarity score (0.0 to 1.0)
            limit: Maximum number of results
        """
        result = self.reverse_search.find_exact_matches(image_url)
        
        # Filter by similarity threshold and limit
        filtered_matches = [
            m for m in result.matches
            if m.match_type == "vector" and m.confidence >= min_similarity
        ][:limit]
        
        return SimilarImageResult(
            image_url=image_url,
            matches=[_convert_image_match(m) for m in filtered_matches],
            total_found=len(filtered_matches),
        )
    
    @strawberry.field
    def check_image_status(self, image_url: str) -> ImageStatusResult:
        """
        Check status of an image and determine if recovery is needed.
        
        Useful for detecting images missed due to spider downtime.
        """
        status = self.recovery.check_image_status(image_url, use_vector_search=True)
        
        matches = [_convert_image_match(ImageMatch(
            image_url=m["image_url"],
            match_type=m["type"],
            confidence=m["confidence"],
            source_post_id=m.get("source_post_id"),
            source_comment_id=m.get("source_comment_id"),
            source_product_id=m.get("source_product_id"),
        )) for m in status.get("matches", [])]
        
        similar_images = []
        for similar in status.get("similar_images", []):
            similar_images.append(_convert_image_match(ImageMatch(
                image_url=similar["url"],
                match_type="vector",
                confidence=similar["similarity"],
                source_post_id=similar.get("source_post_id"),
            )))
        
        return ImageStatusResult(
            image_url=status["image_url"],
            found=status["found"],
            match_type=status.get("match_type"),
            matches=matches,
            recovery_needed=status["recovery_needed"],
            similar_images=similar_images,
        )
    
    @strawberry.field
    def public_image_search(
        self,
        image_url: str,
        providers: Optional[List[ImageSearchProvider]] = None
    ) -> PublicSearchResult:
        """
        Search external reverse image search APIs.
        
        Providers: TINEYE, GOOGLE_IMAGES, BING_VISUAL
        """
        # Placeholder for external API integration
        # TODO: Implement TinEye, Google Images, Bing Visual Search
        
        provider_results = []
        if providers:
            for provider in providers:
                # Placeholder - would call actual API
                provider_results.append(PublicSearchProvider(
                    provider=provider.value,
                    results=[],
                    total_results=0,
                ))
        
        return PublicSearchResult(
            image_url=image_url,
            providers=provider_results,
        )
    
    @strawberry.field
    def find_image_matches(self, image_url: str) -> ImageMatchResult:
        """
        Find image matches with ontology integration.
        
        Returns matches along with associated garment styles.
        """
        result = self.reverse_search.find_exact_matches(image_url)
        
        # Query garment styles for matched products
        garment_styles = []
        for match in result.matches:
            if match.source_product_id:
                # Query product's garment style
                query = """
                MATCH (p:Product {id: $product_id})-[:HAS_STYLE]->(gs:GarmentStyle)
                RETURN gs.uuid as uuid, gs.name as name, gs.features as features
                LIMIT 1
                """
                style_result = self.neo4j.execute_read(
                    query,
                    parameters={"product_id": match.source_product_id}
                )
                
                if style_result:
                    style = style_result[0]
                    # Get matched products for this style
                    products_query = """
                    MATCH (gs:GarmentStyle {uuid: $uuid})<-[:HAS_STYLE]-(p:Product)
                    RETURN p.id as id
                    LIMIT 10
                    """
                    products_result = self.neo4j.execute_read(
                        products_query,
                        parameters={"uuid": style["uuid"]}
                    )
                    product_ids = [p["id"] for p in products_result]
                    
                    garment_styles.append(GarmentStyleMatch(
                        uuid=style["uuid"],
                        name=style.get("name", ""),
                        features=style.get("features", []),
                        confidence=match.confidence,
                        matched_products=product_ids,
                    ))
        
        return ImageMatchResult(
            image_url=image_url,
            found=result.found,
            matches=[_convert_image_match(m) for m in result.matches],
            garment_styles=garment_styles,
        )
    
    @strawberry.field
    def find_images_by_style(self, style_uuid: str) -> List[ImageMatchType]:
        """
        Find all images associated with a garment style.
        
        Returns images from products that have this style.
        """
        query = """
        MATCH (gs:GarmentStyle {uuid: $uuid})<-[:HAS_STYLE]-(p:Product)-[:HAS_IMAGE]->(img:Image)
        RETURN DISTINCT img.url as url, p.id as product_id
        LIMIT 50
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"uuid": style_uuid}
        )
        
        matches = []
        for record in result:
            matches.append(ImageMatchType(
                image_url=record["url"],
                match_type="ontology",
                confidence=1.0,
                source_product_id=record.get("product_id"),
            ))
        
        return matches
    
    @strawberry.field
    def stash_scenes(
        self,
        stash_url: str,
        studio: Optional[str] = None,
        performer_name: Optional[str] = None,
        limit: int = 50
    ) -> List[StashSceneType]:
        """
        Query Stash instance for scenes.
        
        Args:
            stash_url: Stash instance URL (e.g., "http://192.168.0.222:9999")
            studio: Filter by studio (e.g., "FantasyHD")
            performer_name: Filter by performer name
            limit: Maximum results
        """
        client = StashClient(stash_url)
        scenes = client.search_scenes(
            studio=studio,
            performer_name=performer_name,
            limit=limit
        )
        
        result = []
        for scene in scenes:
            performers = [
                StashPerformerType(
                    id=p.id,
                    name=p.name,
                    url=p.url,
                    stash_id=p.stash_id,
                    scene_count=p.scene_count
                )
                for p in (scene.performers or [])
            ]
            
            result.append(StashSceneType(
                id=scene.id,
                title=scene.title,
                url=scene.url,
                date=scene.date,
                studio=scene.studio,
                performers=performers,
                tags=scene.tags or [],
                stash_id=scene.stash_id,
                phash=scene.phash
            ))
        
        return result
    
    @strawberry.field
    def stash_performers(
        self,
        stash_url: str,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[StashPerformerType]:
        """
        Query Stash instance for performers.
        
        Args:
            stash_url: Stash instance URL
            query: Search query
            limit: Maximum results
        """
        client = StashClient(stash_url)
        performers = client.search_performers(query=query, limit=limit)
        
        return [
            StashPerformerType(
                id=p.id,
                name=p.name,
                url=p.url,
                stash_id=p.stash_id,
                scene_count=p.scene_count
            )
            for p in performers
        ]
    
    @strawberry.field
    def identify_video(
        self,
        video_path: str,
        watermark_patterns: Optional[List[str]] = None,
        stash_url: Optional[str] = None
    ) -> VideoIdentificationResultType:
        """
        Identify a video using watermark detection, face matching, and database lookups.
        
        This is a complex OSINT task that:
        1. Detects watermarks using OCR
        2. Matches faces against actor database
        3. Searches scene databases
        4. Builds ontology and metadata
        """
        import json
        
        service = VideoIdentificationService(
            neo4j=self.neo4j,
            enable_face_matching=True,
            stash_url=stash_url  # Use Stash if provided
        )
        
        result = service.identify_video(video_path, watermark_patterns)
        
        # Convert watermarks
        watermarks = [
            WatermarkDetectionType(
                text=w.text,
                confidence=w.confidence,
                bbox=json.dumps(list(w.bbox)),
                frame_number=w.frame_number,
                timestamp=w.timestamp
            )
            for w in result.watermarks
        ]
        
        # Convert face matches
        face_matches = [
            FaceMatchType(
                actor_id=f.actor_id,
                actor_name=f.actor_name,
                confidence=f.confidence,
                frame_number=f.frame_number,
                bbox=json.dumps(list(f.bbox))
            )
            for f in result.face_matches
        ]
        
        # Convert scene matches
        scene_matches = [
            SceneMatchType(
                scene_id=s.scene_id,
                scene_title=s.scene_title,
                studio=s.studio,
                actors=s.actors,
                url=s.url,
                confidence=s.confidence,
                match_type=s.match_type
            )
            for s in result.scene_matches
        ]
        
        metadata_str = json.dumps(result.metadata) if result.metadata else None
        
        return VideoIdentificationResultType(
            video_path=result.video_path,
            identified=result.identified,
            studio=result.studio,
            watermarks=watermarks,
            face_matches=face_matches,
            scene_matches=scene_matches,
            metadata=metadata_str
        )


class ImageSearchMutation:
    """GraphQL mutations for reverse image search."""
    
    def __init__(self):
        """Initialize image search mutation handler."""
        self.neo4j = get_connection()
        self.reverse_search = ReverseImageSearch(
            neo4j=self.neo4j,
            enable_vector_search=True,
        )
        self.recovery = SpiderRecovery(
            neo4j=self.neo4j,
            reverse_search=self.reverse_search,
        )
    
    @strawberry.mutation
    def recover_post(self, post_url: str) -> RecoveryResult:
        """
        Recover a missed Reddit post and ingest it into the database.
        
        Useful when spider was down and missed a post.
        """
        result = self.recovery.recover_post(post_url, index_images=True)
        
        return RecoveryResult(
            post_url=result["post_url"],
            success=result["success"],
            post_id=result.get("post_id"),
            images_found=result.get("images_found", 0),
            images_indexed=result.get("images_indexed", 0),
            error=result.get("error"),
        )
    
    @strawberry.mutation
    def index_image(self, image_url: str) -> IndexResult:
        """
        Index an image for future reverse search.
        
        Stores hash values in Neo4j and CLIP embedding in Valkey.
        """
        success = self.reverse_search.index_image(image_url)
        
        # Check if hashes were stored
        query = """
        MATCH (img:Image {url: $url})
        RETURN img.sha256_hash as sha256, img.dhash as dhash
        LIMIT 1
        """
        result = self.neo4j.execute_read(query, parameters={"url": image_url})
        hashes_stored = bool(result and result[0].get("sha256"))
        
        # Check if embedding was stored (if vector search enabled)
        embedding_stored = False
        if self.reverse_search.enable_vector_search and self.reverse_search.valkey:
            key = f"{self.reverse_search.DOC_PREFIX}{image_url}"
            embedding_stored = self.reverse_search.valkey.exists(key)
        
        return IndexResult(
            image_url=image_url,
            success=success,
            hashes_stored=hashes_stored,
            embedding_stored=embedding_stored,
            error=None if success else "Failed to index image",
        )

