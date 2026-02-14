"""Cross-source verification for performer and content matching."""

from typing import List, Dict, Optional, Any
import re
import requests
from bs4 import BeautifulSoup

from ..storage.neo4j_connection import Neo4jConnection
from .adult_content_crawlers import Data18Crawler


class CrossSourceVerifier:
    """Verify and cross-reference content across multiple sources."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize cross-source verifier.
        
        Args:
            neo4j: Neo4j connection
        """
        self.neo4j = neo4j
        self.data18 = Data18Crawler()
    
    def verify_performer_across_sources(
        self,
        performer_name: str,
        sources: List[str]  # ['18eighteen', 'data18', 'planetsuzy', 'stash']
    ) -> Dict[str, Any]:
        """
        Verify performer exists across multiple sources.
        
        Args:
            performer_name: Performer name
            sources: List of sources to check
            
        Returns:
            Dictionary with verification results
        """
        results = {
            "performer_name": performer_name,
            "sources": {}
        }
        
        # Check Data18
        if 'data18' in sources:
            # Try to find performer on Data18
            # Data18 format: https://www.data18.com/name/natalie-monroe
            slug = performer_name.lower().replace(' ', '-')
            data18_url = f"https://www.data18.com/name/{slug}"
            
            try:
                response = requests.get(data18_url, timeout=10)
                found = response.status_code == 200
                results["sources"]["data18"] = {
                    "found": found,
                    "url": data18_url if found else None,
                    "performer_id": slug if found else None
                }
            except:
                results["sources"]["data18"] = {
                    "found": False,
                    "url": None,
                    "performer_id": None
                }
        
        # Check Neo4j
        query = """
        MATCH (p:Performer {name: $name})
        OPTIONAL MATCH (p)-[:APPEARS_IN]->(s:Scene)
        OPTIONAL MATCH (p)-[:WANTED]->(w:Wanted)
        RETURN 
            count(DISTINCT s) as scene_count,
            count(DISTINCT w) as wanted_count
        """
        
        neo4j_result = self.neo4j.execute_read(
            query,
            parameters={"name": performer_name}
        )
        
        if neo4j_result:
            record = neo4j_result[0]
            results["sources"]["neo4j"] = {
                "found": True,
                "scene_count": record.get("scene_count", 0),
                "wanted_count": record.get("wanted_count", 0)
            }
        else:
            results["sources"]["neo4j"] = {
                "found": False,
                "scene_count": 0,
                "wanted_count": 0
            }
        
        return results
    
    def check_18eighteen_to_data18_mapping(
        self,
        performer_name: str,
        eighteen_url: str
    ) -> Dict[str, Any]:
        """
        Check if 18eighteen.com performer maps to data18.com.
        
        Args:
            performer_name: Performer name
            eighteen_url: 18eighteen.com URL
            
        Returns:
            Mapping result
        """
        # Extract performer slug from 18eighteen URL
        # Format: https://www.18eighteen.com/nude-teen-photos/Natalie-Monroe/43308/
        slug_match = re.search(r'/([^/]+)/\d+', eighteen_url)
        slug = slug_match.group(1) if slug_match else None
        
        # Try to find in Data18
        # Data18 format: https://www.data18.com/name/natalie-monroe
        data18_slug = slug.lower().replace(' ', '-') if slug else None
        data18_url = f"https://www.data18.com/name/{data18_slug}" if data18_slug else None
        
        # Verify Data18 URL exists
        data18_found = False
        if data18_url:
            try:
                response = requests.get(data18_url, timeout=10)
                data18_found = response.status_code == 200
            except:
                pass
        
        return {
            "performer_name": performer_name,
            "18eighteen_url": eighteen_url,
            "data18_url": data18_url,
            "data18_slug": data18_slug,
            "mapping_possible": data18_url is not None,
            "data18_found": data18_found
        }




