# Depop Product Crawler

A graph-based crawler for Depop e-commerce products with price tracking and image gallery support.

## Overview

The Depop crawler extends the existing feed architecture to support e-commerce product data. It extracts:

- **Product Information**: Title, description, price, currency, status
- **Garment Context**: Brand, size, condition, category, tags
- **Image Galleries**: Multiple product images with high-resolution URLs
- **Seller Information**: Username and seller relationships
- **Price History**: Temporal tracking of price changes over time

## Architecture

The crawler follows the same graph-style architecture as the Reddit crawler:

```
Product (Node)
  ├── SOLD_BY -> Seller (Node)
  ├── HAS_IMAGE -> Image (Node) [multiple]
  └── HAS_PRICE_HISTORY -> PriceHistory (Node) [temporal chain]
```

### Graph Schema

- **Product**: Main product node with all product metadata
- **Seller**: Seller information (username, profile)
- **Image**: Individual product images
- **PriceHistory**: Temporal price records linked in chronological order

## Usage

### Basic Usage

```python
from feed.platforms.depop import DepopAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.product_storage import ProductStorage

# Initialize
neo4j = get_connection()
depop = DepopAdapter()
product_storage = ProductStorage(neo4j)

# Fetch a product
product = depop.fetch_product("https://www.depop.com/products/krista_h-hot-pink-tights-thick-and/")

# Store in Neo4j
if product:
    product_storage.store_product(product)
```

### Migration

Before using, run the migration to create the schema:

```bash
# In Neo4j Browser or via cypher-shell
:source src/feed/storage/migrations/009_depop_products.cypher
```

Or programmatically:

```python
migration_path = Path("src/feed/storage/migrations/009_depop_products.cypher")
with open(migration_path) as f:
    migration_cypher = f.read()
# Execute migration statements...
```

## Features

### 1. Product Extraction

The `DepopAdapter` extracts product data from HTML pages using:
- JSON-LD structured data (when available)
- HTML selectors with fallbacks
- Open Graph metadata
- Custom parsing for Depop-specific patterns

### 2. Image Gallery Support

Extracts all product images including:
- Main product image
- Gallery images
- High-resolution versions
- Depop media photo URLs

### 3. Price Tracking

Automatically creates `PriceHistory` nodes when:
- A new product is added
- Price changes are detected on updates

Price history is linked chronologically for time-series queries.

### 4. Graph Relationships

Creates rich relationships:
- `Product -[:SOLD_BY]-> Seller`
- `Product -[:HAS_IMAGE]-> Image`
- `Product -[:HAS_PRICE_HISTORY]-> PriceHistory`
- `PriceHistory -[:NEXT_PRICE]-> PriceHistory` (temporal chain)

## Query Examples

### Get Product with All Relationships

```cypher
MATCH (p:Product {id: $product_id})
OPTIONAL MATCH (p)-[:SOLD_BY]->(s:Seller)
OPTIONAL MATCH (p)-[:HAS_IMAGE]->(img:Image)
OPTIONAL MATCH (p)-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
RETURN p, collect(DISTINCT s) as sellers, 
       collect(DISTINCT img) as images, 
       collect(DISTINCT ph) as price_history
ORDER BY ph.timestamp DESC
```

### Price History Over Time

```cypher
MATCH (p:Product {id: $product_id})-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
RETURN ph.timestamp as timestamp, ph.price as price, ph.currency as currency
ORDER BY ph.timestamp ASC
```

### Products by Seller

```cypher
MATCH (s:Seller {username: $seller_username})<-[:SOLD_BY]-(p:Product)
RETURN p
ORDER BY p.created_utc DESC
```

### Products by Brand

```cypher
MATCH (p:Product {brand: $brand})
RETURN p
ORDER BY p.created_utc DESC
```

### Full-Text Search

```cypher
CALL db.index.fulltext.queryNodes('product_search_index', $query_text)
YIELD node, score
WHERE node:Product
RETURN node as p, score
ORDER BY score DESC
LIMIT 50
```

## Storage API

The `ProductStorage` class provides methods:

- `store_product(product)`: Store or update a product
- `get_product(product_id)`: Get product by ID
- `get_price_history(product_id, start_time, end_time)`: Get price history
- `get_products_by_seller(seller_username)`: Get seller's products
- `get_products_by_brand(brand)`: Get products by brand
- `get_products_by_category(category)`: Get products by category
- `search_products(query_text)`: Full-text search

## Example Notebook

See `notebooks/depop_crawler_example.ipynb` for a complete working example.

## Notes

- The crawler respects rate limits with configurable delays
- HTML parsing is robust with multiple fallback strategies
- Price changes are automatically detected and tracked
- Image URLs are normalized and deduplicated
- The graph structure enables powerful relationship queries

## Future Enhancements

- Support for seller profile crawling
- Category/tag relationship graphs
- Price trend analysis queries
- Similar product recommendations based on graph structure
- Integration with existing image deduplication system







