"""Temporal versioning manager for crawl history with anchor+delta storage."""

import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from ..storage.neo4j_connection import Neo4jConnection
from .temporal_queries import TemporalQueries


class TemporalVersionManager:
    """Manages versioned crawl history with space-efficient delta storage."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize temporal version manager.
        
        Args:
            neo4j: Neo4j connection instance
        """
        self.neo4j = neo4j
        self.queries = TemporalQueries()
    
    def create_version(
        self,
        url: str,
        crawl_data: Dict[str, Any],
        changed: bool
    ) -> Optional[str]:
        """
        Create a new version if content changed, using delta storage.
        
        Args:
            url: Normalized URL
            crawl_data: Dictionary with crawl metadata (content_hash, http_status, etc.)
            changed: Whether content changed from previous version
            
        Returns:
            Version ID if created, None if skipped (no change)
        """
        # Only create versions when content actually changes
        if not changed:
            return None
        
        version_id = str(uuid.uuid4())
        crawled_at = datetime.utcnow()
        
        # Get previous version to compute delta
        previous_version = self._get_latest_version(url)
        
        # Compute delta (only changed properties)
        delta_properties = self._compute_delta(
            previous_version,
            crawl_data
        )
        
        # Create version node
        query = """
        CREATE (v:CrawlVersion {
            version_id: $version_id,
            normalized_url: $url,
            crawled_at: datetime({epochSeconds: $crawled_at_epoch}),
            content_hash: $content_hash,
            changed: $changed,
            delta_properties: $delta_properties,
            http_status: $http_status,
            content_type: $content_type,
            content_length: $content_length,
            crawl_duration_ms: $crawl_duration_ms,
            simhash: $simhash,
            created_at: datetime()
        })
        RETURN v.version_id as version_id
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "version_id": version_id,
                "url": url,
                "crawled_at_epoch": int(crawled_at.timestamp()),
                "content_hash": crawl_data.get("content_hash"),
                "changed": changed,
                "delta_properties": delta_properties,
                "http_status": crawl_data.get("http_status"),
                "content_type": crawl_data.get("content_type"),
                "content_length": crawl_data.get("content_length"),
                "crawl_duration_ms": crawl_data.get("crawl_duration_ms"),
                "simhash": crawl_data.get("simhash"),
            }
        )
        
        # Link to WebPage
        self.neo4j.execute_write(
            self.queries.create_version_relationship(),
            parameters={
                "url": url,
                "version_id": version_id,
            }
        )
        
        # Link to previous version in chain
        if previous_version:
            prev_version_id = previous_version.get("version_id")
            if prev_version_id:
                self.neo4j.execute_write(
                    self.queries.link_version_chain(prev_version_id, version_id),
                    parameters={
                        "older_version_id": prev_version_id,
                        "newer_version_id": version_id,
                    }
                )
        
        return version_id
    
    def get_version_at(
        self,
        url: str,
        timestamp: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Get page state at specific time (time-slice query).
        
        Args:
            url: Normalized URL
            timestamp: Target datetime
            
        Returns:
            Version record or None
        """
        query = self.queries.get_version_at_time(url, timestamp)
        result = self.neo4j.execute_read(
            query,
            parameters={
                "url": url,
                "target_time_epoch": int(timestamp.timestamp()),
            }
        )
        
        if result:
            version_node = result[0].get("v")
            if version_node:
                return dict(version_node)
        return None
    
    def get_version_history(
        self,
        url: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get version chain for a URL.
        
        Args:
            url: Normalized URL
            limit: Maximum number of versions to return
            
        Returns:
            List of version records
        """
        query = self.queries.get_version_history(url, limit)
        result = self.neo4j.execute_read(
            query,
            parameters={"url": url}
        )
        
        return [dict(record["v"]) for record in result if record.get("v")]
    
    def get_changes_between(
        self,
        url: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get all versions (changes) in time range.
        
        Args:
            url: Normalized URL
            start_time: Start datetime
            end_time: End datetime
            
        Returns:
            List of version records
        """
        query = self.queries.get_versions_in_range(url, start_time, end_time)
        result = self.neo4j.execute_read(
            query,
            parameters={
                "url": url,
                "start_time_epoch": int(start_time.timestamp()),
                "end_time_epoch": int(end_time.timestamp()),
            }
        )
        
        return [dict(record["v"]) for record in result if record.get("v")]
    
    def get_change_frequency(
        self,
        url: str,
        days: int = 30
    ) -> int:
        """
        Calculate change frequency over time period.
        
        Args:
            url: Normalized URL
            days: Number of days to look back
            
        Returns:
            Number of changes in period
        """
        query = self.queries.get_change_frequency(url, days)
        result = self.neo4j.execute_read(
            query,
            parameters={
                "url": url,
                "days": days,
            }
        )
        
        if result:
            return result[0].get("change_count", 0)
        return 0
    
    def get_version_statistics(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Get version statistics for a URL.
        
        Args:
            url: Normalized URL
            
        Returns:
            Dictionary with statistics
        """
        query = self.queries.get_version_statistics(url)
        result = self.neo4j.execute_read(
            query,
            parameters={"url": url}
        )
        
        if result:
            stats = result[0]
            return {
                "version_count": stats.get("version_count", 0),
                "first_version_at": stats.get("first_version_at"),
                "last_version_at": stats.get("last_version_at"),
                "change_count": stats.get("change_count", 0),
            }
        return {
            "version_count": 0,
            "first_version_at": None,
            "last_version_at": None,
            "change_count": 0,
        }
    
    def migrate_old_versions(
        self,
        url: str,
        retention_days: int = 365
    ) -> int:
        """
        Archive or delete versions older than retention period.
        
        Args:
            url: Normalized URL
            retention_days: Days to retain versions
            
        Returns:
            Number of versions archived/deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        query = """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
        WHERE v.crawled_at < datetime({epochSeconds: $cutoff_epoch})
        WITH v
        OPTIONAL MATCH (v)-[r1:HAS_VERSION]-()
        OPTIONAL MATCH (v)-[r2:VERSION_CHAIN]-()
        DELETE r1, r2, v
        RETURN count(v) as deleted_count
        """
        
        result = self.neo4j.execute_write(
            query,
            parameters={
                "url": url,
                "cutoff_epoch": int(cutoff_date.timestamp()),
            }
        )
        
        if result:
            return result[0].get("deleted_count", 0)
        return 0
    
    def _get_latest_version(self, url: str) -> Optional[Dict[str, Any]]:
        """Get the latest version for a URL."""
        query = self.queries.get_latest_version(url)
        result = self.neo4j.execute_read(
            query,
            parameters={"url": url}
        )
        
        if result:
            version_node = result[0].get("v")
            if version_node:
                return dict(version_node)
        return None
    
    def _compute_delta(
        self,
        previous_version: Optional[Dict[str, Any]],
        current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute delta (only changed properties) between versions.
        
        Args:
            previous_version: Previous version record or None
            current_data: Current crawl data
            
        Returns:
            Dictionary with only changed properties
        """
        if not previous_version:
            # First version, store all properties
            return {
                "content_hash": current_data.get("content_hash"),
                "http_status": current_data.get("http_status"),
                "content_type": current_data.get("content_type"),
                "content_length": current_data.get("content_length"),
                "simhash": current_data.get("simhash"),
            }
        
        # Compare and store only changed properties
        delta = {}
        
        # Compare key properties
        key_properties = [
            "content_hash",
            "http_status",
            "content_type",
            "content_length",
            "simhash",
        ]
        
        for prop in key_properties:
            current_value = current_data.get(prop)
            previous_value = previous_version.get(prop)
            
            if current_value != previous_value:
                delta[prop] = current_value
        
        return delta

