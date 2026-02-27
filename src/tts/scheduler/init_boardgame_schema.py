#!/usr/bin/env python3
"""Initialize Neo4j database schema for Game ontology."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def initialize_game_schema():
    """Initialize Neo4j database schema for Games."""
    neo4j = get_connection()
    
    print("Initializing Neo4j schema for Game ontology...")
    
    # Create constraints
    print("Creating constraints...")
    constraints = [
        # Game unique IDs
        "CREATE CONSTRAINT game_bgg_id_unique IF NOT EXISTS FOR (g:BoardGame) REQUIRE g.bgg_id IS UNIQUE",
        
        # Entity names unique (optional, but good for merging)
        "CREATE CONSTRAINT mechanic_name_unique IF NOT EXISTS FOR (m:Mechanic) REQUIRE m.name IS UNIQUE",
        "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT designer_name_unique IF NOT EXISTS FOR (d:Designer) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT publisher_name_unique IF NOT EXISTS FOR (p:Publisher) REQUIRE p.name IS UNIQUE",
        
        # Retail constraints
        "CREATE CONSTRAINT retail_listing_url_unique IF NOT EXISTS FOR (r:RetailListing) REQUIRE r.url IS UNIQUE",
    ]
    
    for constraint in constraints:
        try:
            neo4j.execute_write(constraint)
            print(f"  ✓ {constraint[:60]}...")
        except Exception as e:
            print(f"  ✗ {constraint[:60]}... ({e})")
    
    # Create indexes
    print("\nCreating indexes...")
    indexes = [
        "CREATE INDEX game_name IF NOT EXISTS FOR (g:BoardGame) ON (g.name)",
        "CREATE INDEX game_year IF NOT EXISTS FOR (g:BoardGame) ON (g.year_published)",
    ]
    
    for index in indexes:
        try:
            neo4j.execute_write(index)
            print(f"  ✓ {index[:60]}...")
        except Exception as e:
            print(f"  ✗ {index[:60]}... ({e})")
            
    # Fulltext indexes for search
    print("\nCreating fulltext indexes...")
    fulltext_indexes = [
        "CREATE FULLTEXT INDEX game_search_ft IF NOT EXISTS FOR (g:BoardGame) ON EACH [g.name, g.description]"
    ]

    for index in fulltext_indexes:
        try:
            neo4j.execute_write(index)
            print(f"  ✓ {index[:60]}...")
        except Exception as e:
            # Fulltext indexes often fail if they already exist with slightly different config
            print(f"  ✗ {index[:60]}... ({e})")
    
    print("\n✓ Game Schema initialization complete!")
    neo4j.close()

if __name__ == "__main__":
    initialize_game_schema()
