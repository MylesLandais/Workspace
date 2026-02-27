"""Wanted metadata tracking for missing content."""

from typing import List, Dict, Optional, Any
from ..storage.neo4j_connection import Neo4jConnection


class WantedMetadataTracker:
    """Track "wanted" metadata for missing content."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize wanted metadata tracker.
        
        Args:
            neo4j: Neo4j connection
        """
        self.neo4j = neo4j
    
    def create_wanted_entry(
        self,
        performer_name: str,
        source_url: str,
        source_type: str,  # '18eighteen', 'data18', 'forum', etc.
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a "wanted" entry for missing content.
        
        Args:
            performer_name: Performer name
            source_url: Source URL where content was found
            source_type: Type of source
            metadata: Additional metadata
            
        Returns:
            Wanted entry ID
        """
        query = """
        MERGE (w:Wanted {source_url: $source_url})
        ON CREATE SET
            w.uuid = randomUUID(),
            w.performer_name = $performer_name,
            w.source_url = $source_url,
            w.source_type = $source_type,
            w.status = 'missing',
            w.created_at = datetime(),
            w.updated_at = datetime()
        ON MATCH SET
            w.updated_at = datetime()
        WITH w
        MERGE (p:Performer {name: $performer_name})
        ON CREATE SET
            p.uuid = randomUUID(),
            p.name = $performer_name,
            p.created_at = datetime()
        MERGE (p)-[:WANTED]->(w)
        RETURN w.uuid as uuid
        """
        
        result = self.neo4j.execute_write(
            query,
            parameters={
                "performer_name": performer_name,
                "source_url": source_url,
                "source_type": source_type,
                "metadata": str(metadata) if metadata else None
            }
        )
        
        if result:
            return result[0]["uuid"]
        return ""
    
    def cross_reference_sources(
        self,
        performer_name: str
    ) -> Dict[str, Any]:
        """
        Cross-reference performer across multiple sources.
        
        Args:
            performer_name: Performer name to check
            
        Returns:
            Dictionary with matches from different sources
        """
        query = """
        MATCH (p:Performer {name: $name})
        OPTIONAL MATCH (p)-[:WANTED]->(w:Wanted)
        OPTIONAL MATCH (p)-[:APPEARS_IN]->(s:Scene)
        OPTIONAL MATCH (s)-[:FROM_STUDIO]->(st:Studio)
        RETURN 
            collect(DISTINCT w.source_url) as wanted_sources,
            collect(DISTINCT s.scene_id) as scene_ids,
            collect(DISTINCT st.slug) as studios
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"name": performer_name}
        )
        
        if result:
            record = result[0]
            return {
                "performer_name": performer_name,
                "wanted_sources": record.get("wanted_sources", []),
                "scene_ids": record.get("scene_ids", []),
                "studios": record.get("studios", []),
                "has_content": len(record.get("scene_ids", [])) > 0,
                "is_wanted": len(record.get("wanted_sources", [])) > 0
            }
        
        return {
            "performer_name": performer_name,
            "wanted_sources": [],
            "scene_ids": [],
            "studios": [],
            "has_content": False,
            "is_wanted": False
        }
    
    def link_forum_thread_to_wanted(
        self,
        thread_url: str,
        performer_name: str
    ) -> bool:
        """
        Link a forum thread to a wanted entry.
        
        Args:
            thread_url: Forum thread URL
            performer_name: Performer name
            
        Returns:
            True if linked successfully
        """
        query = """
        MATCH (p:Performer {name: $performer_name})
        MATCH (p)-[:WANTED]->(w:Wanted)
        MERGE (t:ForumThread {url: $thread_url})
        ON CREATE SET
            t.uuid = randomUUID(),
            t.url = $thread_url,
            t.created_at = datetime()
        MERGE (w)-[:DISCUSSED_IN]->(t)
        RETURN w.uuid as uuid
        """
        
        result = self.neo4j.execute_write(
            query,
            parameters={
                "performer_name": performer_name,
                "thread_url": thread_url
            }
        )
        
        return bool(result)




