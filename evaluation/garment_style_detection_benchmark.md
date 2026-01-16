# Garment Style Detection Benchmark

## Task Description

**Objective**: Identify the specific style of yoga pants/leggings from an image and match it to an internal garment ontology, then link to e-commerce products for price tracking.

## Test Image

**Image Description**: A person wearing black yoga pants with distinctive sheer/mesh panels running vertically along the outer side of both thighs and calves.

**Key Features to Detect**:
- **Garment Type**: Yoga Pants / Leggings
- **Color**: Black
- **Style Feature**: Sheer/Mesh Panels (vertical, outer thigh and calf)
- **Fit**: Compression/Form-fitting
- **Length**: Full-length (ankle-length)
- **Material**: Polyester/Spandex blend (typical athletic material)
- **Waist**: Standard or high-waisted (not clearly visible)

## Expected Output

### 1. Style Classification
```json
{
  "garment_type": "Yoga Pants",
  "category": "Bottoms",
  "primary_style": "Sheer Panel",
  "color": "Black",
  "fit": "Compression",
  "length": "Full Length",
  "material": "Polyester/Spandex",
  "detected_features": [
    "sheer_panel_thigh",
    "sheer_panel_calf",
    "vertical_panels",
    "compression_fit",
    "full_length"
  ]
}
```

### 2. Ontology Match
- **GarmentStyle Node**: "Sheer Panel Yoga Pants"
- **Style Features**:
  - Panel Style: Sheer Panel
  - Fit Style: Compression
  - Length Style: Full Length
  - Color: Black
  - Material Type: Polyester/Spandex

### 3. Product Matching
Match to e-commerce products with:
- Similar panel style (sheer/mesh panels)
- Same color (black)
- Similar fit (compression)
- Price tracking enabled

### 4. Marketplace Links
Provide Depop/other marketplace search links:
- Search terms: "sheer panel yoga pants black"
- Search terms: "mesh panel leggings black"
- Track specific product listings

## Evaluation Metrics

1. **Style Detection Accuracy**
   - Correct garment type identification
   - Correct style feature detection (panel type, fit, length)
   - Feature completeness score

2. **Ontology Matching**
   - Correct style node creation
   - Feature relationship accuracy
   - Variation detection (if applicable)

3. **Product Matching**
   - Match confidence scores
   - Relevant product retrieval rate
   - False positive rate

4. **Price Tracking Setup**
   - Successful marketplace link creation
   - Price history tracking initialization
   - Availability monitoring setup

## Implementation Steps

1. **Image Analysis** (Computer Vision)
   - Detect garment type
   - Identify style features (panels, fit, length)
   - Extract color and material cues

2. **Ontology Creation**
   - Create/update GarmentStyle node
   - Create StyleFeature nodes
   - Link features to style

3. **Product Matching**
   - Search e-commerce platforms
   - Match products to style
   - Create ProductMatch relationships

4. **Price Tracking Setup**
   - Add products to tracking queue
   - Set up periodic price checks
   - Initialize availability monitoring

## Success Criteria

- [ ] Correctly identifies "Sheer Panel Yoga Pants" style
- [ ] Creates appropriate ontology nodes and relationships
- [ ] Matches to at least 3 relevant e-commerce products
- [ ] Sets up price tracking for matched products
- [ ] Provides marketplace search links
- [ ] Enables market condition analysis

## Future Enhancements

- Multi-image comparison (same garment from different angles)
- Style variation detection (color variations, size variations)
- Brand identification
- Price trend analysis
- Market condition alerts (price drops, new listings)




