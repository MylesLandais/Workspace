// Migration: Add image hash support to Post nodes for duplicate detection
// This allows tracking image reposts and similarity scores

// Add index for image hash lookups
CREATE INDEX post_image_hash_index IF NOT EXISTS
FOR (p:Post) ON (p.image_hash);

// Add index for image URL lookups (for duplicate detection)
CREATE INDEX post_url_index IF NOT EXISTS
FOR (p:Post) ON (p.url);








