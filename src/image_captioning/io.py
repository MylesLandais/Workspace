"""
I/O operations for image captions (JSONL and TXT formats).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Iterator

from .models import ImageCaption


class CaptionIO:
    """Handles loading and saving captions in various formats."""
    
    @staticmethod
    def load_jsonl(file_path: Path) -> Dict[str, ImageCaption]:
        """Load captions from JSONL file."""
        file_path = Path(file_path)
        if not file_path.exists():
            return {}
        
        captions = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    caption = ImageCaption.from_dict(data)
                    captions[caption.file_name] = caption
                except Exception as e:
                    print(f"Error parsing line in {file_path}: {e}")
                    continue
        
        return captions
    
    @staticmethod
    def save_jsonl(captions: Dict[str, ImageCaption], file_path: Path) -> None:
        """Save captions to JSONL file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            for caption in captions.values():
                line = json.dumps(caption.to_dict(), ensure_ascii=False)
                f.write(line + "\n")
    
    @staticmethod
    def export_txt(captions: Dict[str, ImageCaption], image_directory: Path) -> None:
        """Export captions as .txt files (Ostris-compatible format)."""
        image_directory = Path(image_directory)
        
        for filename, caption in captions.items():
            # Get base filename without extension
            base_name = Path(filename).stem
            txt_path = image_directory / f"{base_name}.txt"
            
            # Build caption text from tags
            caption_parts = []
            
            # Add personas first
            if caption.personas:
                caption_parts.extend(caption.personas)
            
            # Add manual tags
            if caption.manual_tags:
                caption_parts.extend(caption.manual_tags)
            
            # Add auto tags (filter out duplicates)
            for tag in caption.auto_tags:
                if tag.lower() not in [p.lower() for p in caption_parts]:
                    caption_parts.append(tag)
            
            # Fallback to caption_text if no tags
            if not caption_parts and caption.caption_text:
                caption_parts = [caption.caption_text]
            
            # Write to file
            caption_text = ", ".join(caption_parts) if caption_parts else ""
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(caption_text)
    
    @staticmethod
    def load_from_directory(image_directory: Path, jsonl_path: Optional[Path] = None) -> Dict[str, ImageCaption]:
        """Load captions from directory, checking for JSONL file first."""
        image_directory = Path(image_directory)
        captions = {}
        
        # Try to load from JSONL if specified
        if jsonl_path and jsonl_path.exists():
            captions = CaptionIO.load_jsonl(jsonl_path)
        
        # Also try to load from metadata.jsonl in the directory
        metadata_path = image_directory / "metadata.jsonl"
        if metadata_path.exists():
            jsonl_captions = CaptionIO.load_jsonl(metadata_path)
            # Merge, with JSONL taking precedence
            for filename, caption in jsonl_captions.items():
                if filename not in captions:
                    captions[filename] = caption
        
        return captions
    
    @staticmethod
    def save_to_directory(
        captions: Dict[str, ImageCaption],
        image_directory: Path,
        jsonl_filename: str = "metadata.jsonl",
        export_txt_files: bool = True,
    ) -> None:
        """Save captions to directory in both JSONL and TXT formats."""
        image_directory = Path(image_directory)
        image_directory.mkdir(parents=True, exist_ok=True)
        
        # Save JSONL
        jsonl_path = image_directory / jsonl_filename
        CaptionIO.save_jsonl(captions, jsonl_path)
        
        # Export TXT files if requested
        if export_txt_files:
            CaptionIO.export_txt(captions, image_directory)
    
    @staticmethod
    def validate_captions(captions: Dict[str, ImageCaption]) -> List[str]:
        """Validate captions and return list of errors."""
        errors = []
        
        for filename, caption in captions.items():
            if not caption.file_name:
                errors.append(f"Caption for {filename} has no file_name")
            
            if not caption.tags and not caption.caption_text:
                errors.append(f"Caption for {filename} has no tags or caption text")
        
        return errors








