// Neo4j Schema Migration for Image Deduplication System
// Run this migration to set up the graph database schema

// ImageFile nodes - represent physical image files
CREATE CONSTRAINT imagefile_id IF NOT EXISTS
FOR (i:ImageFile) REQUIRE i.id IS UNIQUE;

CREATE INDEX imagefile_sha256 IF NOT EXISTS
FOR (i:ImageFile) ON (i.sha256);

CREATE INDEX imagefile_phash IF NOT EXISTS
FOR (i:ImageFile) ON (i.phash);

CREATE INDEX imagefile_dhash IF NOT EXISTS
FOR (i:ImageFile) ON (i.dhash);

// ImageCluster nodes - represent clusters of duplicate/similar images
CREATE CONSTRAINT imagecluster_id IF NOT EXISTS
FOR (c:ImageCluster) REQUIRE c.id IS UNIQUE;

CREATE INDEX imagecluster_canonical IF NOT EXISTS
FOR (c:ImageCluster) ON (c.canonical_sha256);

CREATE INDEX imagecluster_first_seen IF NOT EXISTS
FOR (c:ImageCluster) ON (c.first_seen);

// Post nodes (may already exist, but ensure index)
CREATE INDEX post_id IF NOT EXISTS
FOR (p:Post) ON (p.id);

CREATE INDEX post_created IF NOT EXISTS
FOR (p:Post) ON (p.created_at);

// Note: Relationships are created dynamically:
// - (ImageFile)-[:BELONGS_TO {confidence: float, assigned_at: datetime}]->(ImageCluster)
// - (ImageCluster)-[:CANONICAL]->(ImageFile)
// - (ImageFile)-[:APPEARED_IN {position: integer}]->(Post)
// - (ImageFile)-[:REPOST_OF {confidence: float, detected_method: string}]->(ImageFile)







