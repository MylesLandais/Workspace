// Migration: Post Links Schema
// Adds Link nodes for external links referenced in posts and comments

// Create constraint for unique link URLs
CREATE CONSTRAINT link_url_unique IF NOT EXISTS
FOR (l:Link) REQUIRE l.url IS UNIQUE;

// Create index for link queries
CREATE INDEX link_url_index IF NOT EXISTS
FOR (l:Link) ON (l.url);

// Create full-text index for link domain searches
CREATE FULLTEXT INDEX link_domain_index IF NOT EXISTS
FOR (l:Link) ON EACH [l.url];

// Relationship: Post -[:HAS_LINK]-> Link
// This relationship is created when storing posts with external links
// Example: MFC links, product links, etc.







