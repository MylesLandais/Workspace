"""Product line ontology for tracking product catalogs over time.

This module defines the ontology for product lines (e.g., Lululemon's "Wunder Train",
Victoria's Secret's "Perfect Coverage") and how they evolve over time with variants,
releases, and collections.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ReleaseType(str, Enum):
    """Product release types."""
    FIRST_RELEASE = "First Release"
    RE_RELEASE = "Re-release"
    LIMITED_EDITION = "Limited Edition"
    CORE = "Core"


class PriceType(str, Enum):
    """Price point types."""
    ORIGINAL = "original"
    SALE = "sale"
    CLEARANCE = "clearance"
    DISCONTINUED = "discontinued"


class CollectionType(str, Enum):
    """Collection types."""
    SEASONAL = "Seasonal"
    LIMITED_EDITION = "Limited Edition"
    COLLABORATION = "Collaboration"
    SPECIAL_EVENT = "Special Event"
    CORE = "Core"


class ProductLineOntology:
    """Ontology for product lines and style variants."""
    
    # Node labels
    PRODUCT_LINE = "ProductLine"
    BASE_STYLE = "BaseStyle"
    STYLE_VARIANT = "StyleVariant"
    COLOR_VARIANT = "ColorVariant"
    COLLECTION = "Collection"
    PRICE_POINT = "PricePoint"
    
    # Relationship types
    HAS_BASE_STYLE = "HAS_BASE_STYLE"
    HAS_VARIANT = "HAS_VARIANT"
    HAS_COLOR = "HAS_COLOR"
    HAS_PRICE_POINT = "HAS_PRICE_POINT"
    IN_COLLECTION = "IN_COLLECTION"
    EVOLVED_FROM = "EVOLVED_FROM"
    SUCCEEDED_BY = "SUCCEEDED_BY"
    BELONGS_TO = "BELONGS_TO"
    
    @staticmethod
    def get_product_line_properties() -> List[str]:
        """Get expected properties for ProductLine nodes."""
        return [
            "name",  # e.g., "Wunder Train"
            "brand",  # e.g., "Lululemon"
            "category",  # e.g., "Bottoms"
            "subcategory",  # e.g., "Tights"
            "description",
            "created_at",
            "discontinued_at",  # nullable
        ]
    
    @staticmethod
    def get_base_style_properties() -> List[str]:
        """Get expected properties for BaseStyle nodes."""
        return [
            "name",  # e.g., "Wunder Train High-Rise Tight"
            "style_family",  # e.g., "Wunder Train"
            "fit_type",  # e.g., "High-Rise", "Mid-Rise"
            "length_options",  # e.g., ["23", "25", "28", "31"]
            "material_base",  # e.g., "Everlux", "Nulu"
            "created_at",
        ]
    
    @staticmethod
    def get_style_variant_properties() -> List[str]:
        """Get expected properties for StyleVariant nodes."""
        return [
            "style_number",  # e.g., "W5FMWS" (unique identifier)
            "base_style",  # e.g., "Wunder Train High-Rise Tight"
            "variant_type",  # e.g., "Mesh Panel", "Contour Fit", "Standard"
            "release_type",  # e.g., "First Release", "Re-release"
            "release_date",  # e.g., "2023-10"
            "original_price",  # e.g., 118.00
            "currency",  # e.g., "USD"
            "material",  # e.g., "Mesh, Everlux"
            "features",  # List of features
            "created_at",
        ]
    
    @staticmethod
    def get_color_variant_properties() -> List[str]:
        """Get expected properties for ColorVariant nodes."""
        return [
            "color_name",  # e.g., "Black"
            "hex_code",  # e.g., "#000000"
            "collection",  # e.g., "Core", "Summer Haze"
            "release_date",
            "created_at",
        ]
    
    @staticmethod
    def get_collection_properties() -> List[str]:
        """Get expected properties for Collection nodes."""
        return [
            "name",  # e.g., "Summer Haze", "Seawheeze 2023"
            "collection_type",  # e.g., "Seasonal", "Limited Edition"
            "brand",  # e.g., "Lululemon"
            "release_date",
            "end_date",  # nullable
            "description",
            "created_at",
        ]
    
    @staticmethod
    def get_price_point_properties() -> List[str]:
        """Get expected properties for PricePoint nodes."""
        return [
            "price",  # e.g., 118.00
            "currency",  # e.g., "USD"
            "price_type",  # e.g., "original", "sale", "clearance"
            "effective_date",  # timestamp
            "discontinued_date",  # nullable timestamp
            "created_at",
        ]
    
    @staticmethod
    def create_product_line_data(
        name: str,
        brand: str,
        category: str,
        subcategory: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create ProductLine node data."""
        return {
            "name": name,
            "brand": brand,
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "created_at": datetime.now().isoformat(),
        }
    
    @staticmethod
    def create_style_variant_data(
        style_number: str,
        base_style: str,
        variant_type: str,
        release_type: str,
        release_date: str,
        original_price: float,
        currency: str = "USD",
        material: Optional[str] = None,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create StyleVariant node data."""
        return {
            "style_number": style_number,
            "base_style": base_style,
            "variant_type": variant_type,
            "release_type": release_type,
            "release_date": release_date,
            "original_price": original_price,
            "currency": currency,
            "material": material,
            "features": features or [],
            "created_at": datetime.now().isoformat(),
        }
    
    @staticmethod
    def create_color_variant_data(
        color_name: str,
        hex_code: Optional[str] = None,
        collection: Optional[str] = None,
        release_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create ColorVariant node data."""
        return {
            "color_name": color_name,
            "hex_code": hex_code,
            "collection": collection or "Core",
            "release_date": release_date,
            "created_at": datetime.now().isoformat(),
        }
    
    @staticmethod
    def create_collection_data(
        name: str,
        collection_type: str,
        brand: str,
        release_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create Collection node data."""
        return {
            "name": name,
            "collection_type": collection_type,
            "brand": brand,
            "release_date": release_date,
            "end_date": end_date,
            "description": description,
            "created_at": datetime.now().isoformat(),
        }
    
    @staticmethod
    def create_price_point_data(
        price: float,
        currency: str,
        price_type: str,
        effective_date: str,
        discontinued_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create PricePoint node data."""
        return {
            "price": price,
            "currency": currency,
            "price_type": price_type,
            "effective_date": effective_date,
            "discontinued_date": discontinued_date,
            "created_at": datetime.now().isoformat(),
        }




