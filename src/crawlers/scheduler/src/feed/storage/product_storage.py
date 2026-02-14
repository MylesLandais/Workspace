"""Storage functions for Depop products and price tracking."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from ..models.product import Product
from .neo4j_connection import Neo4jConnection


class ProductStorage:
    """Storage operations for e-commerce products."""

    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize product storage.
        
        Args:
            neo4j: Neo4j connection instance
        """
        self.neo4j = neo4j

    def store_product(self, product: Product) -> bool:
        """
        Store or update a product in Neo4j.
        Creates Product node, Seller node, and relationships.
        Also creates a PriceHistory entry if price changed.
        
        Args:
            product: Product object to store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current product if it exists
            existing_product = self.get_product(product.id)
            
            # Check if price changed
            price_changed = False
            if existing_product:
                old_price = existing_product.get('price')
                if old_price and old_price != product.price:
                    price_changed = True
            else:
                # New product, always create price history
                price_changed = True
            
            # Create or update product
            product_query = """
            MERGE (p:Product {id: $id})
            SET p.title = $title,
                p.description = $description,
                p.price = $price,
                p.currency = $currency,
                p.status = $status,
                p.brand = $brand,
                p.condition = $condition,
                p.size = $size,
                p.category = $category,
                p.tags = $tags,
                p.image_urls = $image_urls,
                p.likes_count = $likes_count,
                p.created_utc = datetime({epochSeconds: $created_utc}),
                p.updated_utc = datetime({epochSeconds: $updated_utc}),
                p.url = $url,
                p.permalink = $permalink,
                p.updated_at = datetime()
            WITH p
            """
            
            created_timestamp = int(product.created_utc.timestamp())
            updated_timestamp = int(product.updated_utc.timestamp()) if product.updated_utc else created_timestamp
            
            # Create seller node and relationship
            if product.seller_username:
                seller_query = """
                MERGE (s:Seller {username: $seller_username})
                ON CREATE SET s.created_at = datetime()
                SET s.updated_at = datetime()
                WITH s
                MATCH (p:Product {id: $product_id})
                MERGE (p)-[:SOLD_BY]->(s)
                """
                
                self.neo4j.execute_write(
                    product_query + seller_query,
                    parameters={
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "currency": product.currency,
                        "status": product.status,
                        "brand": product.brand,
                        "condition": product.condition,
                        "size": product.size,
                        "category": product.category,
                        "tags": product.tags,
                        "image_urls": product.image_urls,
                        "likes_count": product.likes_count,
                        "created_utc": created_timestamp,
                        "updated_utc": updated_timestamp,
                        "url": product.url,
                        "permalink": product.permalink,
                        "seller_username": product.seller_username,
                        "product_id": product.id,
                    },
                )
            else:
                self.neo4j.execute_write(
                    product_query,
                    parameters={
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "currency": product.currency,
                        "status": product.status,
                        "brand": product.brand,
                        "condition": product.condition,
                        "size": product.size,
                        "category": product.category,
                        "tags": product.tags,
                        "image_urls": product.image_urls,
                        "likes_count": product.likes_count,
                        "created_utc": created_timestamp,
                        "updated_utc": updated_timestamp,
                        "url": product.url,
                        "permalink": product.permalink,
                    },
                )
            
            # Create price history entry if price changed
            if price_changed:
                self._create_price_history(product.id, product.price, product.currency)
            
            # Create image nodes and relationships
            self._store_product_images(product.id, product.image_urls)
            
            return True
            
        except Exception as e:
            print(f"Error storing product {product.id}: {e}")
            return False

    def _create_price_history(
        self,
        product_id: str,
        price: float,
        currency: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Create a price history entry for a product.
        
        Args:
            product_id: Product ID
            price: Price value
            currency: Currency code
            timestamp: Timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        price_history_id = str(uuid4())
        timestamp_epoch = int(timestamp.timestamp())
        
        query = """
        MATCH (p:Product {id: $product_id})
        CREATE (ph:PriceHistory {
            id: $price_history_id,
            price: $price,
            currency: $currency,
            timestamp: datetime({epochSeconds: $timestamp}),
            created_at: datetime()
        })
        MERGE (p)-[:HAS_PRICE_HISTORY]->(ph)
        WITH ph
        // Link to previous price history entry for time traversal
        OPTIONAL MATCH (p:Product {id: $product_id})-[:HAS_PRICE_HISTORY]->(prev:PriceHistory)
        WHERE prev.timestamp < ph.timestamp
        WITH ph, prev
        ORDER BY prev.timestamp DESC
        LIMIT 1
        FOREACH (x IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
            MERGE (prev)-[:NEXT_PRICE]->(ph)
        )
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "product_id": product_id,
                "price_history_id": price_history_id,
                "price": price,
                "currency": currency,
                "timestamp": timestamp_epoch,
            },
        )

    def _store_product_images(self, product_id: str, image_urls: List[str]) -> None:
        """
        Store product images as nodes and link to product.
        
        Args:
            product_id: Product ID
            image_urls: List of image URLs
        """
        if not image_urls:
            return
        
        query = """
        MATCH (p:Product {id: $product_id})
        UNWIND $image_urls AS image_url
        MERGE (img:Image {url: image_url})
        ON CREATE SET img.created_at = datetime()
        MERGE (p)-[:HAS_IMAGE]->(img)
        """
        
        self.neo4j.execute_write(
            query,
            parameters={
                "product_id": product_id,
                "image_urls": image_urls,
            },
        )

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a product by ID.
        
        Args:
            product_id: Product ID
        
        Returns:
            Product data dictionary or None
        """
        query = """
        MATCH (p:Product {id: $product_id})
        OPTIONAL MATCH (p)-[:SOLD_BY]->(s:Seller)
        RETURN p,
               s.username as seller_username
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"product_id": product_id},
        )
        
        if result:
            record = result[0]
            product_data = dict(record["p"])
            if record.get("seller_username"):
                product_data["seller_username"] = record["seller_username"]
            return product_data
        return None

    def get_price_history(
        self,
        product_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get price history for a product.
        
        Args:
            product_id: Product ID
            start_time: Start time (optional)
            end_time: End time (optional)
            limit: Maximum number of records
        
        Returns:
            List of price history records
        """
        if start_time and end_time:
            query = """
            MATCH (p:Product {id: $product_id})-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
            WHERE ph.timestamp >= datetime({epochSeconds: $start_time})
            AND ph.timestamp <= datetime({epochSeconds: $end_time})
            RETURN ph
            ORDER BY ph.timestamp ASC
            LIMIT $limit
            """
            params = {
                "product_id": product_id,
                "start_time": int(start_time.timestamp()),
                "end_time": int(end_time.timestamp()),
                "limit": limit,
            }
        else:
            query = """
            MATCH (p:Product {id: $product_id})-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
            RETURN ph
            ORDER BY ph.timestamp DESC
            LIMIT $limit
            """
            params = {
                "product_id": product_id,
                "limit": limit,
            }
        
        result = self.neo4j.execute_read(query, parameters=params)
        return [dict(record["ph"]) for record in result]

    def get_products_by_seller(
        self,
        seller_username: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all products by a seller.
        
        Args:
            seller_username: Seller username
            limit: Maximum number of products
        
        Returns:
            List of product data dictionaries
        """
        query = """
        MATCH (s:Seller {username: $seller_username})<-[:SOLD_BY]-(p:Product)
        RETURN p
        ORDER BY p.created_utc DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"seller_username": seller_username, "limit": limit},
        )
        return [dict(record["p"]) for record in result]

    def get_products_by_brand(
        self,
        brand: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all products by brand.
        
        Args:
            brand: Brand name
            limit: Maximum number of products
        
        Returns:
            List of product data dictionaries
        """
        query = """
        MATCH (p:Product {brand: $brand})
        RETURN p
        ORDER BY p.created_utc DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"brand": brand, "limit": limit},
        )
        return [dict(record["p"]) for record in result]

    def get_products_by_category(
        self,
        category: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all products in a category.
        
        Args:
            category: Category name
            limit: Maximum number of products
        
        Returns:
            List of product data dictionaries
        """
        query = """
        MATCH (p:Product {category: $category})
        RETURN p
        ORDER BY p.created_utc DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"category": category, "limit": limit},
        )
        return [dict(record["p"]) for record in result]

    def search_products(
        self,
        query_text: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Full-text search for products.
        
        Args:
            query_text: Search query
            limit: Maximum number of results
        
        Returns:
            List of product data dictionaries
        """
        query = """
        CALL db.index.fulltext.queryNodes('product_search_index', $query_text)
        YIELD node, score
        WHERE node:Product
        RETURN node as p, score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(
            query,
            parameters={"query_text": query_text, "limit": limit},
        )
        return [dict(record["p"]) for record in result]







