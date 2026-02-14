// Migration: Garment Ontology Schema
// Adds nodes and relationships for garment style classification and product matching

// Create constraints for unique properties
CREATE CONSTRAINT garment_style_name_unique IF NOT EXISTS
FOR (gs:GarmentStyle) REQUIRE gs.name IS UNIQUE;

CREATE CONSTRAINT style_feature_unique IF NOT EXISTS
FOR (sf:StyleFeature) REQUIRE (sf.feature_type, sf.feature_value) IS UNIQUE;

CREATE CONSTRAINT product_match_id_unique IF NOT EXISTS
FOR (pm:ProductMatch) REQUIRE pm.uuid IS UNIQUE;

// Create indexes for common queries
CREATE INDEX garment_style_category_index IF NOT EXISTS
FOR (gs:GarmentStyle) ON (gs.category);

CREATE INDEX garment_style_type_index IF NOT EXISTS
FOR (gs:GarmentStyle) ON (gs.garment_type);

CREATE INDEX garment_style_primary_style_index IF NOT EXISTS
FOR (gs:GarmentStyle) ON (gs.primary_style);

CREATE INDEX style_feature_type_index IF NOT EXISTS
FOR (sf:StyleFeature) ON (sf.feature_type);

CREATE INDEX product_match_confidence_index IF NOT EXISTS
FOR (pm:ProductMatch) ON (pm.confidence_score);

// Full-text index for style search
CREATE FULLTEXT INDEX garment_style_search_index IF NOT EXISTS
FOR (gs:GarmentStyle) ON EACH [gs.name, gs.description];

// Relationship: Image -[:MATCHES_STYLE]-> GarmentStyle
// Links images (from Reddit posts, etc.) to identified garment styles

// Relationship: GarmentStyle -[:HAS_FEATURE]-> StyleFeature
// Links styles to their component features

// Relationship: GarmentStyle -[:IS_VARIATION_OF]-> GarmentStyle
// Links style variations (e.g., different colors of same style)

// Relationship: GarmentStyle -[:MATCHES_PRODUCT]-> Product
// Links identified styles to e-commerce products

// Relationship: Product -[:HAS_MATCH]-> ProductMatch
// Stores match confidence and metadata

// Example queries:
// Find all products matching a style:
// MATCH (gs:GarmentStyle {name: $style_name})-[:MATCHES_PRODUCT]->(p:Product)
// RETURN p

// Find similar styles:
// MATCH (gs1:GarmentStyle)-[:HAS_FEATURE]->(sf:StyleFeature)<-[:HAS_FEATURE]-(gs2:GarmentStyle)
// WHERE gs1 <> gs2
// WITH gs1, gs2, count(sf) as shared_features
// WHERE shared_features >= 2
// RETURN gs1.name, gs2.name, shared_features




