"""Duplicate detection for URLs and content."""

from typing import Optional, Set, List, Dict
from collections import defaultdict

from ..storage.neo4j_connection import Neo4jConnection
from .content import ContentAnalyzer, Simhash
from .frontier import URLNormalizer
from .temporal import TemporalVersionManager


class DuplicateDetector:
    """Detects duplicate URLs and near-duplicate content."""
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        simhash_threshold: int = 3,
        use_temporal_versioning: bool = True
    ):
        """
        Initialize duplicate detector.
        
        Args:
            neo4j: Neo4j connection instance
            simhash_threshold: Hamming distance threshold for near-duplicates
            use_temporal_versioning: Whether to use temporal versioning for history
        """
        self.neo4j = neo4j
        self.simhash_threshold = simhash_threshold
        self.normalizer = URLNormalizer()
        self.content_analyzer = ContentAnalyzer()
        self.use_temporal_versioning = use_temporal_versioning
        if use_temporal_versioning:
            self.temporal_manager = TemporalVersionManager(neo4j)
        else:
            self.temporal_manager = None
    
    def is_url_visited(self, url: str) -> bool:
        """
        Check if URL has been visited (exists in database).
        
        Args:
            url: URL to check
            
        Returns:
            True if URL exists
        """
        normalized = self.normalizer.normalize(url)
        
        query = """
        MATCH (w:WebPage {normalized_url: $normalized_url})
        RETURN w.normalized_url as url
        LIMIT 1
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"normalized_url": normalized}
        )
        
        return len(result) > 0
    
    def find_near_duplicates_by_content(
        self,
        content_hash: str,
        simhash: Optional[int],
        limit: int = 10
    ) -> List[Dict]:
        """
        Find near-duplicate pages by content hash or simhash.
        
        Args:
            content_hash: SHA-256 content hash
            simhash: Simhash value (optional)
            limit: Maximum results to return
            
        Returns:
            List of duplicate page records
        """
        duplicates = []
        
        # First check for exact matches by content hash
        if content_hash:
            query = """
            MATCH (w:WebPage {content_hash: $content_hash})
            WHERE w.normalized_url <> $exclude_url
            RETURN w.normalized_url as url,
                   w.content_hash as hash,
                   w.last_crawled_at as last_crawled
            LIMIT $limit
            """
            result = self.neo4j.execute_read(
                query,
                parameters={
                    "content_hash": content_hash,
                    "exclude_url": "",  # Will be set by caller if needed
                    "limit": limit
                }
            )
            duplicates.extend([dict(record) for record in result])
        
        # Then check for near-duplicates by simhash
        if simhash is not None and len(duplicates) < limit:
            # Note: Neo4j doesn't have built-in Hamming distance,
            # so we'll fetch candidates and filter in Python
            # For production, consider using APOC procedures or
            # storing simhash in a way that allows efficient querying
            
            query = """
            MATCH (w:WebPage)
            WHERE w.simhash IS NOT NULL
            AND w.normalized_url <> $exclude_url
            RETURN w.normalized_url as url,
                   w.simhash as simhash,
                   w.last_crawled_at as last_crawled
            LIMIT 1000
            """
            candidates = self.neo4j.execute_read(
                query,
                parameters={"exclude_url": ""}
            )
            
            # Filter by Hamming distance
            for record in candidates:
                candidate_simhash = record.get("simhash")
                if candidate_simhash is None:
                    continue
                
                # Convert string to int if needed
                if isinstance(candidate_simhash, str):
                    try:
                        candidate_simhash = int(candidate_simhash)
                    except ValueError:
                        continue
                
                distance = Simhash.hamming_distance(simhash, candidate_simhash)
                if distance <= self.simhash_threshold:
                    duplicates.append({
                        "url": record["url"],
                        "simhash": candidate_simhash,
                        "last_crawled": record.get("last_crawled"),
                        "hamming_distance": distance,
                    })
                    
                    if len(duplicates) >= limit:
                        break
        
        return duplicates
    
    def check_and_store_content(
        self,
        url: str,
        content: str,
        exclude_url: Optional[str] = None
    ) -> Dict:
        """
        Check for duplicates and store content hash.
        
        Args:
            url: Normalized URL
            content: Page content
            exclude_url: URL to exclude from duplicate check (self)
            
        Returns:
            Dictionary with duplicate detection results
        """
        normalized = self.normalizer.normalize(url)
        content_hash = self.content_analyzer.compute_content_hash(content)
        simhash = self.content_analyzer.compute_simhash(content)
        
        # Check for duplicates
        near_duplicates = self.find_near_duplicates_by_content(
            content_hash,
            simhash,
            limit=5
        )
        
        # Store content hash in database
        query = """
        MATCH (w:WebPage {normalized_url: $url})
        SET w.content_hash = $content_hash,
            w.simhash = $simhash,
            w.updated_at = datetime()
        RETURN w
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "url": normalized,
                "content_hash": content_hash,
                "simhash": str(simhash) if simhash is not None else None,
            }
        )
        
        return {
            "is_duplicate": len(near_duplicates) > 0,
            "exact_match": any(d.get("hash") == content_hash for d in near_duplicates),
            "near_duplicates": near_duplicates,
            "content_hash": content_hash,
            "simhash": simhash,
        }
    
    def get_visited_urls_batch(self, urls: List[str]) -> Set[str]:
        """
        Check which URLs in a batch have been visited.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Set of normalized URLs that have been visited
        """
        if not urls:
            return set()
        
        normalized_urls = [self.normalizer.normalize(url) for url in urls]
        
        query = """
        MATCH (w:WebPage)
        WHERE w.normalized_url IN $urls
        RETURN w.normalized_url as url
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"urls": normalized_urls}
        )
        
        return {record["url"] for record in result}
    
    def record_crawl_history(
        self,
        url: str,
        http_status: int,
        content_hash: str,
        changed: bool,
        content_length: Optional[int] = None,
        crawl_duration_ms: Optional[int] = None,
        simhash: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Record crawl history for a page using temporal versioning.
        
        Args:
            url: Normalized URL
            http_status: HTTP status code
            content_hash: Content hash
            changed: Whether content changed
            content_length: Content length in bytes
            crawl_duration_ms: Crawl duration in milliseconds
            simhash: Simhash value (optional)
            content_type: Content type (optional)
            
        Returns:
            Version ID if created, None otherwise
        """
        if self.use_temporal_versioning and self.temporal_manager:
            # Use temporal versioning (creates versions only when changed)
            crawl_data = {
                "content_hash": content_hash,
                "http_status": http_status,
                "content_length": content_length,
                "crawl_duration_ms": crawl_duration_ms,
                "simhash": str(simhash) if simhash is not None else None,
                "content_type": content_type,
            }
            
            version_id = self.temporal_manager.create_version(
                url,
                crawl_data,
                changed
            )
            
            # Also maintain backward compatibility with CRAWLED_AT relationship
            # for existing code that might query it
            query = """
            MATCH (w:WebPage {normalized_url: $url})
            CREATE (w)-[r:CRAWLED_AT {
                crawled_at: datetime(),
                http_status: $http_status,
                content_hash: $content_hash,
                changed: $changed,
                content_length: $content_length,
                crawl_duration_ms: $crawl_duration_ms
            }]
            RETURN r
            """
            
            self.neo4j.execute_write(
                query,
                parameters={
                    "url": url,
                    "http_status": http_status,
                    "content_hash": content_hash,
                    "changed": changed,
                    "content_length": content_length,
                    "crawl_duration_ms": crawl_duration_ms,
                }
            )
            
            return version_id
        else:
            # Fallback to original CRAWLED_AT relationship
            query = """
            MATCH (w:WebPage {normalized_url: $url})
            CREATE (w)-[r:CRAWLED_AT {
                crawled_at: datetime(),
                http_status: $http_status,
                content_hash: $content_hash,
                changed: $changed,
                content_length: $content_length,
                crawl_duration_ms: $crawl_duration_ms
            }]
            RETURN r
            """
            
            self.neo4j.execute_write(
                query,
                parameters={
                    "url": url,
                    "http_status": http_status,
                    "content_hash": content_hash,
                    "changed": changed,
                    "content_length": content_length,
                    "crawl_duration_ms": crawl_duration_ms,
                }
            )
            return None

