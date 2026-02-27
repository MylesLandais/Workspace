// WD14 Tag Schema - Separate ontology from CLIP tags
// Stores character/general tags with confidence scores independently

// WD14Tag nodes (indexed by name + category)
CREATE CONSTRAINT wd14_tag_unique IF NOT EXISTS
  FOR (t:WD14Tag) REQUIRE (t.name, t.category) IS UNIQUE;

CREATE INDEX wd14_tag_name IF NOT EXISTS
  FOR (t:WD14Tag) ON (t.name);

CREATE INDEX wd14_tag_category IF NOT EXISTS
  FOR (t:WD14Tag) ON (t.category);

// WD14Result node - tagging result for single image
CREATE CONSTRAINT wd14_result_sha256_unique IF NOT EXISTS
  FOR (r:WD14Result) REQUIRE r.image_sha256 IS UNIQUE;

CREATE INDEX wd14_result_sha256 IF NOT EXISTS
  FOR (r:WD14Result) ON (r.image_sha256);

CREATE INDEX wd14_result_rating IF NOT EXISTS
  FOR (r:WD14Result) ON (r.rating);

CREATE INDEX wd14_result_processed_at IF NOT EXISTS
  FOR (r:WD14Result) ON (r.processed_at);

// Link ImageMedia to WD14Result
CREATE INDEX wd14_has_result_created IF NOT EXISTS
  FOR ()-[r:HAS_WD14_RESULT]->() ON (r.created_at);
