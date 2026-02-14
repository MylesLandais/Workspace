#!/usr/bin/env python3
"""Link a board game to a retail listing and add a price point."""

import sys
import argparse
from typing import Optional
from pathlib import Path
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from feed.ontology.game_ontology import GameOntology
from feed.storage.neo4j_connection import get_connection

def extract_asin(url: str) -> Optional[str]:
    """Extract ASIN from Amazon URL."""
    match = re.search(r'/([A-Z0-9]{10})', url)
    return match.group(1) if match else None

def add_retail_listing(bgg_id: int, url: str, price: Optional[float] = None, currency: str = "USD"):
    """
    Link a game to a retail listing and optional price.
    
    Args:
        bgg_id: BoardGameGeek ID of the game
        url: URL of the retail listing
        price: Current price (optional)
        currency: Currency code
    """
    neo4j = get_connection()
    
    # 1. Determine Store Name and External ID
    store_name = "Unknown"
    external_id = None
    
    if "amazon.com" in url:
        store_name = "Amazon"
        external_id = extract_asin(url)
    elif "boardgamegeek.com" in url:
        store_name = "BoardGameGeek"
    
    print(f"Processing listing for Game ID {bgg_id}...")
    print(f"Store: {store_name}")
    if external_id:
        print(f"External ID: {external_id}")
    
    # 2. Create RetailListing and Link to Game
    listing_data = GameOntology.create_retail_listing_data(
        store_name=store_name,
        url=url,
        external_id=external_id
    )
    
    print("Linking RetailListing to Game...")
    # Using MERGE on URL to avoid duplicates
    query = f"""
        MATCH (g:{GameOntology.BOARD_GAME} {{bgg_id: $bgg_id}})
        MERGE (r:{GameOntology.RETAIL_LISTING} {{url: $url}})
        SET r += $props
        MERGE (g)-[:{GameOntology.SOLD_AT}]->(r)
        RETURN r
    """
    
    result = neo4j.execute_write(query, {
        "bgg_id": bgg_id,
        "url": url,
        "props": listing_data
    })
    
    if not result:
        print(f"Error: Game with BGG ID {bgg_id} not found. Import it first.")
        neo4j.close()
        return

    # 3. Add PricePoint if provided
    if price is not None:
        print(f"Adding PricePoint: {price} {currency}")
        price_data = GameOntology.create_price_point_data(
            price=price,
            currency=currency
        )
        
        # Create PricePoint and link to RetailListing
        # We always CREATE a new PricePoint to track history
        query_price = f"""
            MATCH (r:{GameOntology.RETAIL_LISTING} {{url: $url}})
            CREATE (p:{GameOntology.PRICE_POINT})
            SET p = $props
            CREATE (r)-[:{GameOntology.HAS_PRICE}]->(p)
        """
        
        neo4j.execute_write(query_price, {
            "url": url,
            "props": price_data
        })
        print("Price point added.")

    print("Success!")
    neo4j.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add retail listing/price to a game")
    parser.add_argument("bgg_id", type=int, help="BGG ID of the game")
    parser.add_argument("url", type=str, help="URL of the retail listing")
    parser.add_argument("--price", type=float, help="Current price")
    parser.add_argument("--currency", type=str, default="USD", help="Currency code")
    
    args = parser.parse_args()
    
    add_retail_listing(args.bgg_id, args.url, args.price, args.currency)
