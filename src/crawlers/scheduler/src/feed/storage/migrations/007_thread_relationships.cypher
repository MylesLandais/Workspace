// Migration: Add cross-thread relationship support
// This enables mapping and correlating threads that reference or discuss each other
// Example: r/SillyTavernAI thread discussing an r/LocalLLaMA post

// Create indexes for relationship queries
CREATE INDEX post_permalink_index IF NOT EXISTS
FOR (p:Post) ON (p.permalink);

CREATE INDEX post_url_index IF NOT EXISTS
FOR (p:Post) ON (p.url);

// Note: Relationships are created programmatically:
// - (Post)-[:RELATES_TO {relationship_type: "cross_reference", source: "comment", discovered_at: datetime()}]->(Post)
//   Used when a comment/post contains a URL to another Reddit thread
// - (Post)-[:DISCUSSES {context: "mention", discovered_at: datetime()}]->(Post)
//   Used when a thread explicitly discusses or mentions another thread (semantic relationship)







