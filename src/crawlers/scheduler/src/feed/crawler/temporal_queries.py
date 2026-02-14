"""Cypher query builders for temporal versioning queries."""

from typing import Optional
from datetime import datetime


class TemporalQueries:
    """Query builders for temporal versioning operations."""
    
    @staticmethod
    def get_latest_version(url: str) -> str:
        """
        Get the latest version for a WebPage.
        
        Args:
            url: Normalized URL
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
        RETURN v
        ORDER BY v.crawled_at DESC
        LIMIT 1
        """
    
    @staticmethod
    def get_version_at_time(url: str, target_time: datetime) -> str:
        """
        Get version at specific time (time-slice query).
        
        Args:
            url: Normalized URL
            target_time: Target datetime
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
        WHERE v.crawled_at <= datetime({epochSeconds: $target_time_epoch})
        RETURN v
        ORDER BY v.crawled_at DESC
        LIMIT 1
        """
    
    @staticmethod
    def get_version_history(url: str, limit: Optional[int] = None) -> str:
        """
        Get version history in chronological order.
        
        Args:
            url: Normalized URL
            limit: Maximum number of versions to return
            
        Returns:
            Cypher query string
        """
        limit_clause = f"LIMIT {limit}" if limit else ""
        return f"""
        MATCH (w:WebPage {{normalized_url: $url}})-[:HAS_VERSION]->(v:CrawlVersion)
        RETURN v
        ORDER BY v.crawled_at ASC
        {limit_clause}
        """
    
    @staticmethod
    def get_versions_in_range(
        url: str,
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """
        Get versions in time range.
        
        Args:
            url: Normalized URL
            start_time: Start datetime
            end_time: End datetime
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
        WHERE v.crawled_at >= datetime({epochSeconds: $start_time_epoch})
        AND v.crawled_at <= datetime({epochSeconds: $end_time_epoch})
        RETURN v
        ORDER BY v.crawled_at ASC
        """
    
    @staticmethod
    def get_change_frequency(url: str, days: int) -> str:
        """
        Get change frequency (count of versions with changed=true) in time period.
        
        Args:
            url: Normalized URL
            days: Number of days to look back
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
        WHERE v.changed = true
        AND v.crawled_at >= datetime() - duration({days: $days})
        RETURN count(v) as change_count
        """
    
    @staticmethod
    def get_version_chain(url: str) -> str:
        """
        Get version chain with VERSION_CHAIN relationships.
        
        Args:
            url: Normalized URL
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v1:CrawlVersion)
        OPTIONAL MATCH path = (v1)-[:VERSION_CHAIN*0..]->(v2:CrawlVersion)
        RETURN v1, path
        ORDER BY v1.crawled_at ASC
        """
    
    @staticmethod
    def get_version_statistics(url: str) -> str:
        """
        Get version statistics (count, first, last).
        
        Args:
            url: Normalized URL
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
        RETURN count(v) as version_count,
               min(v.crawled_at) as first_version_at,
               max(v.crawled_at) as last_version_at,
               sum(CASE WHEN v.changed = true THEN 1 ELSE 0 END) as change_count
        """
    
    @staticmethod
    def create_version_relationship() -> str:
        """
        Create HAS_VERSION relationship between WebPage and CrawlVersion.
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (w:WebPage {normalized_url: $url})
        MATCH (v:CrawlVersion {version_id: $version_id})
        MERGE (w)-[r:HAS_VERSION]->(v)
        ON CREATE SET r.created_at = datetime()
        RETURN r
        """
    
    @staticmethod
    def link_version_chain(older_version_id: str, newer_version_id: str) -> str:
        """
        Link two versions in chronological chain.
        
        Args:
            older_version_id: ID of older version
            newer_version_id: ID of newer version
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (v1:CrawlVersion {version_id: $older_version_id})
        MATCH (v2:CrawlVersion {version_id: $newer_version_id})
        MERGE (v1)-[r:VERSION_CHAIN]->(v2)
        ON CREATE SET r.created_at = datetime()
        RETURN r
        """
    
    @staticmethod
    def get_changes_between_versions(version1_id: str, version2_id: str) -> str:
        """
        Get delta properties between two versions.
        
        Args:
            version1_id: First version ID
            version2_id: Second version ID
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (v1:CrawlVersion {version_id: $version1_id})
        MATCH (v2:CrawlVersion {version_id: $version2_id})
        RETURN v1.delta_properties as delta1,
               v2.delta_properties as delta2,
               v1.crawled_at as time1,
               v2.crawled_at as time2
        """
    
    @staticmethod
    def get_all_versions_with_changes(url: str, limit: Optional[int] = None) -> str:
        """
        Get all versions where content changed.
        
        Args:
            url: Normalized URL
            limit: Maximum number of versions to return
            
        Returns:
            Cypher query string
        """
        limit_clause = f"LIMIT {limit}" if limit else ""
        return f"""
        MATCH (w:WebPage {{normalized_url: $url}})-[:HAS_VERSION]->(v:CrawlVersion)
        WHERE v.changed = true
        RETURN v
        ORDER BY v.crawled_at DESC
        {limit_clause}
        """

