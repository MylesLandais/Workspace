"""GraphQL schema for e-commerce products and garment styles."""

from typing import List, Optional
from datetime import datetime
import strawberry

from ..storage.neo4j_connection import Neo4jConnection, get_connection


@strawberry.type
class Seller:
    """Seller type."""
    username: str
    seller_id: Optional[str] = None
    created_at: Optional[str] = None


@strawberry.type
class PriceHistory:
    """Price history entry."""
    id: str
    price: float
    currency: str
    timestamp: str
    created_at: Optional[str] = None


@strawberry.type
class ProductImage:
    """Product image."""
    url: str
    image_index: Optional[int] = None
    created_at: Optional[str] = None


@strawberry.type
class Product:
    """E-commerce product type."""
    id: str
    title: str
    description: str
    price: float
    currency: str
    status: str
    brand: Optional[str] = None
    condition: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None
    tags: List[str]
    image_urls: List[str]  # Will be exposed as imageUrls in GraphQL
    seller_username: Optional[str] = None  # Will be exposed as sellerUsername
    likes_count: int  # Will be exposed as likesCount
    created_utc: str  # Will be exposed as createdUtc
    updated_utc: Optional[str] = None  # Will be exposed as updatedUtc
    url: str
    permalink: Optional[str] = None
    
    @strawberry.field
    def images(self) -> List[ProductImage]:
        """Get product images with metadata."""
        neo4j = get_connection()
        query = """
        MATCH (p:Product {id: $product_id})-[r:HAS_IMAGE]->(img:Image)
        RETURN img.url as url, r.image_index as image_index, img.created_at as created_at
        ORDER BY r.image_index ASC NULLS LAST
        """
        result = neo4j.execute_read(query, parameters={"product_id": self.id})
        return [
            ProductImage(
                url=record["url"],
                imageIndex=record.get("image_index"),
                createdAt=str(record.get("created_at", "")) if record.get("created_at") else None,
            )
            for record in result
        ]
    
    @strawberry.field
    def seller(self) -> Optional[Seller]:
        """Get product seller."""
        if not self.seller_username:
            return None
        
        neo4j = get_connection()
        query = """
        MATCH (p:Product {id: $product_id})-[:SOLD_BY]->(s:Seller)
        RETURN s.username as username, s.created_at as created_at
        LIMIT 1
        """
        result = neo4j.execute_read(query, parameters={"product_id": self.id})
        if result:
            record = result[0]
            return Seller(
                username=record["username"],
                created_at=str(record.get("created_at", "")) if record.get("created_at") else None,
            )
        return None
    
    @strawberry.field
    def price_history(self, limit: int = 10) -> List[PriceHistory]:
        """Get price history for product."""
        neo4j = get_connection()
        query = """
        MATCH (p:Product {id: $product_id})-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
        RETURN ph.id as id, ph.price as price, ph.currency as currency,
               toString(ph.timestamp) as timestamp, toString(ph.created_at) as created_at
        ORDER BY ph.timestamp DESC
        LIMIT $limit
        """
        result = neo4j.execute_read(
            query,
            parameters={"product_id": self.id, "limit": limit},
        )
        return [
            PriceHistory(
                id=record["id"],
                price=record["price"],
                currency=record["currency"],
                timestamp=record["timestamp"],
                created_at=record.get("created_at"),
            )
            for record in result
        ]


@strawberry.type
class StyleFeature:
    """Garment style feature."""
    uuid: str
    feature_type: str
    feature_value: str
    description: Optional[str] = None


@strawberry.type
class ProductMatch:
    """Product match with confidence."""
    product: Product
    confidence_score: float  # Exposed as confidenceScore
    match_type: str  # Exposed as matchType
    matched_features: List[str]  # Exposed as matchedFeatures


@strawberry.type
class GarmentStyle:
    """Garment style type."""
    uuid: str
    name: str
    category: str
    garment_type: str  # Exposed as garmentType
    primary_style: str  # Exposed as primaryStyle
    description: Optional[str] = None
    color: Optional[str] = None
    fit: Optional[str] = None
    length: Optional[str] = None
    material: Optional[str] = None
    
    @strawberry.field
    def features(self) -> List[StyleFeature]:
        """Get style features."""
        neo4j = get_connection()
        query = """
        MATCH (gs:GarmentStyle {uuid: $style_uuid})-[:HAS_FEATURE]->(sf:StyleFeature)
        RETURN sf.uuid as uuid, sf.feature_type as feature_type,
               sf.feature_value as feature_value, sf.description as description
        """
        result = neo4j.execute_read(query, parameters={"style_uuid": self.uuid})
        return [
            StyleFeature(
                uuid=record["uuid"],
                feature_type=record["feature_type"],
                feature_value=record["feature_value"],
                description=record.get("description"),
            )
            for record in result
        ]
    
    @strawberry.field
    def matched_products(self, limit: int = 20) -> List[ProductMatch]:
        """Get products matching this style."""
        neo4j = get_connection()
        query = """
        MATCH (gs:GarmentStyle {uuid: $style_uuid})-[pm:MATCHES_PRODUCT]->(p:Product)
        RETURN p, pm.confidence_score as confidence, pm.match_type as match_type
        ORDER BY pm.confidence_score DESC
        LIMIT $limit
        """
        result = neo4j.execute_read(
            query,
            parameters={"style_uuid": self.uuid, "limit": limit},
        )
        
        matches = []
        for record in result:
            p = record["p"]
            product = Product(
                id=p.get("id", ""),
                title=p.get("title", ""),
                description=p.get("description", ""),
                price=p.get("price", 0.0),
                currency=p.get("currency", "USD"),
                status=p.get("status", "ONSALE"),
                brand=p.get("brand"),
                condition=p.get("condition"),
                size=p.get("size"),
                category=p.get("category"),
                tags=p.get("tags", []),
                image_urls=p.get("image_urls", []),
                seller_username=p.get("seller_username"),
                likes_count=p.get("likes_count", 0),
                created_utc=str(p.get("created_utc", "")),
                updated_utc=str(p.get("updated_utc", "")) if p.get("updated_utc") else None,
                url=p.get("url", ""),
                permalink=p.get("permalink"),
            )
            matches.append(ProductMatch(
                product=product,
                confidence_score=record["confidence"],
                match_type=record["match_type"],
                matched_features=[],  # Could be expanded
            ))
        
        return matches


@strawberry.input
class ProductFilter:
    """Filter for products."""
    brand: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    status: Optional[str] = None
    seller_username: Optional[str] = None
    limit: int = 20
    offset: int = 0


@strawberry.input
class StyleFilter:
    """Filter for garment styles."""
    category: Optional[str] = None
    garment_type: Optional[str] = None
    primary_style: Optional[str] = None
    color: Optional[str] = None
    limit: int = 20
    offset: int = 0


@strawberry.type
class EcommerceQuery:
    """E-commerce GraphQL queries."""
    
    @strawberry.field
    def product(self, id: str) -> Optional[Product]:
        """Get product by ID."""
        neo4j = get_connection()
        query = """
        MATCH (p:Product {id: $id})
        OPTIONAL MATCH (p)-[:SOLD_BY]->(s:Seller)
        RETURN p, s.username as seller_username
        """
        result = neo4j.execute_read(query, parameters={"id": id})
        
        if result:
            record = result[0]
            p = record["p"]
            return Product(
                id=p.get("id", ""),
                title=p.get("title", ""),
                description=p.get("description", ""),
                price=p.get("price", 0.0),
                currency=p.get("currency", "USD"),
                status=p.get("status", "ONSALE"),
                brand=p.get("brand"),
                condition=p.get("condition"),
                size=p.get("size"),
                category=p.get("category"),
                tags=p.get("tags", []),
                image_urls=p.get("image_urls", []),
                seller_username=record.get("seller_username"),
                likes_count=p.get("likes_count", 0),
                created_utc=str(p.get("created_utc", "")) if p.get("created_utc") else "",
                updated_utc=str(p.get("updated_utc", "")) if p.get("updated_utc") else None,
                url=p.get("url", ""),
                permalink=p.get("permalink"),
            )
        return None
    
    @strawberry.field
    def products(self, filter: Optional[ProductFilter] = None) -> List[Product]:
        """Get products with filtering."""
        neo4j = get_connection()
        filter_obj = filter or ProductFilter()
        
        where_clauses = []
        params = {
            "limit": filter_obj.limit,
            "offset": filter_obj.offset,
        }
        
        if filter_obj.brand:
            where_clauses.append("p.brand = $brand")
            params["brand"] = filter_obj.brand
        
        if filter_obj.category:
            where_clauses.append("p.category = $category")
            params["category"] = filter_obj.category
        
        if filter_obj.min_price is not None:
            where_clauses.append("p.price >= $min_price")
            params["min_price"] = filter_obj.min_price
        
        if filter_obj.max_price is not None:
            where_clauses.append("p.price <= $max_price")
            params["max_price"] = filter_obj.max_price
        
        if filter_obj.status:
            where_clauses.append("p.status = $status")
            params["status"] = filter_obj.status
        
        if filter_obj.seller_username:
            where_clauses.append("EXISTS { (p)-[:SOLD_BY]->(:Seller {username: $seller_username}) }")
            params["seller_username"] = filter_obj.seller_username
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        MATCH (p:Product)
        WHERE {where_clause}
        OPTIONAL MATCH (p)-[:SOLD_BY]->(s:Seller)
        RETURN p, s.username as seller_username
        ORDER BY p.created_utc DESC
        SKIP $offset
        LIMIT $limit
        """
        
        result = neo4j.execute_read(query, parameters=params)
        
        products = []
        for record in result:
            p = record["p"]
            products.append(Product(
                id=p.get("id", ""),
                title=p.get("title", ""),
                description=p.get("description", ""),
                price=p.get("price", 0.0),
                currency=p.get("currency", "USD"),
                status=p.get("status", "ONSALE"),
                brand=p.get("brand"),
                condition=p.get("condition"),
                size=p.get("size"),
                category=p.get("category"),
                tags=p.get("tags", []),
                image_urls=p.get("image_urls", []),
                seller_username=record.get("seller_username"),
                likes_count=p.get("likes_count", 0),
                created_utc=str(p.get("created_utc", "")),
                updated_utc=str(p.get("updated_utc", "")) if p.get("updated_utc") else None,
                url=p.get("url", ""),
                permalink=p.get("permalink"),
            ))
        
        return products
    
    @strawberry.field
    def search_products(self, query_text: str, limit: int = 20) -> List[Product]:
        """Full-text search for products."""
        neo4j = get_connection()
        search_query = """
        CALL db.index.fulltext.queryNodes('product_search_index', $query_text)
        YIELD node, score
        WHERE node:Product
        RETURN node as p, score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        result = neo4j.execute_read(
            search_query,
            parameters={"query_text": query_text, "limit": limit},
        )
        
        products = []
        for record in result:
            p = record["p"]
            products.append(Product(
                id=p.get("id", ""),
                title=p.get("title", ""),
                description=p.get("description", ""),
                price=p.get("price", 0.0),
                currency=p.get("currency", "USD"),
                status=p.get("status", "ONSALE"),
                brand=p.get("brand"),
                condition=p.get("condition"),
                size=p.get("size"),
                category=p.get("category"),
                tags=p.get("tags", []),
                image_urls=p.get("image_urls", []),
                seller_username=None,  # Would need separate query
                likes_count=p.get("likes_count", 0),
                created_utc=str(p.get("created_utc", "")),
                updated_utc=str(p.get("updated_utc", "")) if p.get("updated_utc") else None,
                url=p.get("url", ""),
                permalink=p.get("permalink"),
            ))
        
        return products
    
    @strawberry.field
    def garment_style(self, uuid: str) -> Optional[GarmentStyle]:
        """Get garment style by UUID."""
        neo4j = get_connection()
        query = """
        MATCH (gs:GarmentStyle {uuid: $uuid})
        RETURN gs
        """
        result = neo4j.execute_read(query, parameters={"uuid": uuid})
        
        if result:
            gs = result[0]["gs"]
            return GarmentStyle(
                uuid=gs.get("uuid", ""),
                name=gs.get("name", ""),
                category=gs.get("category", ""),
                garment_type=gs.get("garment_type", ""),
                primary_style=gs.get("primary_style", ""),
                description=gs.get("description"),
                color=gs.get("color"),
                fit=gs.get("fit"),
                length=gs.get("length"),
                material=gs.get("material"),
            )
        return None
    
    @strawberry.field
    def garment_styles(self, filter: Optional[StyleFilter] = None) -> List[GarmentStyle]:
        """Get garment styles with filtering."""
        neo4j = get_connection()
        filter_obj = filter or StyleFilter()
        
        where_clauses = []
        params = {
            "limit": filter_obj.limit,
            "offset": filter_obj.offset,
        }
        
        if filter_obj.category:
            where_clauses.append("gs.category = $category")
            params["category"] = filter_obj.category
        
        if filter_obj.garment_type:
            where_clauses.append("gs.garment_type = $garment_type")
            params["garment_type"] = filter_obj.garment_type
        
        if filter_obj.primary_style:
            where_clauses.append("gs.primary_style = $primary_style")
            params["primary_style"] = filter_obj.primary_style
        
        if filter_obj.color:
            where_clauses.append("gs.color = $color")
            params["color"] = filter_obj.color
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        MATCH (gs:GarmentStyle)
        WHERE {where_clause}
        RETURN gs
        ORDER BY gs.created_at DESC
        SKIP $offset
        LIMIT $limit
        """
        
        result = neo4j.execute_read(query, parameters=params)
        
        styles = []
        for record in result:
            gs = record["gs"]
            styles.append(GarmentStyle(
                uuid=gs.get("uuid", ""),
                name=gs.get("name", ""),
                category=gs.get("category", ""),
                garment_type=gs.get("garment_type", ""),
                primary_style=gs.get("primary_style", ""),
                description=gs.get("description"),
                color=gs.get("color"),
                fit=gs.get("fit"),
                length=gs.get("length"),
                material=gs.get("material"),
            ))
        
        return styles
    
    @strawberry.field
    def similar_styles(self, style_uuid: str, min_shared_features: int = 2) -> List[GarmentStyle]:
        """Find similar garment styles based on shared features."""
        neo4j = get_connection()
        query = """
        MATCH (gs1:GarmentStyle {uuid: $style_uuid})-[:HAS_FEATURE]->(sf:StyleFeature)<-[:HAS_FEATURE]-(gs2:GarmentStyle)
        WHERE gs1 <> gs2
        WITH gs1, gs2, count(sf) as shared_features
        WHERE shared_features >= $min_shared_features
        RETURN gs2, shared_features
        ORDER BY shared_features DESC
        LIMIT 10
        """
        
        result = neo4j.execute_read(
            query,
            parameters={"style_uuid": style_uuid, "min_shared_features": min_shared_features},
        )
        
        styles = []
        for record in result:
            gs = record["gs2"]
            styles.append(GarmentStyle(
                uuid=gs.get("uuid", ""),
                name=gs.get("name", ""),
                category=gs.get("category", ""),
                garment_type=gs.get("garment_type", ""),
                primary_style=gs.get("primary_style", ""),
                description=gs.get("description"),
                color=gs.get("color"),
                fit=gs.get("fit"),
                length=gs.get("length"),
                material=gs.get("material"),
            ))
        
        return styles

