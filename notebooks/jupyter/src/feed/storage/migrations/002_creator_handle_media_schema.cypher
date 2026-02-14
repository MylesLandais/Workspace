// Migration: Creator/Handle/Media Ontology Schema
// This migration sets up the graph structure for entity resolution and cross-platform media aggregation

// ============================================================================
// CONSTRAINTS (Uniqueness)
// ============================================================================

CREATE CONSTRAINT creator_uuid_unique IF NOT EXISTS
FOR (c:Creator) REQUIRE c.uuid IS UNIQUE;

CREATE CONSTRAINT creator_slug_unique IF NOT EXISTS
FOR (c:Creator) REQUIRE c.slug IS UNIQUE;

CREATE CONSTRAINT handle_uuid_unique IF NOT EXISTS
FOR (h:Handle) REQUIRE h.uuid IS UNIQUE;

CREATE CONSTRAINT platform_name_unique IF NOT EXISTS
FOR (p:Platform) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT platform_slug_unique IF NOT EXISTS
FOR (p:Platform) REQUIRE p.slug IS UNIQUE;

CREATE CONSTRAINT media_uuid_unique IF NOT EXISTS
FOR (m:Media) REQUIRE m.uuid IS UNIQUE;

// ============================================================================
// INDEXES (Query Performance)
// ============================================================================

// Creator indexes
CREATE INDEX creator_slug_index IF NOT EXISTS
FOR (c:Creator) ON (c.slug);

CREATE INDEX creator_name_index IF NOT EXISTS
FOR (c:Creator) ON (c.name);

// Handle indexes
CREATE INDEX handle_username_index IF NOT EXISTS
FOR (h:Handle) ON (h.username);

CREATE INDEX handle_profile_url_index IF NOT EXISTS
FOR (h:Handle) ON (h.profile_url);

// Media indexes
CREATE INDEX media_publish_date_index IF NOT EXISTS
FOR (m:Media) ON (m.publish_date);

CREATE INDEX media_source_url_index IF NOT EXISTS
FOR (m:Media) ON (m.source_url);

CREATE INDEX media_type_index IF NOT EXISTS
FOR (m:Media) ON (m.media_type);

// Video-specific indexes
CREATE INDEX video_duration_index IF NOT EXISTS
FOR (v:Video) ON (v.duration);

// ============================================================================
// NODE STRUCTURE DOCUMENTATION
// ============================================================================

// Creator Node Structure:
// (:Creator {
//   uuid: String (unique, UUID),
//   name: String (human-readable name, e.g., "Eefje Depoortere"),
//   slug: String (unique, URL-friendly, e.g., "sjokz"),
//   bio: String (nullable, aggregated bio),
//   avatar_url: String (nullable, profile picture URL),
//   created_at: DateTime,
//   updated_at: DateTime
// })

// Handle Node Structure:
// (:Handle {
//   uuid: String (unique, UUID),
//   username: String (platform-specific, e.g., "@sjokz"),
//   display_name: String (nullable, display name on platform),
//   profile_url: String (full URL to profile),
//   follower_count: Integer (nullable),
//   verified_by_platform: Boolean (platform's verification badge),
//   created_at: DateTime,
//   updated_at: DateTime
// })

// Platform Node Structure:
// (:Platform {
//   name: String (unique, e.g., "YouTube", "TikTok", "Instagram"),
//   slug: String (unique, URL-friendly, e.g., "youtube"),
//   api_base_url: String (nullable, API endpoint),
//   icon_url: String (nullable, platform icon URL),
//   created_at: DateTime
// })

// Media Node Structure (Base):
// (:Media {
//   uuid: String (unique, UUID),
//   title: String (nullable),
//   source_url: String (original content URL),
//   publish_date: DateTime,
//   thumbnail_url: String (nullable),
//   media_type: String (MediaType enum: Video, Image, Text, Audio, Mixed),
//   created_at: DateTime,
//   updated_at: DateTime
// })

// Video Node Structure (extends Media):
// (:Media:Video {
//   ... all Media properties ...
//   duration: Integer (seconds, nullable),
//   view_count: Integer (nullable),
//   aspect_ratio: String (nullable, e.g., "16:9", "9:16"),
//   resolution: String (nullable, e.g., "1080p")
// })

// Image Node Structure (extends Media):
// (:Media:Image {
//   ... all Media properties ...
//   width: Integer (pixels, nullable),
//   height: Integer (pixels, nullable),
//   aspect_ratio: String (nullable, e.g., "1:1", "4:3")
// })

// Text Node Structure (extends Media):
// (:Media:Text {
//   ... all Media properties ...
//   body_content: String (full text content),
//   word_count: Integer (nullable)
// })

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// Creator Relationships:
// (:Creator)-[:OWNS_HANDLE {
//   status: String (HandleStatus: Active, Suspended, Abandoned, Unverified),
//   verified: Boolean,
//   confidence: String (VerificationConfidence: High, Medium, Manual),
//   discovered_at: DateTime,
//   verified_at: DateTime (nullable),
//   created_at: DateTime
// }]->(:Handle)

// Handle Relationships:
// (:Handle)-[:ON_PLATFORM]->(:Platform)
// (:Handle)-[:REFERENCES {
//   source_url: String (URL where reference was found),
//   discovered_at: DateTime,
//   confidence: String (VerificationConfidence),
//   context: String (nullable, surrounding text)
// }]->(:Handle)

// Media Relationships:
// (:Handle)-[:PUBLISHED {
//   published_at: DateTime,
//   engagement_score: Float (nullable)
// }]->(:Media)
// (:Media)-[:SOURCED_FROM]->(:Platform)

// ============================================================================
// COMMON QUERY PATTERNS
// ============================================================================

// Get Creator with all Handles:
// MATCH (c:Creator {slug: $slug})-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform)
// RETURN c, collect({handle: h, platform: p}) as handles

// Get Omni-Feed for Creator:
// MATCH (c:Creator {uuid: $creator_uuid})-[:OWNS_HANDLE {verified: true, status: 'Active'}]->(h:Handle)
// MATCH (h)-[:PUBLISHED]->(m:Media)
// WHERE m.publish_date IS NOT NULL
// RETURN m
// ORDER BY m.publish_date DESC
// LIMIT $limit

// Get Unverified Handles:
// MATCH (c:Creator)-[r:OWNS_HANDLE {verified: false}]->(h:Handle)
// RETURN c, h, r
// ORDER BY r.discovered_at DESC

// Get Media by Type:
// MATCH (m:Video)
// WHERE m.publish_date >= $since
// RETURN m
// ORDER BY m.publish_date DESC








