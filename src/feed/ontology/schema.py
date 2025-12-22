"""Neo4j graph ontology schema definitions for Creator/Handle/Media system."""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class HandleStatus(str, Enum):
    """Status of a handle relationship."""
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    ABANDONED = "Abandoned"
    UNVERIFIED = "Unverified"


class VerificationConfidence(str, Enum):
    """Confidence level for handle verification."""
    HIGH = "High"  # Link exists in trusted bio
    MEDIUM = "Medium"  # Username matches exactly across platforms
    MANUAL = "Manual"  # Admin/User confirmed (100% confidence)


class MediaType(str, Enum):
    """Type of media content."""
    VIDEO = "Video"
    IMAGE = "Image"
    TEXT = "Text"
    AUDIO = "Audio"
    MIXED = "Mixed"


class GraphOntology:
    """Defines the Neo4j graph ontology for Creator/Handle/Media system."""

    # Node labels
    CREATOR = "Creator"
    HANDLE = "Handle"
    PLATFORM = "Platform"
    MEDIA = "Media"
    VIDEO = "Video"  # Auxiliary label for Media
    IMAGE = "Image"  # Auxiliary label for Media
    TEXT = "Text"  # Auxiliary label for Media

    # Relationship types
    OWNS_HANDLE = "OWNS_HANDLE"  # Creator -> Handle (strict ownership)
    ON_PLATFORM = "ON_PLATFORM"  # Handle -> Platform (structural)
    REFERENCES = "REFERENCES"  # Handle -> Handle (soft connection for bio-crawler)
    PUBLISHED = "PUBLISHED"  # Handle -> Media (content relationship)
    SOURCED_FROM = "SOURCED_FROM"  # Media -> Platform (platform attribution)

    @staticmethod
    def get_creator_properties() -> Dict[str, str]:
        """Return expected properties for Creator nodes."""
        return {
            "uuid": "String (unique, UUID)",
            "name": "String (human-readable name)",
            "slug": "String (unique, URL-friendly identifier)",
            "bio": "String (nullable, aggregated bio)",
            "avatar_url": "String (nullable, profile picture)",
            "created_at": "DateTime",
            "updated_at": "DateTime",
        }

    @staticmethod
    def get_handle_properties() -> Dict[str, str]:
        """Return expected properties for Handle nodes."""
        return {
            "uuid": "String (unique, UUID)",
            "username": "String (platform-specific username)",
            "display_name": "String (nullable, display name on platform)",
            "profile_url": "String (full URL to profile)",
            "follower_count": "Integer (nullable)",
            "verified_by_platform": "Boolean (platform's verification badge)",
            "created_at": "DateTime",
            "updated_at": "DateTime",
        }

    @staticmethod
    def get_platform_properties() -> Dict[str, str]:
        """Return expected properties for Platform nodes."""
        return {
            "name": "String (unique, e.g., 'YouTube', 'TikTok')",
            "slug": "String (unique, URL-friendly, e.g., 'youtube')",
            "api_base_url": "String (nullable, API endpoint)",
            "icon_url": "String (nullable, platform icon)",
            "created_at": "DateTime",
        }

    @staticmethod
    def get_media_properties() -> Dict[str, str]:
        """Return expected properties for Media nodes (base properties)."""
        return {
            "uuid": "String (unique, UUID)",
            "title": "String (nullable)",
            "source_url": "String (original content URL)",
            "publish_date": "DateTime",
            "thumbnail_url": "String (nullable)",
            "media_type": "String (MediaType enum)",
            "created_at": "DateTime",
            "updated_at": "DateTime",
        }

    @staticmethod
    def get_video_properties() -> Dict[str, str]:
        """Return additional properties for Video media."""
        return {
            "duration": "Integer (seconds, nullable)",
            "view_count": "Integer (nullable)",
            "aspect_ratio": "String (nullable, e.g., '16:9', '9:16')",
            "resolution": "String (nullable, e.g., '1080p')",
        }

    @staticmethod
    def get_image_properties() -> Dict[str, str]:
        """Return additional properties for Image media."""
        return {
            "width": "Integer (pixels, nullable)",
            "height": "Integer (pixels, nullable)",
            "aspect_ratio": "String (nullable, e.g., '1:1', '4:3')",
        }

    @staticmethod
    def get_text_properties() -> Dict[str, str]:
        """Return additional properties for Text media."""
        return {
            "body_content": "String (full text content)",
            "word_count": "Integer (nullable)",
        }

    @staticmethod
    def get_owns_handle_edge_properties() -> Dict[str, str]:
        """Return properties for OWNS_HANDLE relationship."""
        return {
            "status": "String (HandleStatus enum: Active, Suspended, Abandoned, Unverified)",
            "verified": "Boolean (whether handle is verified)",
            "confidence": "String (VerificationConfidence enum: High, Medium, Manual)",
            "discovered_at": "DateTime (when handle was discovered)",
            "verified_at": "DateTime (nullable, when verification occurred)",
            "created_at": "DateTime",
        }

    @staticmethod
    def get_references_edge_properties() -> Dict[str, str]:
        """Return properties for REFERENCES relationship (bio-crawler discoveries)."""
        return {
            "source_url": "String (URL where reference was found)",
            "discovered_at": "DateTime",
            "confidence": "String (VerificationConfidence enum)",
            "context": "String (nullable, surrounding text where link was found)",
        }

    @staticmethod
    def get_published_edge_properties() -> Dict[str, str]:
        """Return properties for PUBLISHED relationship."""
        return {
            "published_at": "DateTime",
            "engagement_score": "Float (nullable, calculated metric)",
        }

    @staticmethod
    def validate_creator_data(data: Dict) -> List[str]:
        """Validate creator data against schema. Returns list of errors."""
        errors = []
        required_fields = ["uuid", "name", "slug"]
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "slug" in data and not isinstance(data["slug"], str):
            errors.append("slug must be a string")
        
        if "name" in data and not isinstance(data["name"], str):
            errors.append("name must be a string")
        
        return errors

    @staticmethod
    def validate_handle_data(data: Dict) -> List[str]:
        """Validate handle data against schema. Returns list of errors."""
        errors = []
        required_fields = ["uuid", "username", "profile_url"]
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return errors

    @staticmethod
    def validate_media_data(data: Dict) -> List[str]:
        """Validate media data against schema. Returns list of errors."""
        errors = []
        required_fields = ["uuid", "source_url", "publish_date", "media_type"]
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "media_type" in data:
            valid_types = [e.value for e in MediaType]
            if data["media_type"] not in valid_types:
                errors.append(f"media_type must be one of: {', '.join(valid_types)}")
        
        return errors

