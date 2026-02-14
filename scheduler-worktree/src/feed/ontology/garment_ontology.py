"""Garment ontology for e-commerce product classification and style matching."""

from typing import Dict, List, Optional
from enum import Enum


class GarmentCategory(str, Enum):
    """Top-level garment categories."""
    BOTTOMS = "Bottoms"
    TOPS = "Tops"
    OUTERWEAR = "Outerwear"
    UNDERWEAR = "Underwear"
    ACCESSORIES = "Accessories"
    FOOTWEAR = "Footwear"


class BottomType(str, Enum):
    """Types of bottom garments."""
    YOGA_PANTS = "Yoga Pants"
    LEGGINGS = "Leggings"
    JEANS = "Jeans"
    TROUSERS = "Trousers"
    SHORTS = "Shorts"
    SKIRTS = "Skirts"
    SWEATPANTS = "Sweatpants"


class YogaPantStyle(str, Enum):
    """Specific styles of yoga pants."""
    # Panel styles
    SHEER_PANEL = "Sheer Panel"
    MESH_PANEL = "Mesh Panel"
    CUTOUT_PANEL = "Cutout Panel"
    SOLID = "Solid"
    
    # Fit styles
    COMPRESSION = "Compression"
    LOOSE_FIT = "Loose Fit"
    HIGH_WAISTED = "High Waisted"
    MID_RISE = "Mid Rise"
    LOW_RISE = "Low Rise"
    
    # Length styles
    FULL_LENGTH = "Full Length"
    CAPRI = "Capri"
    ANKLE_LENGTH = "Ankle Length"
    
    # Material/texture styles
    SHINY = "Shiny"
    MATTE = "Matte"
    RIBBED = "Ribbed"
    SEAMLESS = "Seamless"
    
    # Pattern styles
    PRINTED = "Printed"
    STRIPED = "Striped"
    COLOR_BLOCK = "Color Block"


class GarmentOntology:
    """Ontology for garment classification and style matching."""
    
    # Node labels
    GARMENT_STYLE = "GarmentStyle"
    GARMENT_VARIATION = "GarmentVariation"
    STYLE_FEATURE = "StyleFeature"
    PRODUCT_MATCH = "ProductMatch"
    
    # Relationship types
    HAS_STYLE = "HAS_STYLE"
    HAS_FEATURE = "HAS_FEATURE"
    IS_VARIATION_OF = "IS_VARIATION_OF"
    MATCHES_PRODUCT = "MATCHES_PRODUCT"
    SIMILAR_TO = "SIMILAR_TO"
    
    @staticmethod
    def get_garment_style_properties() -> Dict[str, str]:
        """Return expected properties for GarmentStyle nodes."""
        return {
            "uuid": "String (unique, UUID)",
            "name": "String (e.g., 'Sheer Panel Yoga Pants')",
            "category": "String (GarmentCategory enum)",
            "garment_type": "String (BottomType enum)",
            "primary_style": "String (YogaPantStyle enum)",
            "description": "String (detailed description)",
            "created_at": "DateTime",
            "updated_at": "DateTime",
        }
    
    @staticmethod
    def get_style_feature_properties() -> Dict[str, str]:
        """Return expected properties for StyleFeature nodes."""
        return {
            "uuid": "String (unique, UUID)",
            "feature_type": "String (e.g., 'panel_type', 'fit', 'length')",
            "feature_value": "String (e.g., 'sheer', 'compression', 'full_length')",
            "description": "String (nullable)",
            "created_at": "DateTime",
        }
    
    @staticmethod
    def get_product_match_properties() -> Dict[str, str]:
        """Return expected properties for ProductMatch nodes."""
        return {
            "uuid": "String (unique, UUID)",
            "confidence_score": "Float (0.0-1.0)",
            "match_type": "String (e.g., 'exact', 'similar', 'variant')",
            "matched_features": "List[String] (list of matched feature UUIDs)",
            "created_at": "DateTime",
        }
    
    @staticmethod
    def create_style_from_image_analysis(
        image_analysis: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Create a GarmentStyle node from computer vision image analysis.
        
        Args:
            image_analysis: Dict with keys like:
                - garment_type: "Yoga Pants"
                - color: "Black"
                - panel_type: "Sheer Panel"
                - fit: "Compression"
                - length: "Full Length"
                - material: "Polyester/Spandex"
                - features: List of detected features
        
        Returns:
            Dict suitable for creating GarmentStyle node
        """
        # Build style name from analysis
        style_parts = []
        if image_analysis.get("panel_type"):
            style_parts.append(image_analysis["panel_type"])
        if image_analysis.get("garment_type"):
            style_parts.append(image_analysis["garment_type"])
        else:
            style_parts.append("Yoga Pants")
        
        style_name = " ".join(style_parts)
        
        # Build description
        desc_parts = []
        if image_analysis.get("color"):
            desc_parts.append(f"Color: {image_analysis['color']}")
        if image_analysis.get("fit"):
            desc_parts.append(f"Fit: {image_analysis['fit']}")
        if image_analysis.get("length"):
            desc_parts.append(f"Length: {image_analysis['length']}")
        if image_analysis.get("material"):
            desc_parts.append(f"Material: {image_analysis['material']}")
        
        description = "; ".join(desc_parts)
        
        return {
            "name": style_name,
            "category": GarmentCategory.BOTTOMS.value,
            "garment_type": image_analysis.get("garment_type", BottomType.YOGA_PANTS.value),
            "primary_style": image_analysis.get("panel_type", YogaPantStyle.SOLID.value),
            "description": description,
            "color": image_analysis.get("color"),
            "fit": image_analysis.get("fit"),
            "length": image_analysis.get("length"),
            "material": image_analysis.get("material"),
            "detected_features": image_analysis.get("features", []),
        }
    
    @staticmethod
    def extract_style_features(image_analysis: Dict[str, any]) -> List[Dict[str, str]]:
        """
        Extract style features from image analysis.
        
        Returns:
            List of feature dicts with 'feature_type' and 'feature_value'
        """
        features = []
        
        feature_mapping = {
            "panel_type": "panel_style",
            "fit": "fit_style",
            "length": "length_style",
            "material": "material_type",
            "color": "color",
        }
        
        for key, feature_type in feature_mapping.items():
            if key in image_analysis and image_analysis[key]:
                features.append({
                    "feature_type": feature_type,
                    "feature_value": str(image_analysis[key]),
                })
        
        return features




