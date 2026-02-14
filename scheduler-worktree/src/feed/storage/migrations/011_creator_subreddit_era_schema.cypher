// Creator-Subreddit relationships and era tagging schema
// Run this migration to enable linking creators to subreddits and tagging posts by era

// Create indexes for era queries
CREATE INDEX post_era_index IF NOT EXISTS
FOR (p:Post) ON (p.era);

CREATE INDEX post_era_full_name_index IF NOT EXISTS
FOR (p:Post) ON (p.era_full_name);

// Note: HAS_SOURCE relationship (Creator -> Subreddit) is created dynamically
// Properties: source_type, discovered_at, created_at, updated_at

// Note: ABOUT relationship (Post -> Creator) is created dynamically
// Properties: created_at

// Era tagging is done via Post properties:
// - era: String (short code, e.g., "TLOAS")
// - era_full_name: String (full name, e.g., "The Tortured Poets Department")






