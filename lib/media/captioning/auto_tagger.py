"""
Auto-tagging engine using CLIP and filename pattern matching.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import torch
import numpy as np

try:
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False

from .models import ImageTag, TagSource, ImageCaption, PersonaClass
from .config import CaptionConfig, CLIPConfig


class AutoTagger:
    """Automatic image tagging using CLIP and pattern matching."""
    
    def __init__(self, config: Optional[CaptionConfig] = None):
        self.config = config or CaptionConfig()
        self.clip_model = None
        self.clip_processor = None
        self._load_clip_model()
    
    def _load_clip_model(self):
        """Load CLIP model if available."""
        if not CLIP_AVAILABLE:
            print("Warning: transformers not available. CLIP tagging will be disabled.")
            return
        
        try:
            clip_config = self.config.clip
            model_name = clip_config.model_name
            
            print(f"Loading CLIP model: {model_name}")
            self.clip_model = CLIPModel.from_pretrained(model_name)
            self.clip_processor = CLIPProcessor.from_pretrained(model_name)
            
            # Set device
            if clip_config.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = clip_config.device
            
            self.clip_model = self.clip_model.to(device)
            self.clip_model.eval()
            self.device = device
            print(f"CLIP model loaded on {device}")
        except Exception as e:
            print(f"Warning: Could not load CLIP model: {e}")
            self.clip_model = None
            self.clip_processor = None
    
    def extract_personas_from_filename(self, filename: str) -> List[str]:
        """Extract persona names from filename using pattern matching."""
        personas = []
        filename_lower = filename.lower()
        
        # Check against known persona classes
        for persona_name in self.config.persona_classes:
            if persona_name.lower() in filename_lower:
                personas.append(persona_name)
        
        # Try pattern matching
        for pattern in self.config.tagging.filename_patterns:
            matches = re.findall(pattern, filename_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and match not in personas:
                    # Check if it matches a known persona
                    for persona_name in self.config.persona_classes:
                        if persona_name.lower() in match.lower() or match.lower() in persona_name.lower():
                            personas.append(persona_name)
                            break
        
        return list(set(personas))
    
    def generate_clip_tags(self, image_path: Path, candidate_tags: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """Generate tags using CLIP model."""
        if not self.clip_model or not self.clip_processor:
            return []
        
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Default candidate tags if not provided
            if candidate_tags is None:
                candidate_tags = [
                    "portrait", "photo", "person", "woman", "man", "young", "casual",
                    "formal", "outdoor", "indoor", "smiling", "serious", "close-up",
                    "full body", "headshot", "fashion", "street style", "studio",
                ]
            
            # Process image and text
            inputs = self.clip_processor(
                text=candidate_tags,
                images=image,
                return_tensors="pt",
                padding=True,
            ).to(self.device)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Get top tags
            probs_cpu = probs.cpu().numpy()[0]
            tag_scores = list(zip(candidate_tags, probs_cpu))
            tag_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by threshold
            threshold = self.config.tagging.auto_confidence_threshold
            filtered_tags = [(tag, score) for tag, score in tag_scores if score >= threshold]
            
            return filtered_tags
        except Exception as e:
            print(f"Error generating CLIP tags for {image_path}: {e}")
            return []
    
    def auto_tag_image(self, image_path: Path) -> ImageCaption:
        """Auto-tag a single image."""
        filename = image_path.name
        
        # Extract personas from filename
        personas = self.extract_personas_from_filename(filename)
        
        # Generate CLIP tags
        clip_tags = self.generate_clip_tags(image_path)
        
        # Create tags
        tags = []
        
        # Add persona tags from filename
        for persona in personas:
            tags.append(ImageTag(
                name=persona,
                source=TagSource.FILENAME,
                confidence=0.8,
                weight=self.config.tagging.auto_weight,
            ))
        
        # Add CLIP-generated tags
        for tag_name, confidence in clip_tags:
            tags.append(ImageTag(
                name=tag_name,
                source=TagSource.AUTO,
                confidence=float(confidence),
                weight=self.config.tagging.auto_weight,
            ))
        
        # Build caption text
        caption_parts = []
        if personas:
            caption_parts.append(f"A photo of {', '.join(personas)}")
        if clip_tags:
            top_tags = [tag for tag, _ in clip_tags[:5]]
            caption_parts.append(", ".join(top_tags))
        
        caption_text = ". ".join(caption_parts) if caption_parts else "An image"
        
        # Create classes dict
        classes = {}
        if personas:
            classes["persona"] = sum([self.config.tagging.auto_weight] * len(personas))
        
        return ImageCaption(
            file_name=filename,
            caption_text=caption_text,
            tags=tags,
            personas=personas,
            classes=classes,
            auto_tags=[tag for tag, _ in clip_tags],
        )
    
    def auto_tag_directory(self, directory: Path, pattern: Optional[str] = None) -> Dict[str, ImageCaption]:
        """Auto-tag all images in a directory."""
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        captions = {}
        # Common image extensions
        image_extensions = ["jpg", "jpeg", "png", "webp", "gif", "bmp", "tiff", "JPG", "JPEG", "PNG", "WEBP"]
        
        image_files = []
        for ext in image_extensions:
            image_files.extend(directory.glob(f"*.{ext}"))
        
        # Remove duplicates
        image_files = list(set(image_files))
        
        print(f"Found {len(image_files)} images to tag")
        
        for i, image_path in enumerate(image_files, 1):
            print(f"Tagging {i}/{len(image_files)}: {image_path.name}")
            try:
                caption = self.auto_tag_image(image_path)
                captions[image_path.name] = caption
            except Exception as e:
                print(f"Error tagging {image_path}: {e}")
        
        return captions

