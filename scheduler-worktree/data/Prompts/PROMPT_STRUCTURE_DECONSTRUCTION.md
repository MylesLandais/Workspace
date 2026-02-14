# Prompt Structure Deconstruction

## Overview

This document breaks down the anatomy of effective prompts for consistent character generation with Nano Banana Pro. Understanding prompt structure enables systematic iteration and predictable results.

## Production-Grade Prompt Structure

### Section 1: Subject / Identity Lock

**Purpose**: Lock character features across all generations with explicit, unambiguous language.

```
Use the woman from the provided reference images as the subject. Her identity must match
the reference exactly: same face, bone structure, proportions, skin tone, body shape, and
natural features. Do not alter facial geometry, eye spacing, nose shape, jawline, lips, or
body proportions. This is a 1:1 identity match to the reference photos.

She is a woman in her mid-20s with long dark brown hair, warm brown-hazel eyes, fair skin
with visible natural texture, and defined facial features. No beautification beyond realistic
studio photography.
```

**Key Elements**:
- Explicit reference image instruction
- Feature list: face, bone structure, proportions, skin tone, body shape, natural features
- Identity guarantee: "exactly", "1:1 identity match"
- Negative constraint: "Do not alter facial geometry..."
- Age range and basic characteristics
- Realistic constraint: "No beautification beyond realistic studio photography"

**Best Practice**: Always lead with identity anchor. This is non-negotiable for consistency. Use maximum explicitness for identity features.

### Section 2: Wardrobe

**Purpose**: Define clothing with retail-catalog level detail.

```
She is wearing the [COSTUME NAME]:

- [Garment 1] with [specific details: material, cut, closures]
- [Garment 2] with [specific details]
- [Accessories] with [specific details]

Costume should appear accurate to retail catalog photography, properly fitted, showing
natural body shape with realistic fabric tension and seams.
```

**Key Elements**:
- Costume/product name
- Bulleted list of all garment pieces
- Specific details: materials, cuts, closures, patterns
- Fitting guidance: "accurate to retail catalog photography"
- Fabric behavior: "realistic fabric tension and seams"

**Best Practice**: Use retail-catalog language. List every component. Specify how fabric should appear on body.

### Section 3: Pose & Framing

**Purpose**: Specify body positioning and camera composition.

```
Full-body studio casting photo.
Standing straight, facing the camera.
Both hands placed naturally on hips, elbows slightly outward.
Confident, neutral stance.
Eye-level camera angle.
Full frame, edge-to-edge, no borders or cropping.
```

**Key Elements**:
- Shot type: full-body, headshot, 3/4 body
- Subject state: standing, seated, action
- Pose description: body position, limb placement
- Attitude: confident, neutral, relaxed
- Camera angle: eye-level, low-angle, high-angle
- Framing: full frame, edge-to-edge, no cropping

**Best Practice**: Include camera framing and angle. Specify limb position explicitly. Use edge-to-edge language for consistent cropping.

### Section 4: Photography Style

**Purpose**: Define visual aesthetic and realism level.

```
High-end fashion catalog photography.
Realistic skin texture, visible pores, natural complexion.
Raw, authentic photo style — not airbrushed, not stylized.
True-to-life proportions and anatomy.
```

**Key Elements**:
- Style/Genre: catalog, editorial, portrait
- Skin detail: visible pores, natural texture
- Aesthetic: raw, authentic, not airbrushed
- Proportions: true-to-life
- Negative constraints: "not airbrushed, not stylized"

**Best Practice**: Use "high-end fashion catalog" for consistent retail aesthetics. Specify raw/authentic over stylized.

### Section 5: Technical Capture

**Purpose**: Define camera, lens, and quality specifications.

```
Simulated high-definition digital capture using a Phase One medium-format camera.
50–70mm lens equivalent.
Crystal-clear sharpness, no motion blur, no noise.
Ultra-high resolution, 8K quality.
```

**Key Elements**:
- Camera: brand, system (medium-format)
- Lens: focal length equivalent
- Quality: sharpness, blur control, noise
- Resolution: 8K, ultra-high

**Best Practice**: Use Phase One for catalog work. Specify 50-70mm for flattering portrait distortion. 8K resolution for quality.

### Section 6: Lighting & Background

**Purpose**: Define lighting quality and environment.

```
Flat, even studio lighting.
Soft, diffused light with no harsh shadows or dramatic contrast.
Clean white seamless studio background.
Neutral color balance.
```

**Key Elements**:
- Lighting type: flat, even, studio
- Quality: soft, diffused
- Negative constraints: no harsh shadows, no dramatic contrast
- Background: clean white seamless
- Color balance: neutral

**Best Practice**: Use "flat, even studio lighting" for catalog work. Specify negative lighting constraints to prevent stylization.

### Section 7: Negative Prompt (Strongly Recommended)

**Purpose**: Explicitly prevent unwanted outputs.

```
Do not:
- Change facial identity, age, ethnicity, or body shape
- Stylize the face or body (no anime, CGI, illustration, or painterly looks)
- Add beauty filters, smoothing, or plastic skin
- Add props not listed
- Crop the body or cut off limbs
- Introduce shadows, dramatic lighting, rim light, or colored gels
- Use cinematic grading, HDR, glow, or vignette
- Add logos, watermarks, text overlays, or borders
- Sexualize pose or exaggerate anatomy

No fantasy, cosplay exaggeration, or AI-art artifacts.
```

**Key Elements**:
- Identity protection: no changes to face, age, ethnicity, body
- Style protection: no stylization, CGI, anime
- Skin protection: no filters, smoothing
- Props: only listed props allowed
- Framing: no cropping or limb loss
- Lighting: no dramatic or colored lighting
- Post-processing: no grading, HDR, vignette
- Extra elements: no logos, watermarks, text
- Content: no sexualization or exaggeration

**Best Practice**: Always include negative prompt. Use bullet points for clarity. Cover identity, style, and technical categories.

## Prompt Layers (Legacy Format)

### Layer 1: Identity Anchor
### Layer 2: Core Subject Description
### Layer 3: Pose & Action
### Layer 4: Technical Photography Specifications
### Layer 5: Stylization & Creative Elements (Optional)

(Legacy sections remain for backward compatibility with existing prompts)

## Complete Prompt Template

```
{IDENTITY_ANCHOR}

{CORE_SUBJECT}
{POSE_ACTION}

{TECHNICAL_SPECIFICATIONS}

{OPTIONAL_STYLIZATION}
```

## Prompt Deconstruction Examples

### Example 1: Baseline Casting Photo

```
Use the woman from the reference images as the subject, keeping her face, bone structure, 
skin tone, and body characteristics exactly identical to the reference photos.

Full body studio casting photo. She is wearing a simple solid black two-piece swimsuit 
with classic fit, showing natural body shape.

Pose: Standing straight facing camera, both hands placed naturally on hips, elbows slightly 
out, neutral stance. Shows shoulder structure and natural posture.

High-end swimwear catalog, professional model casting digitals. Realistic skin texture, 
raw photo style, natural proportions, authentic representation.

Full frame, borderless image extending edge-to-edge. Plain white studio background.
High-definition digital capture, Phase One camera system, 50-70mm lens, 
crystal clear sharpness, noise-free, 8k resolution.

Flat even studio lighting, soft diffused, no shadows, no dramatic contrast. 
Shot at eye level.
```

**Layers**:
1. Identity: "Use the woman from reference photos...exactly identical"
2. Subject: "Full body studio casting photo...black two-piece swimsuit"
3. Pose: "Standing straight facing camera, hands on hips"
4. Technical: "Phase One camera, 50-70mm lens, 8k resolution, flat lighting"

**Purpose**: Establish baseline character in neutral conditions.

### Example 2: High-Fashion Editorial

```
Use the woman from the reference images as the subject, keeping her exact facial features, 
bone structure, skin tone identical to reference.

A high-fashion Wolford-inspired studio digital of the consistent character from the 
reference photos.

Setting & Prop: She is seated in a transparent Kartell Louis Ghost Chair.
Pose & Angle: Captured from a dramatic low-angle (worm's-eye view). She is sitting with 
her legs crossed at the thighs, extending toward the camera.

Attire: A minimalist matte black tube top and professional sheer 20-denier black hosiery 
with a subtle satin sheen. The hosiery features a sharp, visible central seam.

Lighting: Helmut Newton-style high-contrast studio lighting. A strong key light from the 
side creates a 'rim light' highlight along the curves of the legs.

Technical: Shot with a 24mm wide-angle lens to intentionally elongate the limbs. 
8k resolution, Phase One camera system, crystal clear sharpness, noise-free, 
ultra-realistic textures.
```

**Layers**:
1. Identity: Same as baseline
2. Subject: "High-fashion Wolford-inspired studio digital"
3. Pose: "Seated in Ghost Chair, legs crossed, low-angle"
4. Technical: "24mm wide-angle lens, Helmut Newton lighting, high-contrast"

**Purpose**: Creative direction while maintaining identity.

### Example 3: Facial Analysis Board

```
A minimalist editorial beauty analysis board featuring {subject} with {facial_features}. 
Neutral gray background, clean studio lighting, high realism.

Top section: front-facing barefaced portrait, natural skin texture, no makeup, 
hair pulled back. A thin blue outline tracing the face shape.

Right side graphic text layout titled 'FACE' with small bullet points describing: 
{facial_features_list}.

Middle section: two studio portraits labeled 'barefaced', one straight-on view and 
one three-quarter profile.

Bottom section: two mirror selfie style images labeled 'with makeup', {makeup_style}, 
contemporary fashion styling.

Fashion magazine editorial layout, clean modern typography, balanced spacing, 
muted neutral tones, professional beauty photography, high resolution.
```

**Layers**:
1. Subject: "Editorial beauty analysis board featuring [character]"
2. Structure: Multi-section layout specification
3. Technical: "Neutral gray background, clean studio lighting, high resolution"

**Purpose**: Character validation and descriptor extraction.

## Prompt Engineering Principles

### 1. Identity-First Approach

Always establish character identity before any other element. The model must know who it's generating before knowing what they're doing or how they look.

**Good**: "Use the woman from reference... Standing in yoga pose..."
**Bad**: "Yoga pose featuring woman with brown hair from reference..."

### 2. Specific Technical Vocabulary

Use photography terminology the model understands:
- Camera: "Phase One", "Canon EOS R5"
- Lens: "50-70mm", "24mm wide-angle", "85mm f/2.8"
- Lighting: "soft diffused", "flat even", "high-contrast"
- Style: "editorial", "catalog", "casting digitals"

### 3. Separation of Concerns

Keep different aspects in separate sections:
- Identity anchor
- Subject/outfit
- Pose/action
- Technical specs

This prevents feature bleeding between elements.

### 4. Wildcard Integration

The prompt system supports wildcard substitution for systematic variation:

```
Use the woman from reference. [shay_face]. [hairstyles: claw_clip_half_up]. 
[outfits: lulu_nulu_tight]. [poses: neutral_expression].
```

### 5. Negative Prompt Synergy

Negative prompt should reinforce positive prompt direction:

```
Positive: "editorial beauty analysis, soft studio lighting"
Negative: "harsh shadows, dramatic contrast"
```

## Common Pitfalls

### 1. Missing Identity Anchor

**Problem**: Character changes across generations.

**Fix**: Always include explicit identity reference at prompt start.

### 2. Inconsistent Technical Specs

**Problem**: 8k resolution in one prompt, no resolution in another.

**Fix**: Use Universal Assets technical tokens consistently.

### 3. Conflicting Directions

**Problem**: "soft diffused lighting" + "high contrast dramatic shadows"

**Fix**: Ensure all prompt elements support the same aesthetic.

### 4. Over-Specifying Creative Elements

**Problem**: Too many style references confuse the model.

**Fix**: Start with identity + basic pose, then layer style elements one at a time.

### 5. Neglecting Baseline Generation

**Problem**: Jumping straight to stylized shots without establishing character baseline.

**Fix**: Always generate neutral casting photos first to lock identity.

## Reference Documents

- [Identity & Face Lock](identity.md) - Core identity tokens
- [Facial Analysis Guide](FACIAL_ANALYSIS_GUIDE.md) - Character validation workflow
- [Wildcard Categories](wildcards/) - Modular prompt elements
- [Universal Assets](Universal-Assets.md) - Standardized templates

## Model-Specific Notes

**Target Model**: nanobanana-3 (Gemini 3 Image Pro)

The model excels at:
- Natural language understanding
- Photography terminology interpretation
- Facial realism and proportion accuracy
- Editorial aesthetics

Prompt structure should leverage these strengths with precise, professional language.
