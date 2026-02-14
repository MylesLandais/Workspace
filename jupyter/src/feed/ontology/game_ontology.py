"""Game ontology for tracking board games and their metadata.

This module defines the ontology for games, initially focused on board games from BoardGameGeek,
to support future digital play capabilities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class GameType(str, Enum):
    """Types of games."""
    BOARDGAME = "BoardGame"
    VIDEOGAME = "VideoGame"
    RPG = "RPG"
    WARGAME = "Wargame"


class GameOntology:
    """Ontology for Games, specifically Board Games."""
    
    # Node labels
    GAME = "Game"
    BOARD_GAME = "BoardGame"  # Specific label for board games
    DESIGNER = "Designer"
    ARTIST = "Artist"
    PUBLISHER = "Publisher"
    MECHANIC = "Mechanic"
    CATEGORY = "Category"
    EXPANSION = "Expansion"
    RETAIL_LISTING = "RetailListing"
    PRICE_POINT = "PricePoint"
    
    # Relationship types
    DESIGNED_BY = "DESIGNED_BY"
    ILLUSTRATED_BY = "ILLUSTRATED_BY"
    PUBLISHED_BY = "PUBLISHED_BY"
    HAS_MECHANIC = "HAS_MECHANIC"
    IN_CATEGORY = "IN_CATEGORY"
    EXPANDS = "EXPANDS"  # Expansion -> Base Game
    PART_OF_FAMILY = "PART_OF_FAMILY"
    SOLD_AT = "SOLD_AT"  # Game -> RetailListing
    HAS_PRICE = "HAS_PRICE"  # RetailListing -> PricePoint
    
    @staticmethod
    def get_board_game_properties() -> List[str]:
        """Get expected properties for BoardGame nodes."""
        return [
            "bgg_id",  # Integer, unique ID from BoardGameGeek
            "name",
            "year_published",
            "min_players",
            "max_players",
            "playing_time",  # minutes
            "min_playtime",  # minutes
            "max_playtime",  # minutes
            "age",  # min age
            "description",
            "image_url",
            "thumbnail_url",
            "rating_average",
            "complexity_average",  # weight
            "created_at",
            "updated_at"
        ]

    @staticmethod
    def create_board_game_data(
        bgg_id: int,
        name: str,
        year_published: Optional[int] = None,
        min_players: Optional[int] = None,
        max_players: Optional[int] = None,
        playing_time: Optional[int] = None,
        min_playtime: Optional[int] = None,
        max_playtime: Optional[int] = None,
        age: Optional[int] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        rating_average: Optional[float] = None,
        complexity_average: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create BoardGame node data."""
        return {
            "bgg_id": bgg_id,
            "name": name,
            "year_published": year_published,
            "min_players": min_players,
            "max_players": max_players,
            "playing_time": playing_time,
            "min_playtime": min_playtime,
            "max_playtime": max_playtime,
            "age": age,
            "description": description,
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "rating_average": rating_average,
            "complexity_average": complexity_average,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    @staticmethod
    def create_retail_listing_data(
        store_name: str,
        url: str,
        external_id: Optional[str] = None,  # e.g., ASIN
        sku: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create RetailListing node data."""
        return {
            "store_name": store_name,
            "url": url,
            "external_id": external_id,
            "sku": sku,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    @staticmethod
    def create_price_point_data(
        price: float,
        currency: str,
        timestamp: Optional[str] = None,
        available: bool = True,
    ) -> Dict[str, Any]:
        """Create PricePoint node data."""
        return {
            "price": price,
            "currency": currency,
            "timestamp": timestamp or datetime.now().isoformat(),
            "available": available,
        }
