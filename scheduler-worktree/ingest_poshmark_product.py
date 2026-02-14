import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Set up module path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from feed.models.product import Product
    from feed.storage.product_storage import ProductStorage
    from feed.storage.neo4j_connection import get_connection
except ImportError as e:
    print(f"ERROR: Missing module import: {e}. Ensure the script is run from the project root and all dependencies are installed.")
    sys.exit(1)

def hex_to_datetime(hex_str: str) -> datetime:
    """Converts a Neo4j ID prefix (hex timestamp) to a UTC datetime."""
    # Poshmark IDs are MongoDB ObjectIDs, where the first 8 hex characters 
    # represent a Unix timestamp.
    try:
        if len(hex_str) > 8:
            hex_str = hex_str[:8]
        timestamp = int(hex_str, 16)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except Exception:
        # Fallback to a fixed past date if parsing fails
        return datetime(2000, 1, 1, tzinfo=timezone.utc)

def ingest_poshmark_products():
    """Ingests hardcoded Poshmark product metadata into the Neo4j database."""

    # 1. Product Data (Manually Extracted & Parsed from previous steps)
    product_data = [
        # Listing 1: New product with Brand
        {
            "productID": "634d007b4bc6553c3a3b2e3a",
            "name": "InCharacter Costumes Teen Racy Referee Costume JUNIOR Medium 5-7",
            "price": 25.0,
            "currency": "USD",
            "brand": "Party City",
            "category": "Women<Other",
            "condition": "new",
            "description": "Shop Women's Party City Pink Black Size Med 5-7 Other at a discounted price at Poshmark. Description: InCharacter Costumes Teen Racy Referee Costume JUNIOR Medium 5-7.",
            "image_url": "https://di2ponv0v5otw.cloudfront.net/posts/2022/10/17/634d007b4bc6553c3a3b2e3a/m_634d00b0c9a22815651b261d.jpg",
            "url": "https://poshmark.com/listing/InCharacter-Costumes-Teen-Racy-Referee-Costume-JUNIOR-Medium-57-634d007b4bc6553c3a3b2e3a",
            "seller_username": "mr1star", # Inferred from URL context
        },
        # Listing 2: Used product without Brand in JSON-LD
        {
            "productID": "5622673c99086a9ebf000b15",
            "name": "Used Racey Referee Costume",
            "price": 10.0,
            "currency": "USD",
            "brand": None,
            "category": "Women<Other",
            "condition": "used",
            "description": "Teen Racy Referee Costume. Jr. Small (1-3). Package Includes: Dress and Knee High Striped Stockings.",
            "image_url": "https://dtpmhvbsmffsz.cloudfront.net/posts/2015/10/17/5622673c99086a9ebf000b15/m_5622673c99086a9ebf000b16.jpg",
            "url": "https://poshmark.com/listing/Used-Racey-Referee-Costume-5622673c99086a9ebf000b15",
            "seller_username": "madjade1", # Inferred from URL context
        },
    ]
    
    # 2. Setup Connection and Storage
    try:
        neo4j_conn = get_connection()
    except Exception as e:
        print(f"ERROR: Failed to connect to Neo4j. Ensure .env is configured and the service is running.")
        print(f"Details: {e}")
        return

    storage = ProductStorage(neo4j_conn)
    print(f"Neo4j connection established. Starting ingestion of {len(product_data)} Poshmark listings...")
    
    # 3. Ingest Data
    success_count = 0
    
    for data in product_data:
        # Determine created_utc from product ID prefix
        created_utc = hex_to_datetime(data["productID"])
        current_utc = datetime.now(timezone.utc)
        
        # Map data to Product model
        product = Product(
            id=data["productID"],
            title=data["name"],
            description=data["description"],
            price=data["price"],
            currency=data["currency"],
            status="ONSALE", # Assuming they are for sale unless price is 0 (Poshmark doesn't explicitly state "SOLD" in this metadata)
            brand=data["brand"],
            condition=data["condition"],
            category=data["category"],
            # Simple tag generation
            tags=[t for t in [data["brand"], data["category"], data["condition"]] if t],
            image_urls=[data["image_url"]],
            seller_username=data["seller_username"],
            created_utc=created_utc,
            updated_utc=current_utc, 
            url=data["url"],
            permalink=data["url"].split("poshmark.com/listing/")[1],
        )

        # Store product
        print(f"Processing product: {product.id} - {product.title}")
        if storage.store_product(product):
            success_count += 1
            print(f"  -> SUCCESS: Product and price history stored.")
        else:
            print(f"  -> FAILED: Could not store product {product.id}.")
            
    print(f"\nIngestion complete. {success_count} / {len(product_data)} products successfully stored.")

if __name__ == "__main__":
    ingest_poshmark_products()