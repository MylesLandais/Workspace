"""
Structured Image Captioning System with Hybrid Tagging

Provides structured data types for complex text embeddings, supporting
hybrid auto-tagging, manual tagging, and user bias weighting.
"""

from .models import (
    TagSource,
    ImageTag,
    PersonaClass,
    ImageCaption,
)
from .tag_manager import TagManager
from .auto_tagger import AutoTagger
from .io import CaptionIO
from .config import CaptionConfig

__all__ = [
    "TagSource",
    "ImageTag",
    "PersonaClass",
    "ImageCaption",
    "TagManager",
    "AutoTagger",
    "CaptionIO",
    "CaptionConfig",
]








