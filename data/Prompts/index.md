# Shay Character Prompt Guide

## Overview

This guide provides a modular wildcard-based prompt system for generating consistent character images of Shay using nanobanana-3 (Gemini 3 Image Pro). The system separates identity constants from variable elements, allowing systematic iteration over the diversity space.

## System Architecture

The prompt system consists of:

1. **Identity Lock** - Core character traits that remain constant
2. **Wildcard Categories** - Variable elements that can be combined
3. **Batch Generator** - Automated prompt combination tool

## Navigation

### Core Files

- [Production-Grade Prompt Template](PRODUCTION_PROMPT_TEMPLATE.md) - Retail-catalog quality prompt structure with explicit identity lock
- [Sora Master Prompts](SORA_MASTER_PROMPTS.md) - Complete Sora-ready prompts with carousel sequences and pose variations
- [Quick Prompt: Seated Baton](QUICK_PROMPT_SEATED_BATON.md) - Ready-to-use prompt for vertical baton seated pose
- [Quick Prompt: Kissing Baton](QUICK_PROMPT_KISSING_BATON.md) - Ready-to-use VIP/tease prompt (exclusive content)
- [Racy Referee 2009 Variations](SHAY_RACY_REFEREE_2009_VARIATIONS.md) - 20+ variations in 2009 MySpace/emo aesthetic with asymmetric scene hair
- [Racy Referee Wildcard Tests](SHAY_REFEREE_WILDCARD_TESTS.md) - 8 test prompts using wildcard combinations (emo/MySpace vibe)
- [Racy Referee Polished GF Tests](SHAY_REFEREE_POLISHED_GF_TESTS.md) - 8 test prompts with polished girlfriend-message aesthetic (smooth touchup, clean, bright)
- [Racy Referee Aesthetic Comparison](SHAY_REFEREE_AESTHETIC_COMPARISON.md) - Side-by-side comparison of 2009 emo vs polished girlfriend vibe, usage guidelines
- [Shay's Bedroom Environment](SHAY_BEDROOM_ENVIRONMENT.md) - Detailed reference for Shay's bedroom: lilac purple walls, warm 2700K lighting, fairy lights
- [Prompt Pairings Guide](PROMPT_PAIRINGS.md) - Optimal pose + prop + footwear combinations and carousel sequencing
- [Identity & Face Lock](identity.md) - Character consistency tokens and base identity template
- [Facial Analysis Guide](FACIAL_ANALYSIS_GUIDE.md) - Using editorial beauty analysis for character consistency
- [Prompt Structure Deconstruction](PROMPT_STRUCTURE_DECONSTRUCTION.md) - Anatomy of effective prompts for consistent character generation
- [Dataset Preparation](DATASET_PREPARATION.md) - Pre-training dataset creation and management for consistent character fine-tuning
- [Image Cropper Guide](IMAGE_CROPPER_GUIDE.md) - Using Hugging Face Space for image cropping
- [Main Character Reference](Subject-Shay.md) - High-level character overview
- [Shay Yoga & Fitness](Subject-Shay-Yoga.md) - Complete ComfyUI-ready yoga and fitness workout prompts

### Wildcard Categories

- [Hairstyles](wildcards/hairstyles.md) - Hair styling variations (down, ponytail, claw clip, updo, etc.)
- [Outfits](wildcards/outfits.md) - Clothing options and descriptions (costumes, streetwear, vinyl jackets)
- [Footwear](wildcards/footwear.md) - Luxury footwear options (Louboutin stilettos, chunky sneakers, streetwear)
- [Hosiery & Accessories](wildcards/hosiery.md) - Hosiery, socks, and accessory options (fishnet tights, knee-high socks)
- [Poses](wildcards/poses.md) - Expression and angle combinations (crouching, seated authority, VIP teasing)
  - [Yoga Poses](wildcards/yoga_poses.md) - Full-body yoga poses and sequences (universal templates)
- [Actions & Props](wildcards/actions.md) - Hand and prop actions (whistle, clothing interactions, body movements)
- [Props](wildcards/props.md) - Training props and police accessories (inversion table, ballet barre, baton, handcuffs)
- [Expressions & Vibes](wildcards/expressions.md) - Emotional expressions and atmospheric vibes (romantic, tease, countdown, 2009 emo, soft neutral)
- [Facial Features](wildcards/facial_features.md) - Facial analysis and beauty descriptors (face shape, symmetry, eye style, barefaced, makeup)
- [Composition](wildcards/composition.md) - Visual arrangement and shot composition (framing, balance, depth, perspective, dynamic vs static) **[NEW - replaces framing]**
- [Lighting](wildcards/lighting.md) - Lighting scenarios, moods, and nostalgic camera styles
- [Backgrounds](wildcards/backgrounds.md) - Background and environment options

## Usage

### Manual Prompt Construction

1. Start with the [base identity template](identity.md#base-identity-template-for-nanobanana-3)
2. Select one option from each wildcard category
3. Combine into a complete prompt

### Automated Batch Generation

Use `batch_generator.py` to:
- Generate full cartesian product of all wildcard combinations
- Create curated subsets (e.g., 16 or 32 image datasets)
- Randomly sample combinations for variety
- Export prompts tagged for nanobanana-3

## Target Model

**nanobanana-3** (Gemini 3 Image Pro) only.

All prompts are optimized for this model's natural language understanding and image generation capabilities.

## Quick Reference

### Character Identity

- **Name**: Shay
- **Heritage**: Polish-American
- **Age Appearance**: 25-30 range
- **Skin**: Fair with warm undertones, natural freckles on nose and cheeks
- **Hair**: Dark brown, straight, long (chest-length), center part
- **Eyes**: Warm brown, almond-shaped
- **Face Shape**: Oval with defined but soft jawline

### Key Wildcard Counts

- **Hairstyles**: 12 variations (5 standard + 7 2009 emo/scene asymmetric styles)
- **Outfits**: 15 variations (including Stop Traffic and Racy Referee costumes + 5 streetwear/sneakers)
- **Footwear**: 10 variations (3 Louboutin + costume Mary Jane platform + 6 streetwear/sneakers)
- **Hosiery & Accessories**: 7 variations (2 basic + 5 fishnet/tights)
- **Poses**: 37 variations (facial expressions, head angles, Instagram, VIP, car window, basement, seated authority, seated teasing + 7 crouching variations)
- **Actions & Props**: 13 variations (whistle actions, costume interactions, body movements)
- **Yoga Poses**: 37+ variations (full-body poses, sequences, and handstand progressions)
- **Props**: 16 variations (9 police/sports accessories + 7 fitness/yoga props)
- **Expressions & Vibes**: 25 variations (romantic, playful tease, countdown, 2009 emo, referee-specific, polished girlfriend messages + 6 soft/neutral expressions)
- **Facial Features**: 5 variations (face shape, symmetry, eye style, barefaced, makeup)
- **Composition**: 30+ variations (shot types, camera angles, balance & symmetry, dynamic vs static, intimacy & distance, framing within frame, smartphone/mobile style, polished girlfriend message)
- **Lighting**: 18 variations (12 standard + 3 mood/nostalgic camera styles + 3 polished girlfriend touchup)
- **Backgrounds**: 21 variations (20 standard + 1 Shay's bedroom specific)

**Recent Updates (Feb 2026)**:
- **Composition refactor**: `framing` → `composition` (broader art term covering framing, balance, depth, perspective)
- **New streetwear wildcards**: vinyl jackets, chunky sneakers, fishnet tights
- **New poses**: crouching variations for dynamic fashion photography
- **New expressions**: soft neutral, looking down, contemplative, shy
- **Updated batch_generator.py**: Now uses `composition` wildcard category

**Note**: Yoga poses, actions, expressions, and vibes are universal templates and can be combined with any character identity and other wildcards. These abstract concepts are designed for reuse across different characters and scenarios.

## Static Web Publishing

This guide is designed for static site generators (Jekyll, Hugo, etc.). All files are in Markdown format for easy rendering to HTML.

## Character-Specific Environments

See [Shay's Bedroom Environment](SHAY_BEDROOM_ENVIRONMENT.md) for detailed reference to her personal space including:
- Lilac purple painted walls
- Warm 2700K lighting
- Fairy lights creating soft bokeh
- Compatible outfit, hairstyle, and expression combinations
- Time-of-day variations (daytime, nighttime, golden hour)

## License & Usage

This prompt guide is for character consistency in image generation. Maintain character identity while exploring stylistic variations.

## Universal Assets

- [Universal Assets](Universal-Assets.md) - Standardized templates and recommendations
- [Cinematography Techniques](Cinematography-Techniques.md) - Camera movement, orbital pans, and cinematic sequence strategies for Nano Banana AIO
- [Handstand Orbital 360° Prompts](shay_handstand_orbital_360_prompts.txt) - Complete handstand progression sequence with bullet-time orbital pans (11 prompts: 7 basic progression + 4 prop-assisted variations with inversion table and ballet barre)
- [Handstand Orbital 360° (JSON)](shay_handstand_orbital_360_prompts.json) - Machine-readable JSON version for automated processing





