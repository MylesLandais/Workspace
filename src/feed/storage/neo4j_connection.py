"""Neo4j database connection management for feed engine."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session


class Neo4jConnection:
    """Manages Neo4j database connections using environment variables."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize Neo4j connection.
        
        Args:
            env_path: Path to .env file. Defaults to ~/workspace/.env
        """
        # Support both Docker container and local development
        if env_path:
            self.env_path = env_path
        elif Path("/home/jovyan/workspaces/.env").exists():
            self.env_path = Path("/home/jovyan/workspaces/.env")
        elif Path(".env").exists():
            self.env_path = Path(".env").absolute()
        else:
            self.env_path = Path.home() / "Workspace" / "jupyter" / ".env"
        self._load_environment()
        
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.uri:
            raise ValueError("NEO4J_URI is missing! Check the .env file path.")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD is missing! Check the .env file path.")
        
        self._driver: Optional[Driver] = None

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        load_dotenv(self.env_path, override=True)

    def connect(self) -> Driver:
        """
        Create and return a Neo4j driver instance.
        
        Returns:
            Neo4j Driver instance
        """
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            self._driver.verify_connectivity()
        return self._driver

    def get_session(self, **kwargs) -> Session:
        """
        Get a Neo4j session.
        
        Args:
            **kwargs: Additional session parameters (e.g., database="neo4j")
        
        Returns:
            Neo4j Session instance
        """
        driver = self.connect()
        return driver.session(**kwargs)

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[dict] = None,
        database: str = "neo4j"
    ) -> list:
        """Execute a Cypher query and return results."""
        with self.get_session(database=database) as session:
            result = session.run(query, parameters or {})
            return [record for record in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[dict] = None,
        database: str = "neo4j"
    ) -> list:
        """Execute a write transaction."""
        with self.get_session(database=database) as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return result

    def execute_read(
        self,
        query: str,
        parameters: Optional[dict] = None,
        database: str = "neo4j"
    ) -> list:
        """Execute a read transaction."""
        with self.get_session(database=database) as session:
            result = session.execute_read(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return result
    
    # Crawler-specific query helpers
    
    def get_webpage(self, normalized_url: str) -> Optional[dict]:
        """
        Get a WebPage node by normalized URL.
        
        Args:
            normalized_url: Normalized URL
            
        Returns:
            WebPage record or None
        """
        query = """
        MATCH (w:WebPage {normalized_url: $url})
        RETURN w
        LIMIT 1
        """
        result = self.execute_read(query, parameters={"url": normalized_url})
        if result:
            return dict(result[0]["w"])
        return None
    
    def get_webpages_due_for_crawl(self, limit: int = 100) -> list:
        """
        Get WebPages that are due for crawling.
        
        Args:
            limit: Maximum number of pages to return
            
        Returns:
            List of WebPage records
        """
        query = """
        MATCH (w:WebPage)
        WHERE w.next_crawl_at IS NOT NULL 
        AND w.next_crawl_at <= datetime()
        AND w.robots_allowed = true
        RETURN w.normalized_url as url,
               w.domain as domain,
               w.next_crawl_at as next_crawl_at,
               w.crawl_interval_days as interval
        ORDER BY w.next_crawl_at ASC
        LIMIT $limit
        """
        return self.execute_read(query, parameters={"limit": limit})
    
    def update_webpage_crawl_metadata(
        self,
        normalized_url: str,
        http_status: Optional[int] = None,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
        crawl_duration_ms: Optional[int] = None,
    ) -> None:
        """
        Update crawl metadata for a WebPage.
        
        Args:
            normalized_url: Normalized URL
            http_status: HTTP status code
            content_type: Content type
            content_length: Content length in bytes
            crawl_duration_ms: Crawl duration in milliseconds
        """
        updates = []
        params = {"url": normalized_url}
        
        if http_status is not None:
            updates.append("w.http_status = $http_status")
            params["http_status"] = http_status
        
        if content_type is not None:
            updates.append("w.content_type = $content_type")
            params["content_type"] = content_type
        
        if content_length is not None:
            updates.append("w.content_length = $content_length")
            params["content_length"] = content_length
        
        if crawl_duration_ms is not None:
            updates.append("w.crawl_duration_ms = $crawl_duration_ms")
            params["crawl_duration_ms"] = crawl_duration_ms
        
        if not updates:
            return
        
        query = f"""
        MATCH (w:WebPage {{normalized_url: $url}})
        SET {', '.join(updates)},
            w.last_crawled_at = datetime(),
            w.updated_at = datetime()
        """
        self.execute_write(query, parameters=params)
    
    def get_crawl_history(self, normalized_url: str, limit: int = 10) -> list:
        """
        Get crawl history for a WebPage.
        
        Args:
            normalized_url: Normalized URL
            limit: Maximum number of history records
            
        Returns:
            List of crawl history records
        """
        query = """
        MATCH (w:WebPage {normalized_url: $url})-[r:CRAWLED_AT]->()
        RETURN r.crawled_at as crawled_at,
               r.http_status as http_status,
               r.content_hash as content_hash,
               r.changed as changed,
               r.content_length as content_length,
               r.crawl_duration_ms as crawl_duration_ms
        ORDER BY r.crawled_at DESC
        LIMIT $limit
        """
        return self.execute_read(query, parameters={"url": normalized_url, "limit": limit})
    
    def get_webpages_by_domain(self, domain: str, limit: int = 100) -> list:
        """
        Get WebPages for a specific domain.
        
        Args:
            domain: Domain name
            limit: Maximum number of pages to return
            
        Returns:
            List of WebPage records
        """
        query = """
        MATCH (w:WebPage {domain: $domain})
        RETURN w.normalized_url as url,
               w.next_crawl_at as next_crawl_at,
               w.last_crawled_at as last_crawled_at
        ORDER BY w.next_crawl_at ASC
        LIMIT $limit
        """
        return self.execute_read(query, parameters={"domain": domain, "limit": limit})
    
    def purge_stale_webpages(
        self,
        max_failures: int = 5,
        stale_days: int = 365,
    ) -> int:
        """
        Purge stale WebPages (404s, unreachable, old).
        
        Args:
            max_failures: Maximum consecutive failures before purging
            stale_days: Days since last successful crawl before purging
            
        Returns:
            Number of pages purged
        """
        query = """
        MATCH (w:WebPage)
        WHERE (w.http_status = 404 OR w.http_status >= 500)
        OR (w.last_crawled_at IS NULL AND w.created_at < datetime() - duration({days: $stale_days}))
        OR (w.last_crawled_at IS NOT NULL AND w.last_crawled_at < datetime() - duration({days: $stale_days}))
        WITH w, count{(w)-[:CRAWLED_AT]->(r) WHERE r.http_status >= 400} as failure_count
        WHERE failure_count >= $max_failures
        DETACH DELETE w
        RETURN count(w) as purged
        """
        result = self.execute_write(
            query,
            parameters={"max_failures": max_failures, "stale_days": stale_days}
        )
        if result:
            return result[0].get("purged", 0)
        return 0
    
    # Temporal versioning query helpers
    
    def get_webpage_at_time(
        self,
        normalized_url: str,
        timestamp: datetime
    ) -> Optional[dict]:
        """
        Get WebPage state at specific time using time-slice query.
        
        Args:
            normalized_url: Normalized URL
            timestamp: Target datetime
            
        Returns:
            WebPage state at that time or None
        """
        from ..crawler.temporal_queries import TemporalQueries
        
        queries = TemporalQueries()
        query = queries.get_version_at_time(normalized_url, timestamp)
        
        result = self.execute_read(
            query,
            parameters={
                "url": normalized_url,
                "target_time_epoch": int(timestamp.timestamp()),
            }
        )
        
        if result:
            version_node = result[0].get("v")
            if version_node:
                return dict(version_node)
        return None
    
    def get_crawl_versions(
        self,
        normalized_url: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> list:
        """
        Get crawl versions in time range.
        
        Args:
            normalized_url: Normalized URL
            start_time: Start datetime (optional)
            end_time: End datetime (optional)
            
        Returns:
            List of version records
        """
        from ..crawler.temporal_queries import TemporalQueries
        
        queries = TemporalQueries()
        
        if start_time and end_time:
            query = queries.get_versions_in_range(normalized_url, start_time, end_time)
            result = self.execute_read(
                query,
                parameters={
                    "url": normalized_url,
                    "start_time_epoch": int(start_time.timestamp()),
                    "end_time_epoch": int(end_time.timestamp()),
                }
            )
        else:
            query = queries.get_version_history(normalized_url)
            result = self.execute_read(
                query,
                parameters={"url": normalized_url}
            )
        
        return [dict(record["v"]) for record in result if record.get("v")]
    
    def get_change_frequency(
        self,
        normalized_url: str,
        days: int = 30
    ) -> int:
        """
        Calculate change frequency over time period.
        
        Args:
            normalized_url: Normalized URL
            days: Number of days to look back
            
        Returns:
            Number of changes in period
        """
        from ..crawler.temporal_queries import TemporalQueries
        
        queries = TemporalQueries()
        query = queries.get_change_frequency(normalized_url, days)
        
        result = self.execute_read(
            query,
            parameters={
                "url": normalized_url,
                "days": days,
            }
        )
        
        if result:
            return result[0].get("change_count", 0)
        return 0
    
    def get_version_statistics(
        self,
        normalized_url: str
    ) -> dict:
        """
        Get version statistics for a URL.
        
        Args:
            normalized_url: Normalized URL
            
        Returns:
            Dictionary with statistics
        """
        from ..crawler.temporal_queries import TemporalQueries
        
        queries = TemporalQueries()
        query = queries.get_version_statistics(normalized_url)
        
        result = self.execute_read(
            query,
            parameters={"url": normalized_url}
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


# Global connection instance (singleton pattern)
_connection: Optional[Neo4jConnection] = None


def get_connection(env_path: Optional[Path] = None) -> Neo4jConnection:
    """
    Get or create a global Neo4j connection instance.
    
    Args:
        env_path: Path to .env file
    
    Returns:
        Neo4jConnection instance
    """
    global _connection
    if _connection is None:
        _connection = Neo4jConnection(env_path)
    return _connection

