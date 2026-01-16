"""
Configuration for image captioning system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class CLIPConfig:
    """CLIP model configuration."""
    model_name: str = "openai/clip-vit-base-patch32"
    device: str = "auto"  # "auto", "cuda", "cpu"
    batch_size: int = 16
    image_size: int = 224


@dataclass
class WD14Config:
    """WD14 ONNX model configuration for image tagging."""
    model_repo: str = "SmilingWolf/wd-v1-4-vit-tagger-v2"
    confidence_threshold: float = 0.95
    device: str = "cuda"  # "cuda" or "cpu"
    batch_size: int = 32
    providers: List[str] = field(default_factory=lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"])
    model_cache_dir: Optional[Path] = None


@dataclass
class TaggingConfig:
    """Tagging configuration."""
    auto_confidence_threshold: float = 0.5
    auto_weight: float = 1.0
    manual_weight: float = 2.0
    user_bias_weight: float = 1.5
    filename_patterns: List[str] = field(default_factory=lambda: [
        r"(\w+)-monk",
        r"(\w+)-monk-",
        r"(\w+)_",
        r"(\w+)-",
    ])


@dataclass
class CaptionConfig:
    """Main configuration for captioning system."""
    clip: CLIPConfig = field(default_factory=CLIPConfig)
    wd14: WD14Config = field(default_factory=WD14Config)
    tagging: TaggingConfig = field(default_factory=TaggingConfig)
    persona_classes: List[str] = field(default_factory=lambda: [
        "brooke",
        "taylor",
        "sydney",
    ])
    output_dir: Optional[Path] = None
    
    def get_persona_aliases(self) -> Dict[str, List[str]]:
        """Get persona aliases mapping."""
        # Common aliases for known personas
        aliases = {
            "brooke": ["brooke monk", "brooke-monk"],
            "taylor": ["taylor swift", "taylor-swift"],
            "sydney": ["sydney sweeney", "sydney-sweeney"],
        }
        return aliases








