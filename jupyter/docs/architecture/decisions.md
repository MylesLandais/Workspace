# Architecture Decision Records

This document records architectural decisions made for the e-commerce product tracking and garment style detection system.

**Last Updated**: 2025-01-XX  
**Total ADRs**: 13

## ADR-001: Graph-Based E-commerce Ontology

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to organize e-commerce product data, track prices, and match products to garment styles from images.

**Decision**: Use Neo4j graph database with a structured ontology for:
- Product nodes with price history
- Garment style classification
- Style-to-product matching
- Cross-platform price tracking

**Consequences**:
- ✅ Enables rich relationship queries (find similar styles, track price trends)
- ✅ Supports temporal data (price history with versioning)
- ✅ Flexible schema for adding new garment types and features
- ⚠️ Requires migration management for schema changes
- ⚠️ Learning curve for Cypher queries

## ADR-002: Computer Vision for Garment Style Detection

**Status**: Accepted (Implementation Ready)  
**Date**: 2025-01-XX  
**Context**: Need to identify garment styles from images (e.g., Reddit posts) and match to e-commerce products.

**Decision**: Create a benchmark task for garment style detection that:
1. Analyzes images to extract style features
2. Creates/updates garment style ontology nodes
3. Matches styles to e-commerce products
4. Sets up price tracking for matched products

**Implementation**:
- GarmentStyle nodes for identified styles
- StyleFeature nodes for component features (panels, fit, length, etc.)
- ProductMatch relationships with confidence scores
- Automatic marketplace search link generation

**Consequences**:
- ✅ Enables automated product discovery from images
- ✅ Supports style-based product recommendations
- ✅ Enables market analysis by style
- ⚠️ Requires CV model training/implementation
- ⚠️ Need to handle false positives in matching

## ADR-003: Multi-Platform E-commerce Crawling

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to track products across multiple marketplaces (Depop, Shopify, etc.).

**Decision**: Create platform adapters (DepopAdapter, ShopifyAdapter) that:
- Extract product data consistently
- Store in unified Product model
- Support price history tracking
- Handle platform-specific quirks

**Consequences**:
- ✅ Unified data model across platforms
- ✅ Easier to add new platforms
- ✅ Consistent price tracking
- ⚠️ Each platform requires custom parsing logic
- ⚠️ Rate limiting and anti-scraping measures vary

## ADR-004: Temporal Price Tracking

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to track price changes over time for market analysis.

**Decision**: Use PriceHistory nodes with temporal relationships:
- Each price change creates a new PriceHistory node
- Linked chronologically via NEXT_PRICE relationships
- Enables time-series queries and trend analysis

**Consequences**:
- ✅ Historical price data for analysis
- ✅ Can detect price trends and patterns
- ✅ Supports "price drop" alerts
- ⚠️ Storage grows over time (need cleanup strategy)
- ⚠️ Requires periodic crawling of tracked products

## ADR-005: Image-to-Product Matching

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to match images (from Reddit, etc.) to e-commerce products.

**Decision**: Multi-stage matching process:
1. CV analysis extracts style features
2. Create/update GarmentStyle ontology
3. Match style to products using:
   - Feature overlap (tags, descriptions)
   - Confidence scoring
   - Manual review queue for low-confidence matches

**Consequences**:
- ✅ Enables discovery of products from social media images
- ✅ Supports style-based search
- ⚠️ Matching accuracy depends on CV model quality
- ⚠️ May need human review for edge cases

## ADR-006: Marketplace Search Link Generation

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to provide users with links to search for products on marketplaces.

**Decision**: Automatically generate search links based on:
- Detected style features
- Garment type and color
- Primary style characteristics

**Consequences**:
- ✅ Easy access to marketplace searches
- ✅ Can be used for manual product discovery
- ⚠️ Search quality depends on marketplace search algorithms
- ⚠️ Links may become stale if marketplace URLs change

## ADR-007: Price Tracking Automation

**Status**: Partially Implemented  
**Date**: 2025-01-XX  
**Note**: Price history tracking is implemented. Scheduled crawling and alerts are planned.  
**Context**: Need to automatically track prices for matched products.

**Decision**: Implement scheduled crawling:
- Products with ProductMatch relationships are automatically tracked
- Periodic price checks (daily/weekly)
- Price changes trigger notifications/alerts
- Market condition analysis (price trends, availability)

**Consequences**:
- ✅ Automated price monitoring
- ✅ Market trend detection
- ⚠️ Requires crawling infrastructure
- ⚠️ Rate limiting considerations
- ⚠️ Storage for historical data

## ADR-008: Garment Style Ontology Structure

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need structured way to classify garment styles.

**Decision**: Hierarchical ontology:
- GarmentCategory (top-level: Bottoms, Tops, etc.)
- GarmentType (specific: Yoga Pants, Leggings, etc.)
- StyleFeatures (components: panel type, fit, length, etc.)
- GarmentStyle (composite: "Sheer Panel Yoga Pants")

**Consequences**:
- ✅ Flexible classification system
- ✅ Supports style variations
- ✅ Enables similarity matching
- ⚠️ Requires maintenance as new styles emerge
- ⚠️ Need to handle edge cases and ambiguous styles

## ADR-009: Reddit Image Gallery Support

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Reddit posts can contain multiple images in galleries, and we need to track them individually for similarity search.

**Decision**: 
- Extract all images from Reddit gallery posts
- Store images with `image_index` property on `HAS_IMAGE` relationships
- Enable queries for posts with multiple images
- Support similarity search using multiple images from same post

**Implementation**:
- `RedditAdapter.extract_all_images()` handles gallery data
- `store_thread()` stores images with index tracking
- Queries can find posts with 2+ images for similarity search

**Consequences**:
- ✅ Supports multi-image posts for better style detection
- ✅ Enables image comparison within same post
- ✅ Useful for similarity search benchmarks
- ⚠️ Requires proper gallery data extraction from Reddit API

## ADR-010: External Link Extraction and Storage

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Reddit posts often contain links to external resources (MFC, image sources, product links) that should be tracked.

**Decision**: 
- Extract external links from post text and comments
- Store as Link nodes with relationship types
- Support link type classification (image_source, product_link, etc.)
- Enable queries to find posts linking to external resources

**Implementation**:
- Link extraction via regex patterns
- Link nodes with `HAS_LINK` relationships
- Link type metadata on relationships
- Supports MFC, Twitter, Pixiv, and other platforms

**Consequences**:
- ✅ Builds connections between social media and external data
- ✅ Enables discovery of original image sources
- ✅ Supports cross-platform data linking
- ⚠️ Link extraction depends on text patterns (may miss some links)

## ADR-011: Shopify Platform Support

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to support Shopify-based stores (e.g., HANRO) in addition to Depop.

**Decision**: Create `ShopifyAdapter` that:
- Parses Shopify product pages (HTML + JSON-LD)
- Extracts product data similar to Depop
- Handles Shopify-specific patterns (variants, JSON data)
- Uses same Product model for consistency

**Implementation**:
- `ShopifyAdapter` extends `PlatformAdapter`
- Supports JSON-LD structured data
- Extracts Shopify product JSON from script tags
- Handles variant selection and product options

**Consequences**:
- ✅ Unified product tracking across Depop and Shopify
- ✅ Consistent price tracking regardless of platform
- ✅ Easier to add more Shopify stores
- ⚠️ Each Shopify store may have custom themes (parsing may need adjustment)

## ADR-012: GraphQL API for Client-Server Architecture

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need a unified API interface for client applications to query products, styles, and relationships.

**Decision**: Use GraphQL with Strawberry (Python) to provide:
- Type-safe schema definitions
- Flexible querying (client requests only needed fields)
- Real-time subscriptions for updates
- Unified interface for all data types

**Implementation**:
- Strawberry GraphQL library
- Separate schema modules (ecommerce_schema, creator_schema, etc.)
- FastAPI integration for HTTP/WebSocket
- Schema introspection support

**Consequences**:
- ✅ Single endpoint for all queries
- ✅ Client can request only needed data
- ✅ Type-safe API with schema validation
- ✅ Easy to extend with new types
- ⚠️ Requires GraphQL client libraries on frontend
- ⚠️ Need to manage N+1 query problems

## ADR-013: End-to-End Testing with Puppeteer

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to validate full workflows including browser interactions and real website crawling.

**Decision**: Use Puppeteer (via pyppeteer or playwright) for E2E tests that:
- Test real browser interactions
- Validate actual website crawling
- Test GraphQL API from client perspective
- Verify end-to-end workflows

**Implementation**:
- PuppeteerTestBase class for test utilities
- GraphQLTestClient for API testing
- Screenshot capture for debugging
- Headless mode for CI/CD

**Consequences**:
- ✅ Tests real user workflows
- ✅ Validates actual website parsing
- ✅ Catches integration issues
- ⚠️ Slower than unit tests
- ⚠️ Requires browser installation
- ⚠️ May be flaky due to network/website changes

**Status**: Accepted  
**Date**: 2025-01-XX  
**Context**: Need to support Shopify-based stores (e.g., HANRO) in addition to Depop.

**Decision**: Create `ShopifyAdapter` that:
- Parses Shopify product pages (HTML + JSON-LD)
- Extracts product data similar to Depop
- Handles Shopify-specific patterns (variants, JSON data)
- Uses same Product model for consistency

**Implementation**:
- `ShopifyAdapter` extends `PlatformAdapter`
- Supports JSON-LD structured data
- Extracts Shopify product JSON from script tags
- Handles variant selection and product options

**Consequences**:
- ✅ Unified product tracking across Depop and Shopify
- ✅ Consistent price tracking regardless of platform
- ✅ Easier to add more Shopify stores
- ⚠️ Each Shopify store may have custom themes (parsing may need adjustment)

