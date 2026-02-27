# Structured Image Captioning System

A comprehensive image captioning system with structured data types (Pydantic models) for complex text embeddings, supporting hybrid auto-tagging, manual tagging, and user bias weighting.

## Features

- **Structured Data Models**: Pydantic models for type-safe caption metadata
- **Hybrid Tagging**: Combines auto (CLIP), manual, and user bias tags
- **Persona/Class Support**: Organize images by personas or actors (e.g., "brooke")
- **Multiple Output Formats**: JSONL (HuggingFace compatible) and TXT (Ostris compatible)
- **Weight Calculation**: Intelligent weight merging from multiple sources
- **CLI Interface**: Easy-to-use command-line tools

## Installation

The system requires:
- `pydantic` (for structured models)
- `PIL` / `Pillow` (for image processing)
- `torch` (for CLIP model)
- `transformers` (for CLIP, optional but recommended)

## Usage

### Python API

```python
from pathlib import Path
from src.image_captioning import TagManager, CaptionIO

# Initialize manager
manager = TagManager()

# Auto-tag images in a directory
captions = manager.auto_tag_directory(Path("data/Pictures"))

# Add manual tags
manager.add_manual_tag("brooke-monk.jpg", "brooke", confidence=1.0)
manager.add_manual_tag("brooke-monk.jpg", "portrait", confidence=1.0)

# Set user bias (boost certain personas)
manager.set_bias("brooke", weight=1.5)

# Export to JSONL
CaptionIO.save_jsonl(manager.captions, Path("captions.jsonl"))

# Export to TXT files (Ostris format)
CaptionIO.export_txt(manager.captions, Path("data/Pictures"))

# Sort by persona
sorted_captions = manager.sort_by_weight("brooke")
for caption in sorted_captions[:10]:
    print(f"{caption.file_name}: {caption.personas}")
```

### CLI Usage

```bash
# Auto-tag images
python -m src.image_captioning.cli tag-images data/Pictures

# Add manual tags
python -m src.image_captioning.cli add-manual-tags data/Pictures brooke-monk.jpg brooke portrait

# Set user bias
python -m src.image_captioning.cli set-bias data/Pictures brooke 1.5

# Export to JSONL
python -m src.image_captioning.cli export-jsonl data/Pictures output.jsonl

# Export to TXT files
python -m src.image_captioning.cli export-txt data/Pictures

# Sort by persona/class
python -m src.image_captioning.cli sort-by-class data/Pictures --persona-or-class brooke --limit 20
```

## Data Models

### ImageCaption

Main caption model with:
- `file_name`: Image filename
- `caption_text`: Human-readable caption
- `tags`: List of structured ImageTag objects
- `personas`: List of persona/actor names
- `classes`: Dictionary of class assignments with weights
- `auto_tags`: CLIP-generated tags
- `manual_tags`: User-provided tags
- `bias_weights`: User preference weights
- `metadata`: Additional extensible metadata

### ImageTag

Structured tag with:
- `name`: Tag name
- `source`: TagSource enum (AUTO, MANUAL, USER_BIAS, FILENAME)
- `confidence`: Confidence score (0-1)
- `weight`: Weight for this tag

## Output Formats

### JSONL Format

```json
{"file_name": "brooke-monk.jpg", "caption_text": "A photo of brooke, a young woman", "tags": [{"name": "brooke", "source": "manual", "confidence": 1.0, "weight": 1.5}], "personas": ["brooke"], "classes": {"persona": 1.5}}
```

### TXT Format (Ostris-compatible)

Each image gets a corresponding `.txt` file:
```
brooke, young woman, casual clothing, portrait
```

## Configuration

Customize behavior via `CaptionConfig`:

```python
from src.image_captioning import CaptionConfig, CLIPConfig, TaggingConfig

config = CaptionConfig(
    clip=CLIPConfig(
        model_name="openai/clip-vit-base-patch32",
        device="cuda",
        batch_size=16,
    ),
    tagging=TaggingConfig(
        auto_confidence_threshold=0.5,
        auto_weight=1.0,
        manual_weight=2.0,
        user_bias_weight=1.5,
    ),
    persona_classes=["brooke", "taylor", "sydney"],
)

manager = TagManager(config)
```

## Weight Calculation

Final tag weights are calculated as:
- Auto tags: `weight * confidence`
- Manual tags: `weight * confidence` (higher default weight)
- User bias: `weight` (applied multiplicatively)

Tags are merged with priority: Manual > User Bias > Auto > Filename








