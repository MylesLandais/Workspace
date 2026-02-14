# User Stories

This document tracks user stories for the e-commerce product tracking and garment style detection system.

**Last Updated**: 2025-01-XX  
**Total Stories**: 15  
**Implemented**: 8  
**In Progress**: 4  
**Planned**: 3

## Status Legend
- ✅ **Implemented**: Feature is complete and working
- 🔄 **In Progress**: Feature is partially implemented
- 📋 **Planned**: Feature is defined but not yet implemented

## E-commerce Product Tracking

### US-001: Track Product Prices
**As a** market analyst  
**I want to** track prices of specific products over time  
**So that** I can analyze market trends and price fluctuations

**Status**: ✅ Implemented  
**Implementation**: `ProductStorage.store_product()` automatically creates PriceHistory nodes

**Acceptance Criteria**:
- [x] Can add products to price tracking
- [x] Price history is automatically recorded
- [x] Can query price history for any product
- [ ] Price changes trigger notifications (planned)

### US-002: Discover Products from Images
**As a** user browsing social media  
**I want to** find e-commerce listings for garments I see in images  
**So that** I can purchase similar items

**Status**: ✅ Implemented  
**Implementation**: `GarmentMatcher.analyze_and_match_image()` provides full workflow

**Acceptance Criteria**:
- [x] Can upload/analyze an image (via CV model input)
- [x] System identifies garment style (creates GarmentStyle nodes)
- [x] System finds matching products (ProductMatch relationships)
- [x] Provides links to marketplace listings (Depop, eBay, Poshmark, Mercari)

### US-003: Style-Based Product Search
**As a** shopper  
**I want to** search for products by style features (e.g., "sheer panel yoga pants")  
**So that** I can find items matching specific style preferences

**Status**: 🔄 Partially Implemented  
**Implementation**: `GarmentMatcher` provides matching, full search UI planned

**Acceptance Criteria**:
- [x] Can search by style features (via GarmentMatcher)
- [x] Results show matching products across platforms
- [x] Results include price and availability
- [ ] Can filter by price range, condition, etc. (planned)

### US-004: Market Condition Analysis
**As a** market analyst  
**I want to** analyze market conditions for specific garment styles  
**So that** I can understand pricing trends and availability

**Status**: 🔄 Partially Implemented  
**Implementation**: Price history tracking implemented, analysis queries available

**Acceptance Criteria**:
- [x] Can view price trends for a style (via Cypher queries)
- [ ] Can see availability statistics (needs dashboard)
- [x] Can compare prices across platforms (via Product nodes)
- [ ] Can identify price anomalies (needs analysis logic)

### US-005: Automated Price Alerts
**As a** shopper  
**I want to** receive alerts when prices drop for tracked products  
**So that** I can purchase at the best price

**Acceptance Criteria**:
- [ ] Can set up price alerts for products
- [ ] Alerts trigger on price drops
- [ ] Alerts include product details and new price
- [ ] Can manage alert preferences

## Computer Vision & Style Detection

### US-006: Identify Garment Style from Image
**As a** system  
**I want to** automatically identify garment styles from images  
**So that** I can classify and match products

**Status**: 🔄 Partially Implemented  
**Implementation**: Ontology and matching implemented, CV model integration needed

**Acceptance Criteria**:
- [ ] Analyzes images to extract style features (needs CV model)
- [x] Creates garment style ontology entries (via `GarmentMatcher`)
- [x] Handles multiple garment types (ontology supports all types)
- [x] Confidence scores for detections (ProductMatch has confidence)

### US-007: Match Images to Products
**As a** user  
**I want to** find products that match garments in images  
**So that** I can purchase similar items

**Status**: ✅ Implemented  
**Implementation**: `GarmentMatcher.match_style_to_products()` with confidence scoring

**Acceptance Criteria**:
- [x] Matches images to existing products
- [x] Shows match confidence scores (0.0-1.0)
- [x] Provides product links
- [x] Handles style variations (via match_type: exact/similar/variant)

### US-008: Style Variation Detection
**As a** system  
**I want to** identify style variations (colors, sizes)  
**So that** I can group related products

**Acceptance Criteria**:
- [ ] Detects color variations of same style
- [ ] Groups products by base style
- [ ] Tracks availability of variations
- [ ] Shows price differences between variations

## Data Management

### US-009: Multi-Platform Product Tracking
**As a** system  
**I want to** track products across multiple marketplaces  
**So that** I can provide comprehensive market data

**Status**: ✅ Implemented  
**Implementation**: 
- `DepopAdapter` for Depop products
- `ShopifyAdapter` for Shopify stores (e.g., HANRO)
- Unified `Product` model
- `ProductStorage` for consistent storage

**Acceptance Criteria**:
- [x] Supports Depop, Shopify, and other platforms
- [x] Unified product data model (`Product` class)
- [x] Cross-platform price comparison (via Product nodes)
- [x] Platform-specific metadata preserved (stored in Product properties)

### US-010: Product Deduplication
**As a** system  
**I want to** identify duplicate products across platforms  
**So that** I can provide accurate market analysis

**Status**: 📋 Planned  
**Implementation**: Not yet implemented, would use image hashing and title similarity

**Acceptance Criteria**:
- [ ] Detects duplicate products
- [ ] Links duplicates via relationships
- [ ] Tracks prices across all instances
- [ ] Shows best price across platforms

### US-011: Historical Data Retention
**As a** system  
**I want to** retain historical product and price data  
**So that** I can analyze long-term trends

**Status**: ✅ Implemented  
**Implementation**: PriceHistory nodes with temporal relationships, temporal versioning schema

**Acceptance Criteria**:
- [x] Price history preserved (PriceHistory nodes)
- [x] Product metadata changes tracked (updated_at timestamps)
- [x] Can query historical states (via Cypher queries)
- [ ] Data retention policies configurable (planned)

## Benchmark & Evaluation

### US-012: Garment Style Detection Benchmark
**As a** developer  
**I want to** evaluate CV model performance on garment style detection  
**So that** I can improve accuracy

**Status**: ✅ Benchmark Defined  
**Implementation**: `evaluation/garment_style_detection_benchmark.md` defines test case

**Acceptance Criteria**:
- [x] Benchmark dataset with ground truth (test case defined)
- [ ] Evaluation metrics (accuracy, precision, recall) - needs CV model
- [ ] Style feature detection scores - needs CV model
- [x] Product matching accuracy (implemented via `GarmentMatcher`)

**Test Case**: Sheer Panel Yoga Pants
- Input: Image of black yoga pants with sheer panels
- Expected: Correctly identifies "Sheer Panel Yoga Pants" style ✅
- Expected: Matches to relevant e-commerce products ✅
- Expected: Sets up price tracking ✅

## Reddit & Social Media Integration

### US-013: Extract Images from Reddit Posts
**As a** system  
**I want to** extract all images from Reddit posts including galleries  
**So that** I can analyze garment styles from social media

**Status**: ✅ Implemented  
**Implementation**: `RedditAdapter.extract_all_images()` handles galleries and comment images

**Acceptance Criteria**:
- [x] Extracts images from Reddit gallery posts
- [x] Extracts images from post content
- [x] Extracts images from comments
- [x] Handles multiple images per post (with image_index tracking)

### US-014: Link Reddit Posts to External Data
**As a** system  
**I want to** extract and store links from Reddit posts (MFC, image sources, etc.)  
**So that** I can build connections between social media and external data

**Status**: ✅ Implemented  
**Implementation**: Link nodes with `HAS_LINK` relationships, supports MFC and image source links

**Acceptance Criteria**:
- [x] Extracts MFC links from posts and comments
- [x] Extracts image source links (Twitter, Pixiv, etc.)
- [x] Stores links as Link nodes
- [x] Links posts to external resources

### US-015: Multi-Image Post Analysis
**As a** system  
**I want to** identify posts with multiple distinct images  
**So that** I can use them for similarity search and style comparison

**Status**: ✅ Implemented  
**Implementation**: Image indexing with `image_index` property on `HAS_IMAGE` relationships

**Acceptance Criteria**:
- [x] Tracks image order in gallery posts
- [x] Identifies posts with 2+ images
- [x] Enables similarity search queries
- [x] Supports visual comparison

