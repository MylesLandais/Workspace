"""Analytics and monitoring for temporal versioning system."""

from typing import Dict, List, Any
from datetime import datetime, timedelta

from ..storage.neo4j_connection import Neo4jConnection
from .temporal import TemporalVersionManager


class TemporalAnalytics:
    """Analytics and monitoring for temporal versioning."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize temporal analytics.
        
        Args:
            neo4j: Neo4j connection instance
        """
        self.neo4j = neo4j
        self.temporal_manager = TemporalVersionManager(neo4j)
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics for versioning system.
        
        Returns:
            Dictionary with storage metrics
        """
        query = """
        MATCH (v:CrawlVersion)
        RETURN count(v) as total_versions,
               count(DISTINCT v.normalized_url) as unique_pages,
               avg(size(v.delta_properties)) as avg_delta_size,
               min(v.crawled_at) as oldest_version,
               max(v.crawled_at) as newest_version
        """
        
        result = self.neo4j.execute_read(query)
        
        if result:
            stats = result[0]
            return {
                "total_versions": stats.get("total_versions", 0),
                "unique_pages": stats.get("unique_pages", 0),
                "avg_delta_size": stats.get("avg_delta_size", 0),
                "oldest_version": stats.get("oldest_version"),
                "newest_version": stats.get("newest_version"),
            }
        
        return {
            "total_versions": 0,
            "unique_pages": 0,
            "avg_delta_size": 0,
            "oldest_version": None,
            "newest_version": None,
        }
    
    def get_change_frequency_analysis(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze change frequency patterns.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with change frequency metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
        MATCH (v:CrawlVersion)
        WHERE v.crawled_at >= datetime({epochSeconds: $cutoff_epoch})
        WITH v.normalized_url as url, count(v) as version_count
        RETURN avg(version_count) as avg_versions_per_page,
               max(version_count) as max_versions_per_page,
               min(version_count) as min_versions_per_page,
               percentileCont(version_count, 0.5) as median_versions_per_page
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"cutoff_epoch": int(cutoff_date.timestamp())}
        )
        
        if result:
            stats = result[0]
            return {
                "avg_versions_per_page": stats.get("avg_versions_per_page", 0),
                "max_versions_per_page": stats.get("max_versions_per_page", 0),
                "min_versions_per_page": stats.get("min_versions_per_page", 0),
                "median_versions_per_page": stats.get("median_versions_per_page", 0),
            }
        
        return {
            "avg_versions_per_page": 0,
            "max_versions_per_page": 0,
            "min_versions_per_page": 0,
            "median_versions_per_page": 0,
        }
    
    def get_query_performance_metrics(self) -> Dict[str, Any]:
        """
        Get query performance metrics (placeholder for future implementation).
        
        Returns:
            Dictionary with performance metrics
        """
        # This would require query logging/monitoring infrastructure
        # For now, return placeholder
        return {
            "time_slice_query_avg_ms": None,
            "version_history_query_avg_ms": None,
            "change_frequency_query_avg_ms": None,
        }
    
    def get_version_chain_health(self, url: str) -> Dict[str, Any]:
        """
        Check health of version chain for a URL.
        
        Args:
            url: Normalized URL
            
        Returns:
            Dictionary with chain health metrics
        """
        stats = self.temporal_manager.get_version_statistics(url)
        versions = self.temporal_manager.get_version_history(url, limit=100)
        
        # Check for gaps in version chain
        gaps = []
        if len(versions) > 1:
            for i in range(1, len(versions)):
                try:
                    prev_time = versions[i-1].get("crawled_at")
                    curr_time = versions[i].get("crawled_at")
                    
                    if isinstance(prev_time, str):
                        from dateutil import parser
                        prev_time = parser.parse(prev_time)
                        curr_time = parser.parse(curr_time)
                    
                    if prev_time and curr_time:
                        gap_days = (curr_time - prev_time).total_seconds() / 86400
                        if gap_days > 90:  # Large gap
                            gaps.append({
                                "from": prev_time,
                                "to": curr_time,
                                "days": gap_days,
                            })
                except Exception:
                    pass
        
        return {
            "version_count": stats["version_count"],
            "change_count": stats["change_count"],
            "chain_gaps": len(gaps),
            "largest_gap_days": max([g["days"] for g in gaps], default=0) if gaps else 0,
            "first_version": stats["first_version_at"],
            "last_version": stats["last_version_at"],
        }
    
    def get_top_changing_pages(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get pages with most changes in time period.
        
        Args:
            limit: Maximum number of pages to return
            days: Number of days to analyze
            
        Returns:
            List of page records with change counts
        """
        query = """
        MATCH (w:WebPage)-[:HAS_VERSION]->(v:CrawlVersion)
        WHERE v.crawled_at >= datetime() - duration({days: $days})
        AND v.changed = true
        WITH w, count(v) as change_count
        RETURN w.normalized_url as url,
               w.domain as domain,
               change_count,
               w.last_crawled_at as last_crawled
        ORDER BY change_count DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"days": days, "limit": limit}
        )
        
        return [dict(record) for record in result]
    
    def estimate_space_savings(self) -> Dict[str, Any]:
        """
        Estimate space savings from delta storage vs full snapshots.
        
        Returns:
            Dictionary with space savings estimates
        """
        query = """
        MATCH (v:CrawlVersion)
        WITH v,
             size(v.delta_properties) as delta_size,
             CASE 
               WHEN v.delta_properties IS NULL THEN 0
               ELSE 10  // Estimated full snapshot size (properties)
             END as full_size
        RETURN sum(delta_size) as total_delta_size,
               sum(full_size) as estimated_full_size,
               count(v) as version_count
        """
        
        result = self.neo4j.execute_read(query)
        
        if result:
            stats = result[0]
            total_delta = stats.get("total_delta_size", 0)
            estimated_full = stats.get("estimated_full_size", 0)
            version_count = stats.get("version_count", 0)
            
            if estimated_full > 0:
                savings_ratio = estimated_full / total_delta if total_delta > 0 else 1.0
                savings_percent = ((estimated_full - total_delta) / estimated_full * 100) if estimated_full > 0 else 0
            else:
                savings_ratio = 1.0
                savings_percent = 0.0
            
            return {
                "total_delta_size": total_delta,
                "estimated_full_size": estimated_full,
                "version_count": version_count,
                "savings_ratio": savings_ratio,
                "savings_percent": savings_percent,
            }
        
        return {
            "total_delta_size": 0,
            "estimated_full_size": 0,
            "version_count": 0,
            "savings_ratio": 1.0,
            "savings_percent": 0.0,
        }

