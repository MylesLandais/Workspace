// Migration: Temporal Versioning Schema
// This migration adds versioned crawl history with anchor+delta storage pattern
// inspired by AeonG and Clock-G research for efficient temporal data management

// ============================================================================
// CONSTRAINTS (Uniqueness)
// ============================================================================

CREATE CONSTRAINT crawlversion_id_unique IF NOT EXISTS
FOR (v:CrawlVersion) REQUIRE v.version_id IS UNIQUE;

// ============================================================================
// INDEXES (Query Performance)
// ============================================================================

// CrawlVersion indexes for efficient temporal queries
CREATE INDEX crawlversion_crawled_at_index IF NOT EXISTS
FOR (v:CrawlVersion) ON (v.crawled_at);

CREATE INDEX crawlversion_content_hash_index IF NOT EXISTS
FOR (v:CrawlVersion) ON (v.content_hash);

CREATE INDEX crawlversion_changed_index IF NOT EXISTS
FOR (v:CrawlVersion) ON (v.changed);

// Composite index for time-range queries
CREATE INDEX crawlversion_url_time_index IF NOT EXISTS
FOR (v:CrawlVersion) ON (v.normalized_url, v.crawled_at);

// ============================================================================
// NODE STRUCTURE DOCUMENTATION
// ============================================================================

// CrawlVersion Node Structure:
// (:CrawlVersion {
//   version_id: String (unique, UUID),
//   normalized_url: String (reference to WebPage),
//   crawled_at: DateTime (timestamp of this version),
//   content_hash: String (SHA-256 hash of content),
//   changed: Boolean (whether content changed from previous version),
//   delta_properties: Map (only changed properties, space-efficient),
//   http_status: Integer (nullable, HTTP status code),
//   content_type: String (nullable, MIME type),
//   content_length: Integer (nullable, size in bytes),
//   crawl_duration_ms: Integer (nullable, crawl duration),
//   simhash: String (nullable, 64-bit fingerprint),
//   created_at: DateTime
// })

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// HAS_VERSION Relationship:
// (:WebPage)-[:HAS_VERSION {
//   created_at: DateTime
// }]->(:CrawlVersion)
// Links WebPage to its version history

// VERSION_CHAIN Relationship:
// (:CrawlVersion)-[:VERSION_CHAIN {
//   created_at: DateTime
// }]->(:CrawlVersion)
// Links versions in chronological order (older -> newer)
// Enables efficient time traversal

// ============================================================================
// COMMON QUERY PATTERNS
// ============================================================================

// Get latest version for a page:
// MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
// RETURN v
// ORDER BY v.crawled_at DESC
// LIMIT 1

// Get version at specific time (time-slice query):
// MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
// WHERE v.crawled_at <= datetime($target_time)
// RETURN v
// ORDER BY v.crawled_at DESC
// LIMIT 1

// Get version chain (chronological order):
// MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v1:CrawlVersion)
// OPTIONAL MATCH path = (v1)-[:VERSION_CHAIN*]->(v2:CrawlVersion)
// RETURN v1, path
// ORDER BY v1.crawled_at ASC

// Get versions in time range:
// MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
// WHERE v.crawled_at >= datetime($start_time)
// AND v.crawled_at <= datetime($end_time)
// RETURN v
// ORDER BY v.crawled_at ASC

// Get change frequency (versions with changed=true):
// MATCH (w:WebPage {normalized_url: $url})-[:HAS_VERSION]->(v:CrawlVersion)
// WHERE v.changed = true
// AND v.crawled_at >= datetime() - duration({days: $days})
// RETURN count(v) as change_count

// Get all changed properties between versions:
// MATCH (v1:CrawlVersion {version_id: $version1})
// MATCH (v2:CrawlVersion {version_id: $version2})
// RETURN v1.delta_properties as delta1, v2.delta_properties as delta2

