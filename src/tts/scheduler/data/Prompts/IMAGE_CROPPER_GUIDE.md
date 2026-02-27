# Image Cropper Quick Guide

## Overview

Quick reference for using the [Dataset Preparation Hugging Face Space](https://huggingface.co/spaces/malcolmrey/dataset-preparation) to crop images for character datasets.

## Access

**URL**: https://huggingface.co/spaces/malcolmrey/dataset-preparation

## Workflow

### Step 1: Upload Images

1. Navigate to the Hugging Face Space
2. Upload your generated images (batch upload supported)
3. Wait for processing to complete

### Step 2: Crop Each Image

For each image:
1. Review the image preview
2. Draw crop box around character region
3. Keep consistent aspect ratio across all images (recommended: 1:1 or 4:5)
4. Save cropped output

### Step 3: Download Results

1. After cropping all images, download the processed batch
2. Extract to your dataset directory
3. Verify crop consistency

## Cropping Guidelines for Character Datasets

### Baseline Casting Photos

**Goal**: Maximize facial visibility and clean background

- **Crop**: From mid-chest to top of head (exclude shoulders if distracting)
- **Aspect Ratio**: 1:1 (square) for consistent face focus
- **Padding**: Leave ~10% breathing room around face
- **Background**: Remove if possible, crop to character only

### Full Body Shots

**Goal**: Show complete character form

- **Crop**: Include full body, minimal background
- **Aspect Ratio**: 4:5 or 3:4 (portrait)
- **Padding**: Minimal, tight to body
- **Alignment**: Center character in frame

### Editorial/Artistic Shots

**Goal**: Preserve artistic composition while cleaning background

- **Crop**: Maintain intended composition
- **Aspect Ratio**: Match original artistic intent
- **Background**: Keep if integral to image, remove if distracting
- **Focus**: Ensure character is primary subject

## Consistency Rules

### Rule 1: Uniform Aspect Ratio

Choose ONE aspect ratio for your entire dataset:
- **1:1 (Square)**: Best for facial identity training
- **4:5 (Portrait)**: Best for full body shots
- **3:4 (Landscape)**: Best for environmental shots

### Rule 2: Consistent Subject Position

- Center character in all crops
- Maintain same head-to-body ratio across similar shot types
- Leave consistent padding amounts

### Rule 3: Quality Threshold

- Minimum resolution: 512x512 for identity training
- Recommended resolution: 1024x1024 or higher
- Reject images where crop reduces quality below threshold

## Naming Convention

After cropping, rename files systematically:

```
[character]_[shot_type]_[angle]_[number].jpg

Examples:
- shay_baseline_front_001.jpg
- shay_pose_standing_3q_left_042.jpg
- shay_outfit_swimsuit_side_089.jpg
```

## Integration with Dataset Pipeline

### Local Scripting

If using the Hugging Face Space repeatedly, consider local automation:

```python
import requests
from pathlib import Path

def batch_crop_images(image_dir, output_dir):
    """Batch upload and crop using Hugging Face Space API."""
    # Note: Check Space documentation for specific API endpoints
    pass

# Or use local cropper for bulk processing
from PIL import Image

def local_crop(image_path, output_path, crop_box):
    """Local cropping as alternative to Hugging Face Space."""
    img = Image.open(image_path)
    cropped = img.crop(crop_box)
    cropped.save(output_path)
```

### Alternative: Local Tools

Consider local tools for large batches:
- Python Pillow (PIL) for scripted cropping
- OpenCV for automated face detection crops
- Labelbox or similar for annotated cropping

## Quality Control

After cropping, validate:

```python
from PIL import Image

def validate_cropped_image(image_path):
    """Validate cropped image meets quality standards."""
    img = Image.open(image_path)

    # Size check
    if img.width < 512 or img.height < 512:
        return False, "Too small"

    # Aspect ratio check
    ratio = img.width / img.height
    if ratio < 0.8 or ratio > 1.2:
        return False, "Aspect ratio inconsistent"

    # Visual check (manual)
    # Verify character is properly centered
    # Verify no important features cropped
    # Verify background is clean

    return True, "OK"
```

## Troubleshooting

### Issue: Crop box doesn't match image

**Solution**: Check if image loaded correctly. Try different browser or re-upload.

### Issue: Cropped images are too small

**Solution**: Upload higher resolution source images (minimum 1024px on longest side).

### Issue: Consistent cropping across batch

**Solution**: Use reference crop dimensions for first image, apply similar for rest.

## Related Documentation

- [Dataset Preparation](DATASET_PREPARATION.md) - Complete dataset creation workflow
- [Facial Analysis Guide](FACIAL_ANALYSIS_GUIDE.md) - Character validation
- [Prompt Structure Deconstruction](PROMPT_STRUCTURE_DECONSTRUCTION.md) - Prompt generation
