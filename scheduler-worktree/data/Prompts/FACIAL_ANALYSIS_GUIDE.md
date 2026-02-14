# Facial Analysis & Character Consistency Guide

## Overview

This guide explains how to use the Editorial Beauty Analysis template for validating and maintaining consistent character likeness across generations with Nano Banana Pro.

## Template Structure

The Editorial Beauty Analysis template is located in [Universal-Assets.md](Universal-Assets.md) and provides a systematic approach to facial analysis.

### Key Components

1. **Analysis Board Layout**: Multi-section editorial format showing barefaced vs. makeup states
2. **Face Shape Tracing**: Visual guide (blue outline) for identifying facial proportions
3. **Feature Documentation**: Bullet-point descriptions of facial characteristics
4. **Comparison Views**: Straight-on and three-quarter profile angles

## Usage Workflow

### Step 1: Initial Character Setup

Start with reference images and identity descriptors:

```python
subject = "A woman in her mid-20s with long dark brown hair, brown eyes, fair skin"
facial_features = "balanced oval face shape, softly pronounced cheekbones, feminine and delicate jawline"
```

### Step 2: Generate Facial Analysis

Use the template with your character:

```
A minimalist editorial beauty analysis board featuring [IDENTITY] with [FACIAL_FEATURES]. 
Neutral gray background, clean studio lighting, high realism.
```

This generates a character validation board showing:
- Barefaced baseline state (no styling distractions)
- Natural proportions and symmetry
- Facial structure documentation

### Step 3: Extract Descriptors

From the generated analysis board, extract the facial feature descriptors that the model produces. These become your character's permanent identity tokens.

### Step 4: Incorporate into Wildcards

Add extracted descriptors to [facial_features.md](wildcards/facial_features.md):

```markdown
## shay_face
- **Short**: "Shay's face"
- **Description**: [extracted from analysis board]
```

## Prompt Construction Pattern

### Full Editorial Analysis Prompt

```
{subject} with {facial_features}. Neutral gray background, clean studio lighting, high realism.

Top section: front-facing barefaced portrait, natural skin texture, no makeup, hair pulled back.
Right side: graphic text layout titled 'FACE' with {facial_features_list}.
Middle section: two studio portraits labeled 'barefaced' (straight-on + 3/4 profile).
Bottom section: two images labeled 'with makeup', {makeup_style}.
```

### Negative Prompt

```
exaggerated makeup, heavy contour, harsh shadows, cartoon style, anime, 
distorted facial proportions, overly sharp jawline, low resolution, 
oversaturated colors, messy layout, watermark, logo, text artifacts, 
duplicated faces, extra limbs
```

## Technical Parameters

```json
{
  "style": "editorial beauty photography",
  "quality": "high",
  "lighting": "soft studio lighting",
  "background": "neutral gray"
}
```

## Best Practices

### 1. Establish Baseline First

Always start with barefaced analysis before adding styling elements. This removes hair and makeup variables that can obscure facial structure.

### 2. Use Neutral Expressions

Calm neutral expression prevents dynamic facial movements from affecting proportion analysis.

### 3. Multiple Angles

Capture both straight-on and three-quarter profile views to verify 3D consistency.

### 4. Compare States

Generate both barefaced and with-makeup versions to understand how styling affects perceived features.

### 5. Document Variations

If the model produces slightly different facial interpretations, document all variations and select the most consistent elements.

## Integration with Wildcard System

The facial features wildcard integrates with the existing prompt system:

```
Identity Lock + [facial_features] + [hairstyles] + [outfits] + [poses]
```

Example complete prompt construction:
```
Use the woman from reference photos as subject. [shay_face]. [hairstyles: claw_clip_half_up]. 
[poses: neutral_expression]. Soft studio lighting, neutral background.
```

## Troubleshooting

### Issue: Inconsistent Jawline

**Solution**: Run facial analysis board focusing on jawline descriptions. Use the "delicate jawline" descriptor consistently.

### Issue: Eye Shape Variations

**Solution**: Generate barefaced portraits with "hair pulled back" specification. Extract the eye shape description the model produces.

### Issue: Nose Structure Changes

**Solution**: Use three-quarter profile view from analysis board to establish consistent nose bridge and tip descriptions.

## Example: Shay Character

### Generated Descriptors

From analysis boards, Shay's facial features were identified as:
- Face: Balanced oval-to-heart shape
- Jawline: Feminine and delicate
- Cheekbones: Softly pronounced
- Chin: Slightly tapered natural
- Nose: Straight to softly contoured bridge
- Eyes: Clear almond-to-rounded with soft gaze

### Wildcard Entry

```markdown
## shay_face
- **Short**: "Shay's oval face"
- **Description**: balanced oval-to-heart face shape, softly pronounced cheekbones, 
feminine and delicate jawline, slightly tapered natural chin, straight to softly 
contoured nose bridge, clear almond-to-rounded eyes with soft gaze
```

### Usage in Prompts

```
Use the woman from reference photos. [shay_face]. [editorial_barefaced] for 
baseline validation. [claw_clip_half_up] hair. Soft studio lighting.
```

## Related Templates

- [Identity & Face Lock](identity.md) - Core character traits
- [Facial Features Wildcard](wildcards/facial_features.md) - Modular descriptors
- [Subject-Shay.md](Subject-Shay.md) - Complete character reference
- [Universal Assets](Universal-Assets.md) - Full analysis template

## Model Notes

This template is optimized for **nanobanana-3 (Gemini 3 Image Pro)** which excels at:
- Facial realism and proportion accuracy
- Natural skin texture representation
- Editorial photography aesthetics
- Structured analysis board generation

The model's strength in understanding natural language descriptions allows for precise facial feature specification and consistent character reproduction.
