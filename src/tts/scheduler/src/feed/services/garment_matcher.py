"""Service for matching garment images to e-commerce products using ontology."""

from typing import List, Dict, Optional, Any
from uuid import uuid4
from datetime import datetime

from ..storage.neo4j_connection import Neo4jConnection
from ..ontology.garment_ontology import (
    GarmentOntology,
    GarmentCategory,
    BottomType,
    YogaPantStyle,
)
from ..storage.product_storage import ProductStorage


class GarmentMatcher:
    """Matches garment images to e-commerce products using graph ontology."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize garment matcher.
        
        Args:
            neo4j: Neo4j connection instance
        """
        self.neo4j = neo4j
        self.ontology = GarmentOntology()
        self.product_storage = ProductStorage(neo4j)
    
    def analyze_and_match_image(
        self,
        image_url: str,
        image_analysis: Dict[str, Any],
        post_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze an image, create/update garment style ontology, and match to products.
        
        Args:
            image_url: URL of the image
            image_analysis: Computer vision analysis results with:
                - garment_type: str
                - color: str
                - panel_type: str (optional)
                - fit: str (optional)
                - length: str (optional)
                - material: str (optional)
                - features: List[str] (optional)
            post_id: Optional Reddit post ID if image is from a post
        
        Returns:
            Dict with style_id, matched_products, tracking_links
        """
        # Create style from analysis
        style_data = self.ontology.create_style_from_image_analysis(image_analysis)
        style_features = self.ontology.extract_style_features(image_analysis)
        
        # Create or update GarmentStyle node
        style_id = self._create_or_update_style(style_data, style_features)
        
        # Link image to style
        if post_id:
            self._link_image_to_style(image_url, style_id, post_id)
        
        # Match to existing products
        matched_products = self._match_style_to_products(style_id, style_data)
        
        # Create marketplace search links
        search_links = self._create_marketplace_search_links(style_data)
        
        # Set up price tracking for matched products
        tracking_setup = self._setup_price_tracking(matched_products)
        
        return {
            "style_id": style_id,
            "style_name": style_data["name"],
            "matched_products": matched_products,
            "search_links": search_links,
            "tracking_setup": tracking_setup,
        }
    
    def _create_or_update_style(
        self,
        style_data: Dict[str, Any],
        style_features: List[Dict[str, str]],
    ) -> str:
        """Create or update GarmentStyle node and link features."""
        style_name = style_data["name"]
        
        # Create style node
        style_query = """
        MERGE (gs:GarmentStyle {name: $name})
        ON CREATE SET
            gs.uuid = randomUUID(),
            gs.category = $category,
            gs.garment_type = $garment_type,
            gs.primary_style = $primary_style,
            gs.description = $description,
            gs.color = $color,
            gs.fit = $fit,
            gs.length = $length,
            gs.material = $material,
            gs.created_at = datetime(),
            gs.updated_at = datetime()
        ON MATCH SET
            gs.updated_at = datetime()
        RETURN gs.uuid as uuid
        """
        
        result = self.neo4j.execute_write(
            style_query,
            parameters={
                "name": style_name,
                "category": style_data.get("category"),
                "garment_type": style_data.get("garment_type"),
                "primary_style": style_data.get("primary_style"),
                "description": style_data.get("description"),
                "color": style_data.get("color"),
                "fit": style_data.get("fit"),
                "length": style_data.get("length"),
                "material": style_data.get("material"),
            },
        )
        
        if not result:
            raise Exception("Failed to create style node")
        
        style_uuid = result[0]["uuid"]
        
        # Create and link style features
        for feature in style_features:
            feature_query = """
            MERGE (sf:StyleFeature {feature_type: $feature_type, feature_value: $feature_value})
            ON CREATE SET
                sf.uuid = randomUUID(),
                sf.description = $description,
                sf.created_at = datetime()
            WITH sf
            MATCH (gs:GarmentStyle {uuid: $style_uuid})
            MERGE (gs)-[:HAS_FEATURE]->(sf)
            """
            
            self.neo4j.execute_write(
                feature_query,
                parameters={
                    "feature_type": feature["feature_type"],
                    "feature_value": feature["feature_value"],
                    "description": None,
                    "style_uuid": style_uuid,
                },
            )
        
        return style_uuid
    
    def _link_image_to_style(
        self,
        image_url: str,
        style_uuid: str,
        post_id: str,
    ) -> None:
        """Link an image to a garment style."""
        link_query = """
        MATCH (img:Image {url: $image_url})
        MATCH (gs:GarmentStyle {uuid: $style_uuid})
        MERGE (img)-[:MATCHES_STYLE]->(gs)
        WITH img, gs
        MATCH (p:Post {id: $post_id})
        MERGE (p)-[:ABOUT_STYLE]->(gs)
        """
        
        self.neo4j.execute_write(
            link_query,
            parameters={
                "image_url": image_url,
                "style_uuid": style_uuid,
                "post_id": post_id,
            },
        )
    
    def _match_style_to_products(
        self,
        style_uuid: str,
        style_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Match style to existing products in database."""
        # Search for products with similar features
        match_query = """
        MATCH (gs:GarmentStyle {uuid: $style_uuid})-[:HAS_FEATURE]->(sf:StyleFeature)
        WITH gs, collect(sf.feature_value) as style_features
        MATCH (p:Product)
        WHERE 
            (gs.color IS NULL OR p.tags CONTAINS gs.color OR p.description CONTAINS gs.color)
            AND (gs.category IS NULL OR p.category = gs.category)
            AND (
                p.title CONTAINS gs.primary_style 
                OR p.description CONTAINS gs.primary_style
                OR ANY(tag IN p.tags WHERE tag CONTAINS gs.primary_style)
            )
        WITH p, gs, style_features,
             size([tag IN p.tags WHERE tag IN style_features]) as feature_matches
        WHERE feature_matches > 0
        RETURN p.id as product_id,
               p.title as title,
               p.price as price,
               p.currency as currency,
               p.url as url,
               feature_matches,
               p.status as status
        ORDER BY feature_matches DESC, p.created_utc DESC
        LIMIT 20
        """
        
        result = self.neo4j.execute_read(
            match_query,
            parameters={"style_uuid": style_uuid},
        )
        
        matched_products = []
        for record in result:
            # Create ProductMatch relationship
            match_uuid = str(uuid4())
            confidence = min(record["feature_matches"] / 5.0, 1.0)  # Normalize to 0-1
            
            match_rel_query = """
            MATCH (gs:GarmentStyle {uuid: $style_uuid})
            MATCH (p:Product {id: $product_id})
            MERGE (gs)-[pm:MATCHES_PRODUCT]->(p)
            ON CREATE SET
                pm.uuid = $match_uuid,
                pm.confidence_score = $confidence,
                pm.match_type = CASE 
                    WHEN $confidence >= 0.8 THEN 'exact'
                    WHEN $confidence >= 0.5 THEN 'similar'
                    ELSE 'variant'
                END,
                pm.created_at = datetime()
            RETURN pm.uuid as match_uuid
            """
            
            self.neo4j.execute_write(
                match_rel_query,
                parameters={
                    "style_uuid": style_uuid,
                    "product_id": record["product_id"],
                    "match_uuid": match_uuid,
                    "confidence": confidence,
                },
            )
            
            matched_products.append({
                "product_id": record["product_id"],
                "title": record["title"],
                "price": record["price"],
                "currency": record["currency"],
                "url": record["url"],
                "confidence": confidence,
                "status": record["status"],
            })
        
        return matched_products
    
    def _create_marketplace_search_links(
        self,
        style_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """Create marketplace search links for the style."""
        # Build search terms
        search_terms = []
        if style_data.get("primary_style"):
            search_terms.append(style_data["primary_style"].lower())
        if style_data.get("garment_type"):
            search_terms.append(style_data["garment_type"].lower())
        if style_data.get("color"):
            search_terms.append(style_data["color"].lower())
        
        search_query = " ".join(search_terms)
        
        # Create marketplace links
        links = {
            "depop": f"https://www.depop.com/search/?q={search_query.replace(' ', '%20')}",
            "ebay": f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}",
            "poshmark": f"https://poshmark.com/search?query={search_query.replace(' ', '%20')}",
            "mercari": f"https://www.mercari.com/search/?keyword={search_query.replace(' ', '%20')}",
        }
        
        return links
    
    def _setup_price_tracking(
        self,
        matched_products: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Set up price tracking for matched products."""
        tracked = []
        failed = []
        
        for product in matched_products:
            product_id = product["product_id"]
            
            # Check if already being tracked
            check_query = """
            MATCH (p:Product {id: $product_id})
            OPTIONAL MATCH (p)-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
            RETURN p.id as id, count(ph) as history_count
            """
            
            result = self.neo4j.execute_read(
                check_query,
                parameters={"product_id": product_id},
            )
            
            if result and result[0].get("history_count", 0) > 0:
                tracked.append({
                    "product_id": product_id,
                    "status": "already_tracked",
                })
            else:
                # Mark for tracking (price history will be created on next crawl)
                tracked.append({
                    "product_id": product_id,
                    "status": "tracking_setup",
                })
        
        return {
            "tracked_count": len(tracked),
            "products": tracked,
        }




