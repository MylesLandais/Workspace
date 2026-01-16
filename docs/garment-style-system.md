# Garment Style Detection and Product Matching System

## Overview

This system enables computer vision-based garment style detection, ontology creation, and automatic product matching with price tracking across e-commerce platforms.

## Architecture

### Components

1. **Garment Ontology** (`src/feed/ontology/garment_ontology.py`)
   - Defines garment categories, types, and styles
   - Provides structure for style classification
   - Supports feature extraction

2. **Garment Matcher Service** (`src/feed/services/garment_matcher.py`)
   - Analyzes images and creates style ontology
   - Matches styles to e-commerce products
   - Sets up price tracking
   - Generates marketplace search links

3. **Graph Schema** (`src/feed/storage/migrations/011_garment_ontology.cypher`)
   - GarmentStyle nodes
   - StyleFeature nodes
   - ProductMatch relationships
   - Image-to-style links

## Workflow

### 1. Image Analysis
```
Image → CV Model → Style Features
```

**Input**: Image URL  
**Output**: Style analysis dict with:
- garment_type
- color
- panel_type (if applicable)
- fit
- length
- material
- features list

### 2. Ontology Creation
```
Style Features → GarmentStyle Node + StyleFeature Nodes
```

Creates or updates:
- GarmentStyle node with composite style name
- StyleFeature nodes for each detected feature
- Links features to style via HAS_FEATURE relationships

### 3. Product Matching
```
GarmentStyle → Product Search → ProductMatch Relationships
```

Matches style to products using:
- Feature overlap (tags, descriptions)
- Confidence scoring (0.0-1.0)
- Match type classification (exact/similar/variant)

### 4. Price Tracking Setup
```
Matched Products → Price History Tracking
```

- Creates PriceHistory nodes for new products
- Sets up periodic price checks
- Enables market condition analysis

### 5. Marketplace Links
```
Style Features → Search Query → Marketplace URLs
```

Generates search links for:
- Depop
- eBay
- Poshmark
- Mercari

## Example: Sheer Panel Yoga Pants

### Input Image Analysis
```python
{
    "garment_type": "Yoga Pants",
    "color": "Black",
    "panel_type": "Sheer Panel",
    "fit": "Compression",
    "length": "Full Length",
    "material": "Polyester/Spandex",
    "features": [
        "sheer_panel_thigh",
        "sheer_panel_calf",
        "vertical_panels",
        "compression_fit",
        "full_length"
    ]
}
```

### Created Ontology
- **GarmentStyle**: "Sheer Panel Yoga Pants"
- **StyleFeatures**:
  - panel_style: "Sheer Panel"
  - fit_style: "Compression"
  - length_style: "Full Length"
  - color: "Black"
  - material_type: "Polyester/Spandex"

### Product Matching
- Searches for products with matching features
- Creates ProductMatch relationships with confidence scores
- Returns top matches with prices and URLs

### Marketplace Links
- Depop: `https://www.depop.com/search/?q=sheer%20panel%20yoga%20pants%20black`
- eBay: `https://www.ebay.com/sch/i.html?_nkw=sheer+panel+yoga+pants+black`
- Poshmark: `https://poshmark.com/search?query=sheer%20panel%20yoga%20pants%20black`
- Mercari: `https://www.mercari.com/search/?keyword=sheer%20panel%20yoga%20pants%20black`

## Graph Queries

### Find Products Matching a Style
```cypher
MATCH (gs:GarmentStyle {name: "Sheer Panel Yoga Pants"})-[:MATCHES_PRODUCT]->(p:Product)
RETURN p.title, p.price, p.currency, p.url
ORDER BY p.price ASC
```

### Find Similar Styles
```cypher
MATCH (gs1:GarmentStyle)-[:HAS_FEATURE]->(sf:StyleFeature)<-[:HAS_FEATURE]-(gs2:GarmentStyle)
WHERE gs1 <> gs2
WITH gs1, gs2, count(sf) as shared_features
WHERE shared_features >= 2
RETURN gs1.name, gs2.name, shared_features
ORDER BY shared_features DESC
```

### Price Trends for a Style
```cypher
MATCH (gs:GarmentStyle {name: "Sheer Panel Yoga Pants"})-[:MATCHES_PRODUCT]->(p:Product)
MATCH (p)-[:HAS_PRICE_HISTORY]->(ph:PriceHistory)
RETURN ph.timestamp, ph.price, ph.currency
ORDER BY ph.timestamp ASC
```

## Benchmark Evaluation

See `evaluation/garment_style_detection_benchmark.md` for:
- Test case definition
- Evaluation metrics
- Success criteria
- Future enhancements

## Integration Points

### With Reddit Crawler
- Images from Reddit posts can be analyzed
- Posts linked to garment styles via ABOUT_STYLE relationship
- Enables discovery of trending styles

### With E-commerce Crawlers
- Products automatically matched to styles
- Price tracking enabled for matched products
- Market analysis by style

### With Price Tracking
- Automatic price history creation
- Trend analysis by style
- Price drop alerts

## Future Enhancements

1. **CV Model Integration**
   - Train/use actual CV model for style detection
   - Improve feature extraction accuracy
   - Handle multiple garments in one image

2. **Style Variation Detection**
   - Automatic color variation grouping
   - Size availability tracking
   - Brand identification

3. **Market Analysis**
   - Price trend predictions
   - Availability forecasting
   - Seller behavior analysis

4. **User Interface**
   - Image upload interface
   - Style browser
   - Product comparison tool



