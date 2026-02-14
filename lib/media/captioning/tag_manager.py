"""
Tag manager for hybrid auto/manual/user_bias tagging.
"""

from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

from .models import ImageCaption, ImageTag, TagSource, PersonaClass
from .auto_tagger import AutoTagger
from .config import CaptionConfig


class TagManager:
    """Manages hybrid tagging with auto, manual, and user bias weighting."""
    
    def __init__(self, config: Optional[CaptionConfig] = None):
        self.config = config or CaptionConfig()
        self.auto_tagger = AutoTagger(config)
        self.captions: Dict[str, ImageCaption] = {}
        self.user_biases: Dict[str, float] = {}  # persona/class -> weight
        self.persona_classes: Dict[str, PersonaClass] = {}
        self._initialize_persona_classes()
    
    def _initialize_persona_classes(self):
        """Initialize persona classes from config."""
        aliases = self.config.get_persona_aliases()
        for persona_name in self.config.persona_classes:
            self.persona_classes[persona_name] = PersonaClass(
                name=persona_name,
                aliases=aliases.get(persona_name, []),
                default_weight=1.0,
            )
    
    def auto_tag_directory(self, directory: Path) -> Dict[str, ImageCaption]:
        """Auto-tag all images in a directory."""
        captions = self.auto_tagger.auto_tag_directory(directory)
        self.captions.update(captions)
        return captions
    
    def add_manual_tag(self, filename: str, tag_name: str, confidence: float = 1.0) -> None:
        """Add a manual tag to an image."""
        if filename not in self.captions:
            # Create a new caption if it doesn't exist
            self.captions[filename] = ImageCaption(file_name=filename)
        
        caption = self.captions[filename]
        
        # Create manual tag
        tag = ImageTag(
            name=tag_name,
            source=TagSource.MANUAL,
            confidence=confidence,
            weight=self.config.tagging.manual_weight,
        )
        
        caption.add_tag(tag)
        caption.manual_tags.append(tag_name)
        
        # Update persona if it matches
        for persona_name, persona_class in self.persona_classes.items():
            if persona_class.matches(tag_name):
                if persona_name not in caption.personas:
                    caption.personas.append(persona_name)
                break
    
    def set_bias(self, persona_or_class: str, weight: float) -> None:
        """Set user bias weight for a persona or class."""
        self.user_biases[persona_or_class.lower()] = weight
        
        # Apply bias to existing captions
        for caption in self.captions.values():
            self._apply_bias_to_caption(caption)
    
    def _apply_bias_to_caption(self, caption: ImageCaption) -> None:
        """Apply user biases to a caption."""
        for persona in caption.personas:
            persona_lower = persona.lower()
            if persona_lower in self.user_biases:
                bias_weight = self.user_biases[persona_lower]
                caption.bias_weights[persona] = bias_weight
                
                # Update or add bias tag
                bias_tag = ImageTag(
                    name=persona,
                    source=TagSource.USER_BIAS,
                    confidence=1.0,
                    weight=bias_weight,
                )
                caption.add_tag(bias_tag)
        
        # Update class weights
        for class_name, current_weight in caption.classes.items():
            if class_name.lower() in self.user_biases:
                bias_weight = self.user_biases[class_name.lower()]
                caption.classes[class_name] = current_weight * bias_weight
    
    def calculate_final_weights(self, caption: ImageCaption) -> Dict[str, float]:
        """Calculate final weights for tags combining all sources."""
        tag_weights = defaultdict(float)
        
        for tag in caption.tags:
            if tag.source == TagSource.AUTO:
                weight = tag.weight * tag.confidence
            elif tag.source == TagSource.MANUAL:
                weight = tag.weight * tag.confidence
            elif tag.source == TagSource.USER_BIAS:
                weight = tag.weight
            else:  # FILENAME
                weight = tag.weight * tag.confidence
            
            tag_weights[tag.name.lower()] = max(tag_weights[tag.name.lower()], weight)
        
        return dict(tag_weights)
    
    def merge_tags(self, caption: ImageCaption) -> None:
        """Merge tags from different sources, resolving conflicts."""
        # Group tags by name (case-insensitive)
        tag_groups = defaultdict(list)
        for tag in caption.tags:
            tag_groups[tag.name.lower()].append(tag)
        
        # Merge tags, keeping highest priority
        merged_tags = []
        for name, tags in tag_groups.items():
            # Sort by priority: manual > user_bias > auto > filename
            priority = {
                TagSource.MANUAL: 4,
                TagSource.USER_BIAS: 3,
                TagSource.AUTO: 2,
                TagSource.FILENAME: 1,
            }
            tags.sort(key=lambda t: priority.get(t.source, 0), reverse=True)
            
            # Use the highest priority tag, but combine weights
            primary_tag = tags[0]
            combined_weight = sum(t.weight * t.confidence for t in tags)
            
            merged_tag = ImageTag(
                name=primary_tag.name,
                source=primary_tag.source,
                confidence=max(t.confidence for t in tags),
                weight=combined_weight,
            )
            merged_tags.append(merged_tag)
        
        caption.tags = merged_tags
    
    def get_caption(self, filename: str) -> Optional[ImageCaption]:
        """Get caption for a filename."""
        return self.captions.get(filename)
    
    def get_captions_by_persona(self, persona: str) -> List[ImageCaption]:
        """Get all captions for a specific persona."""
        return [cap for cap in self.captions.values() if persona.lower() in [p.lower() for p in cap.personas]]
    
    def get_captions_by_class(self, class_name: str) -> List[ImageCaption]:
        """Get all captions for a specific class."""
        return [cap for cap in self.captions.values() if class_name.lower() in [c.lower() for c in cap.classes.keys()]]
    
    def sort_by_weight(self, persona_or_class: Optional[str] = None) -> List[ImageCaption]:
        """Sort captions by weight for a persona or class."""
        captions = list(self.captions.values())
        
        if persona_or_class:
            # Filter and sort by specific persona/class
            filtered = []
            for caption in captions:
                weight = 0.0
                if persona_or_class.lower() in [p.lower() for p in caption.personas]:
                    weight = caption.bias_weights.get(persona_or_class, 1.0)
                elif persona_or_class.lower() in [c.lower() for c in caption.classes.keys()]:
                    weight = caption.classes[persona_or_class.lower()]
                
                if weight > 0:
                    filtered.append((caption, weight))
            
            filtered.sort(key=lambda x: x[1], reverse=True)
            return [cap for cap, _ in filtered]
        else:
            # Sort by total weight
            def get_total_weight(cap):
                weights = self.calculate_final_weights(cap)
                return sum(weights.values())
            
            captions.sort(key=get_total_weight, reverse=True)
            return captions








