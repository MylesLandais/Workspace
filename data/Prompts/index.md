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

- [Identity & Face Lock](identity.md) - Character consistency tokens and base identity template
- [Main Character Reference](Subject-Shay.md) - High-level character overview

### Wildcard Categories

- [Hairstyles](wildcards/hairstyles.md) - Hair styling variations (down, ponytail, claw clip, updo, etc.)
- [Outfits](wildcards/outfits.md) - Clothing options and descriptions
- [Poses](wildcards/poses.md) - Expression and angle combinations
- [Framing](wildcards/framing.md) - Camera framing options (head-shoulders, medium-shot, back-view, etc.)
- [Lighting](wildcards/lighting.md) - Lighting scenarios and environments
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

- **Hairstyles**: 5 variations
- **Outfits**: 13 variations
- **Poses**: 19 variations
- **Framing**: 7 variations
- **Lighting**: 12 variations
- **Backgrounds**: 20 variations

**Total Possible Combinations**: 5 × 13 × 19 × 7 × 12 × 20 = 2,074,800 combinations

## Static Web Publishing

This guide is designed for static site generators (Jekyll, Hugo, etc.). All files are in Markdown format for easy rendering to HTML.

## License & Usage

This prompt guide is for character consistency in image generation. Maintain character identity while exploring stylistic variations.

## Universal Assets

See [Universal Assets](Universal-Assets.md) for standardized templates and recommendations.

