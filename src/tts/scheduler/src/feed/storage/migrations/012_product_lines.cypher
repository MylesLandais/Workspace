// Migration 012: Product Lines and Style Variants
// Adds support for product line tracking, style variants, and temporal evolution
// Similar to how Victoria's Secret and Lululemon manage product catalogs

// Product Line nodes (e.g., "Wunder Train", "Align", "Speed Up")
CREATE CONSTRAINT product_line_name IF NOT EXISTS
FOR (pl:ProductLine) REQUIRE pl.name IS UNIQUE;

CREATE INDEX product_line_brand IF NOT EXISTS
FOR (pl:ProductLine) ON (pl.brand);

CREATE INDEX product_line_category IF NOT EXISTS
FOR (pl:ProductLine) ON (pl.category);

// Base Style nodes (e.g., "Wunder Train High-Rise Tight")
CREATE CONSTRAINT base_style_name IF NOT EXISTS
FOR (bs:BaseStyle) REQUIRE bs.name IS UNIQUE;

CREATE INDEX base_style_family IF NOT EXISTS
FOR (bs:BaseStyle) ON (bs.style_family);

// Style Variant nodes (specific style with features, e.g., "W5FMWS")
CREATE CONSTRAINT style_variant_number IF NOT EXISTS
FOR (sv:StyleVariant) REQUIRE sv.style_number IS UNIQUE;

CREATE INDEX style_variant_base IF NOT EXISTS
FOR (sv:StyleVariant) ON (sv.base_style);

CREATE INDEX style_variant_release_date IF NOT EXISTS
FOR (sv:StyleVariant) ON (sv.release_date);

// Color Variant nodes
CREATE INDEX color_variant_name IF NOT EXISTS
FOR (cv:ColorVariant) ON (cv.color_name);

CREATE INDEX color_variant_collection IF NOT EXISTS
FOR (cv:ColorVariant) ON (cv.collection);

// Collection nodes (e.g., "Summer Haze", "Aerial", "Seawheeze 2023")
CREATE CONSTRAINT collection_name IF NOT EXISTS
FOR (c:Collection) REQUIRE c.name IS UNIQUE;

CREATE INDEX collection_type IF NOT EXISTS
FOR (c:Collection) ON (c.collection_type);

// Price Point nodes (temporal price tracking)
CREATE INDEX price_point_effective_date IF NOT EXISTS
FOR (pp:PricePoint) ON (pp.effective_date);

CREATE INDEX price_point_type IF NOT EXISTS
FOR (pp:PricePoint) ON (pp.price_type);

// Relationships
// ProductLine -> BaseStyle
// BaseStyle -> StyleVariant
// StyleVariant -> ColorVariant
// StyleVariant -> ProductInstance (existing Product nodes)
// StyleVariant -> PricePoint
// ColorVariant -> Collection
// StyleVariant -> StyleVariant (evolution/re-release)

// Full-text search indexes
CALL db.index.fulltext.createNodeIndex(
    'product_line_search',
    ['ProductLine'],
    ['name', 'description']
) YIELD indexName;

CALL db.index.fulltext.createNodeIndex(
    'style_variant_search',
    ['StyleVariant'],
    ['style_number', 'base_style', 'variant_type', 'material']
) YIELD indexName;

CALL db.index.fulltext.createNodeIndex(
    'collection_search',
    ['Collection'],
    ['name', 'description']
) YIELD indexName;




