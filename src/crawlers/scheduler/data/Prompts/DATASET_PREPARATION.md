# Dataset Preparation for Consistent Character Training

## Overview

This guide covers dataset preparation workflows for training models with consistent character identity, integrating image cropper tools with your existing Hugging Face dataset pipeline.

## Image Cropper Tool

### Hugging Face Space

The [Dataset Preparation Space](https://huggingface.co/spaces/malcolmrey/dataset-preparation) provides an interactive image cropping interface for dataset preprocessing.

### Key Features

- **Visual cropping interface** - Precise selection of character regions
- **Batch processing** - Efficient handling of multiple images
- **Output formats** - Compatible with standard CV pipelines
- **No-code interface** - Web-based operation

### Integration with Dataset Pipeline

```
Raw Images → Image Cropper → Cleaned Dataset → Metadata Generation → Hugging Face Upload
```

## Character Dataset Structure

### For Consistent Character Training

```
character_dataset/
├── train/
│   ├── baseline_casting/          # Neutral reference images
│   ├── facial_analysis/          # Editorial beauty analysis boards
│   ├── poses/                    # Various poses and angles
│   ├── outfits/                  # Different clothing
│   └── lighting/                 # Various lighting conditions
├── validation/
│   ├── test_angles/               # Unseen angles for validation
│   └── test_outfits/            # Unseen outfit combinations
└── metadata.jsonl                # Unified metadata file
```

### Baseline Casting Subset (Critical)

```
baseline_casting/
├── front_face/                   # Direct front view, neutral expression
├── three_quarter_left/           # 45° left angle
├── three_quarter_right/          # 45° right angle
├── profile_left/                 # Side view, left
├── profile_right/                # Side view, right
└── barefaced/                   # No makeup, hair pulled back
```

## Prompt-Driven Dataset Creation

### Automated Dataset Generation

Use your prompt system to systematically generate training data:

```python
from pathlib import Path
from prompt_system import PromptBuilder

builder = PromptBuilder()

# Generate baseline casting set
baseline_prompts = builder.generate_cartesian(
    identity="shay_face",
    poses=["neutral_expression", "calm_gaze"],
    outfits=["simple_black_swimsuit", "white_tank_leggings"],
    lighting=["flat_studio", "soft_even"],
    backgrounds=["plain_white", "neutral_gray"]
)

# Generate pose variation set
pose_prompts = builder.generate_cartesian(
    identity="shay_face",
    poses=["standing", "seated", "arms_up", "hands_on_hips"],
    outfits=["lulu_nulu_tight"],
    lighting=["soft_even"],
    backgrounds=["plain_white"]
)
```

### Metadata Generation

For each generated image, extract and record:

```jsonl
{"file_name": "baseline_front_001.jpg", "prompt": "...", "tags": ["baseline", "front"], "identity": "shay", "pose": "neutral", "outfit": "black_swimsuit", "lighting": "flat_studio"}
{"file_name": "baseline_3q_left_002.jpg", "prompt": "...", "tags": ["baseline", "three_quarter"], "identity": "shay", "pose": "neutral", "outfit": "black_swimsuit", "lighting": "flat_studio"}
```

## Image Preprocessing Pipeline

### Step 1: Cropping (Image Cropper)

Use the Hugging Face Space or local tooling to:

1. **Center crop** - Remove distracting background elements
2. **Face extraction** - Isolate facial region for identity locking
3. **Consistent aspect ratio** - Standardize across all images
4. **Remove partial shots** - Filter out obscured or partial views

### Step 2: Standardization

```python
from PIL import Image

def standardize_image(input_path, output_path, target_size=(1024, 1024)):
    """Standardize all images to consistent size and format."""
    img = Image.open(input_path)

    # Maintain aspect ratio
    img.thumbnail((target_size[0], target_size[1]), Image.LANCZOS)

    # Center pad to exact size
    background = Image.new('RGB', target_size, (255, 255, 255))
    offset = ((target_size[0] - img.width) // 2,
              (target_size[1] - img.height) // 2)
    background.paste(img, offset)

    background.save(output_path, 'JPEG', quality=95)
```

### Step 3: Quality Filtering

```python
def filter_high_quality_images(image_path, min_size=(512, 512)):
    """Filter out low-quality or small images."""
    img = Image.open(image_path)

    # Minimum resolution check
    if img.width < min_size[0] or img.height < min_size[1]:
        return False

    # Aspect ratio sanity check
    aspect_ratio = img.width / img.height
    if aspect_ratio < 0.5 or aspect_ratio > 2.0:
        return False

    return True
```

## Dataset Categories for Fine-Tuning

### 1. Identity Lock Subset (30-40% of dataset)

**Purpose**: Establish strong character identity association

- Baseline casting photos (neutral conditions)
- Front and profile views
- Barefaced portraits
- Minimal clothing variations

**Prompts**: Use identity anchors with minimal variation

```
Use the woman from reference photos. [shay_face]. Neutral expression.
Plain white background. Soft even studio lighting.
```

### 2. Pose/Angle Variation Subset (20-30% of dataset)

**Purpose**: Teach model character in different orientations

- Three-quarter views
- Profile views
- Upper body and full body
- Different camera angles

**Prompts**: Vary poses and angles

```
Use the woman from reference photos. [shay_face]. [poses: standing].
Three-quarter left view. Soft even lighting.
```

### 3. Outfit/Styling Subset (15-20% of dataset)

**Purpose**: Decouple identity from clothing

- Different outfits (swimsuit, activewear, casual)
- Minimal vs. styled hair
- Barefaced vs. light makeup

**Prompts**: Vary outfits while keeping pose/angle consistent

```
Use the woman from reference photos. [shay_face]. [outfits: lulu_nulu_tight].
[hairstyles: ponytail]. Neutral expression.
```

### 4. Lighting/Environment Subset (10-15% of dataset)

**Purpose**: Teach invariance to lighting conditions

- Soft studio lighting
- Natural window light
- Various backgrounds

**Prompts**: Vary lighting while keeping identity constant

```
Use the woman from reference photos. [shay_face]. Neutral expression.
[lighting: natural_window]. Warm background.
```

### 5. Editorial/Creative Subset (5-10% of dataset)

**Purpose**: Transfer identity to high-quality aesthetics

- Fashion editorial style
- High-contrast dramatic lighting
- Creative compositions

**Prompts**: Add creative direction

```
Use the woman from reference photos. [shay_face].
Helmut Newton-style high-contrast lighting. Dramatic low angle.
```

## Facial Analysis Board as Validation Tool

### Generating Analysis Boards

Use the editorial beauty analysis template to generate character validation sets:

```python
analysis_prompts = [
    "A minimalist editorial beauty analysis board featuring {identity} with {facial_features}. " +
    "Neutral gray background, clean studio lighting, high realism."
]
```

### Validation Workflow

1. **Generate analysis board** for each major dataset iteration
2. **Extract facial descriptors** from generated board
3. **Compare with original identity tokens** - verify consistency
4. **Update wildcards** if new descriptors are more accurate
5. **Tag dataset** with analysis board version

## Hugging Face Dataset Publishing

### Upload Process

```bash
# 1. Prepare parquet with embedded images
python create_hf_compatible_dataset.py

# 2. Push to Hugging Face Hub
cd packs/imageboard_full_archive_YYYYMMDD_HHMMSS
huggingface-cli upload your-username/character-name-dataset \
    huggingface_dataset.parquet \
    --repo-type dataset
```

### Dataset Card Template

```markdown
---
license: cc-by-4.0
task_categories:
- image-to-image
- image-captioning
tags:
- consistent-character
- identity-lock
- editorial-beauty
language:
- en
size_categories:
- 10K<n<100K
---

# Character Dataset: [Character Name]

## Dataset Description

Consistent character image dataset designed for fine-tuning text-to-image models.

### Character Identity

- Name: [Character Name]
- Age: [Age Range]
- Hair: [Hair Color, Length, Style]
- Eyes: [Eye Color]
- Skin: [Skin Tone]
- Face Shape: [Face Shape Description]

### Dataset Structure

- Total images: [N]
- Baseline casting: [N] images
- Pose variations: [N] images
- Outfit variations: [N] images
- Lighting variations: [N] images
- Editorial/creative: [N] images

### Prompts and Wildcards

All images generated using systematic prompt construction:
- Identity lock anchor in all prompts
- Wildcard-based systematic variation
- Editorial beauty analysis for validation

See [Prompt Structure Guide](PROMPT_STRUCTURE_DECONSTRUCTION.md) for details.

## Uses

### Fine-Tuning Text-to-Image Models

```python
from datasets import load_dataset
from transformers import AutoProcessor

dataset = load_dataset("your-username/character-name-dataset")
processor = AutoProcessor.from_pretrained("your-base-model")

# Load training data
train_data = dataset["train"]
```

### Character Consistency Validation

Generate editorial beauty analysis boards to verify model outputs match dataset identity.

## Dataset Creation

This dataset was generated using:
- Base model: nanobanana-3 (Gemini 3 Image Pro)
- Prompt system: [Link to prompt guide]
- Image cropper: [Hugging Face Space](https://huggingface.co/spaces/malcolmrey/dataset-preparation)
- Validation: Editorial beauty analysis boards

## Bias and Limitations

- Dataset focuses on specific character identity
- Limited diversity in poses and expressions
- Consistent lighting conditions in baseline subset
```

## Pre-Training Best Practices

### 1. Identity Lock Principle

**Never sacrifice identity for quantity.**
- Quality identity anchors > Quantity of weak references
- Prioritize baseline casting subset
- Validate identity across all generated images

### 2. Systematic Variation

Use wildcard-based generation to ensure coverage:
- Prompt each variable (pose, outfit, lighting) independently
- Avoid random generation - use structured approach
- Track which combinations have been generated

### 3. Iterative Refinement

1. **Generate initial dataset** (500-1000 images)
2. **Validate with analysis boards** - check identity consistency
3. **Identify weak areas** - which poses/outfits fail?
4. **Generate targeted supplements** - focus on weak areas
5. **Re-validate** - ensure supplements maintain identity

### 4. Dataset Sizing Guidelines

For consistent character fine-tuning:
- **Minimum viable**: 500-800 high-quality images
- **Recommended**: 1000-2000 images with balanced categories
- **High quality**: 2000+ images with extensive variation

**Quality > Quantity**: 500 perfect identity-lock images beat 2000 inconsistent images.

### 5. Validation Metrics

Track these metrics during dataset creation:

```python
# Identity consistency score
identity_score = successful_identity_matches / total_generated_images

# Prompt adherence score
prompt_score = images_matching_prompt_description / total_images

# Diversity score
diversity_score = unique_pose_outfit_combinations / possible_combinations
```

Target: Identity score > 95%, Prompt score > 90%, Diversity score > 80%

## Tooling Integration

### Complete Workflow

```
1. Prompt System
   ↓
2. Batch Generation (ComfyUI / Nano Banana Pro)
   ↓
3. Image Cropper (Hugging Face Space / Local)
   ↓
4. Quality Filtering
   ↓
5. Metadata Generation
   ↓
6. Analysis Board Validation
   ↓
7. Hugging Face Upload
```

### Automation Scripts

```bash
# Generate dataset from prompts
python generate_dataset.py --config dataset_config.json

# Process and filter images
python preprocess_dataset.py --input generated/ --output processed/

# Create Hugging Face parquet
python create_hf_compatible_dataset.py

# Push to Hub
python push_to_hf.py --dataset-name character-name
```

## Related Documentation

- [Facial Analysis Guide](FACIAL_ANALYSIS_GUIDE.md) - Character validation workflow
- [Prompt Structure Deconstruction](PROMPT_STRUCTURE_DECONSTRUCTION.md) - Prompt engineering
- [Dataset Quick Start](../docs/dataset-quickstart.md) - Hugging Face pipeline
- [Wildcards](wildcards/) - Modular prompt elements
