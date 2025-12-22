// Migration: Web Crawler Schema
// This migration sets up the graph structure for adaptive decay web crawling
// with URL tracking, content hashing, and crawl history

// ============================================================================
// CONSTRAINTS (Uniqueness)
// ============================================================================

CREATE CONSTRAINT webpage_url_unique IF NOT EXISTS
FOR (w:WebPage) REQUIRE w.normalized_url IS UNIQUE;

// ============================================================================
// INDEXES (Query Performance)
// ============================================================================

// WebPage indexes for efficient querying
CREATE INDEX webpage_next_crawl_index IF NOT EXISTS
FOR (w:WebPage) ON (w.next_crawl_at);

CREATE INDEX webpage_domain_index IF NOT EXISTS
FOR (w:WebPage) ON (w.domain);

CREATE INDEX webpage_content_hash_index IF NOT EXISTS
FOR (w:WebPage) ON (w.content_hash);

CREATE INDEX webpage_simhash_index IF NOT EXISTS
FOR (w:WebPage) ON (w.simhash);

CREATE INDEX webpage_last_crawled_index IF NOT EXISTS
FOR (w:WebPage) ON (w.last_crawled_at);

// ============================================================================
// NODE STRUCTURE DOCUMENTATION
// ============================================================================

// WebPage Node Structure:
// (:WebPage {
//   normalized_url: String (unique, canonical URL),
//   original_url: String (first seen URL),
//   domain: String (extracted domain for rate limiting),
//   content_hash: String (SHA-256 hash of content),
//   simhash: String (64-bit fingerprint for near-duplicate detection),
//   last_crawled_at: DateTime (nullable, last successful crawl),
//   next_crawl_at: DateTime (nullable, scheduled next crawl),
//   crawl_interval_days: Float (current interval in days),
//   change_count: Integer (number of times content changed),
//   no_change_count: Integer (consecutive crawls with no change),
//   http_status: Integer (nullable, last HTTP status code),
//   content_type: String (nullable, MIME type),
//   content_length: Integer (nullable, size in bytes),
//   crawl_duration_ms: Integer (nullable, last crawl duration),
//   robots_allowed: Boolean (robots.txt compliance),
//   created_at: DateTime,
//   updated_at: DateTime
// })

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// CrawlHistory Relationship:
// (:WebPage)-[:CRAWLED_AT {
//   crawled_at: DateTime,
//   http_status: Integer,
//   content_hash: String,
//   changed: Boolean,
//   content_length: Integer (nullable),
//   crawl_duration_ms: Integer (nullable)
// }]

// ============================================================================
// COMMON QUERY PATTERNS
// ============================================================================

// Get pages ready for crawling:
// MATCH (w:WebPage)
// WHERE w.next_crawl_at IS NOT NULL AND w.next_crawl_at <= datetime()
// AND w.robots_allowed = true
// RETURN w
// ORDER BY w.next_crawl_at ASC
// LIMIT $limit

// Get crawl history for a page:
// MATCH (w:WebPage {normalized_url: $url})-[r:CRAWLED_AT]->()
// RETURN r
// ORDER BY r.crawled_at DESC
// LIMIT $limit

// Find near-duplicate pages (simhash Hamming distance <= 3):
// MATCH (w1:WebPage), (w2:WebPage)
// WHERE w1.normalized_url < w2.normalized_url
// AND w1.simhash IS NOT NULL AND w2.simhash IS NOT NULL
// AND apoc.bitwise.hammingDistance(w1.simhash, w2.simhash) <= 3
// RETURN w1, w2

// Get pages by domain for rate limiting:
// MATCH (w:WebPage {domain: $domain})
// WHERE w.next_crawl_at IS NOT NULL
// RETURN w
// ORDER BY w.next_crawl_at ASC

