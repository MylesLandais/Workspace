# Duplicate Detection & Quality-Based Stacking

## Problem
Media content exists in multiple variants (high-quality originals, screenshots with UI elements, resized versions). Need to automatically group duplicates and identify the canonical source.

## Approach

### Two-Layer Similarity Detection

1. **Perceptual Hashing** (dHash/pHash)
   - Fast near-duplicate detection
   - Handles resizing, minor watermarks
   - Hamming distance < 5 = match

2. **Visual Embeddings** (CLIP/SSCD)
   - Semantic matching across variants
   - Links screenshots to original video/content
   - Handles cropping, overlays, color changes

### Quality Scoring Heuristic

Rank images to identify source vs derivative:
- Resolution (width × height)
- Phone aspect ratio penalty (9:19.5, 9:20)
- UI element detection (OCR for text overlays, edge detection for bars)
- Highest score = canonical source

### Stacking Architecture

- Graph structure: `IS_DERIVATIVE_OF` edges
- Parent node = highest quality score
- Children preserve metadata (timestamps, UI text)
- Display canonical, search derivatives

### Person-Specific Enhancements

- Face recognition (insightface) to prevent false matches
- OCR dates from screenshots to backfill metadata






