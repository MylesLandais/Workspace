"""
Pydantic models for structured image captions.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TagSource(str, Enum):
    """Source of a tag (CLIP-based)."""
    AUTO = "auto"
    MANUAL = "manual"
    USER_BIAS = "user_bias"
    FILENAME = "filename"


class WD14TagCategory(str, Enum):
    """WD14 tag categories (separate ontology from CLIP)."""
    CHARACTER = "character"
    GENERAL = "general"
    RATING = "rating"


class ImageTag(BaseModel):
    """A tag associated with an image."""
    name: str = Field(..., description="Tag name")
    source: TagSource = Field(..., description="Source of the tag")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    weight: float = Field(default=1.0, description="Weight for this tag")
    
    def __hash__(self):
        """Make hashable for use in sets."""
        return hash((self.name.lower(), self.source))
    
    def __eq__(self, other):
        """Compare tags by name and source."""
        if not isinstance(other, ImageTag):
            return False
        return self.name.lower() == other.name.lower() and self.source == other.source


class PersonaClass(BaseModel):
    """Definition of a persona/actor class."""
    name: str = Field(..., description="Persona name (e.g., 'brooke')")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    description: Optional[str] = Field(None, description="Description of the persona")
    default_weight: float = Field(default=1.0, description="Default weight for this persona")
    
    def matches(self, text: str) -> bool:
        """Check if text matches this persona (name or alias)."""
        text_lower = text.lower()
        if self.name.lower() in text_lower:
            return True
        return any(alias.lower() in text_lower for alias in self.aliases)


class ImageCaption(BaseModel):
    """Structured image caption with tags and metadata."""
    file_name: str = Field(..., description="Image filename")
    caption_text: str = Field(default="", description="Human-readable caption")
    tags: List[ImageTag] = Field(default_factory=list, description="Structured tags")
    personas: List[str] = Field(default_factory=list, description="Persona/actor names")
    classes: Dict[str, float] = Field(default_factory=dict, description="Class assignments with weights")
    auto_tags: List[str] = Field(default_factory=list, description="CLIP-generated tags")
    manual_tags: List[str] = Field(default_factory=list, description="User-provided tags")
    bias_weights: Dict[str, float] = Field(default_factory=dict, description="User preference weights")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def get_all_tags(self) -> List[str]:
        """Get all tag names as a flat list."""
        return list(set([tag.name for tag in self.tags] + self.auto_tags + self.manual_tags))
    
    def get_tag_by_name(self, name: str) -> Optional[ImageTag]:
        """Get a tag by name (case-insensitive)."""
        name_lower = name.lower()
        for tag in self.tags:
            if tag.name.lower() == name_lower:
                return tag
        return None
    
    def add_tag(self, tag: ImageTag) -> None:
        """Add or update a tag."""
        existing = self.get_tag_by_name(tag.name)
        if existing:
            # Update existing tag if new one has higher confidence or is manual
            if tag.source == TagSource.MANUAL or tag.confidence > existing.confidence:
                self.tags.remove(existing)
                self.tags.append(tag)
        else:
            self.tags.append(tag)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_name": self.file_name,
            "caption_text": self.caption_text,
            "tags": [tag.model_dump() for tag in self.tags],
            "personas": self.personas,
            "classes": self.classes,
            "auto_tags": self.auto_tags,
            "manual_tags": self.manual_tags,
            "bias_weights": self.bias_weights,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageCaption":
        """Create from dictionary."""
        # Convert tag dicts to ImageTag objects
        tags = [ImageTag(**tag) if isinstance(tag, dict) else tag for tag in data.get("tags", [])]

        # Parse datetime strings
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.utcnow()

        return cls(
            file_name=data["file_name"],
            caption_text=data.get("caption_text", ""),
            tags=tags,
            personas=data.get("personas", []),
            classes=data.get("classes", {}),
            auto_tags=data.get("auto_tags", []),
            manual_tags=data.get("manual_tags", []),
            bias_weights=data.get("bias_weights", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
        )


class WD14Tag(BaseModel):
    """A WD14 tag (separate from CLIP ImageTag)."""
    name: str = Field(..., description="Tag name")
    category: WD14TagCategory = Field(..., description="Tag category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="WD14 confidence score (0-1)")

    def __hash__(self):
        return hash((self.name.lower(), self.category))

    def __eq__(self, other):
        if not isinstance(other, WD14Tag):
            return False
        return self.name.lower() == other.name.lower() and self.category == other.category


class WD14Result(BaseModel):
    """Result of WD14 tagging for a single image."""
    image_sha256: str = Field(..., description="SHA256 hash of image")
    character_tags: List[WD14Tag] = Field(default_factory=list, description="Character tags")
    general_tags: List[WD14Tag] = Field(default_factory=list, description="General tags")
    rating: str = Field(default="safe", description="Content rating (safe, questionable, explicit)")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    model_version: str = Field(default="wd14-vit", description="Model version used")
    score_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw scores per tag")

    def get_all_tags(self) -> List[WD14Tag]:
        """Get all tags (character + general)."""
        return self.character_tags + self.general_tags

    def get_high_confidence_tags(self, threshold: float = 0.95) -> List[WD14Tag]:
        """Get tags above confidence threshold."""
        return [tag for tag in self.get_all_tags() if tag.confidence >= threshold]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "image_sha256": self.image_sha256,
            "character_tags": [tag.model_dump() for tag in self.character_tags],
            "general_tags": [tag.model_dump() for tag in self.general_tags],
            "rating": self.rating,
            "processed_at": self.processed_at.isoformat(),
            "model_version": self.model_version,
            "score_metadata": self.score_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WD14Result":
        """Create from dictionary."""
        processed_at = data.get("processed_at")
        if isinstance(processed_at, str):
            processed_at = datetime.fromisoformat(processed_at)
        elif processed_at is None:
            processed_at = datetime.utcnow()

        character_tags = [WD14Tag(**tag) if isinstance(tag, dict) else tag for tag in data.get("character_tags", [])]
        general_tags = [WD14Tag(**tag) if isinstance(tag, dict) else tag for tag in data.get("general_tags", [])]

        return cls(
            image_sha256=data["image_sha256"],
            character_tags=character_tags,
            general_tags=general_tags,
            rating=data.get("rating", "safe"),
            processed_at=processed_at,
            model_version=data.get("model_version", "wd14-vit"),
            score_metadata=data.get("score_metadata", {}),
        )




