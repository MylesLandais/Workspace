// Listal schema extension for knowledge graph
// Run this migration to enable Listal profile and image tracking

// Indexes for Listal queries
CREATE INDEX listal_image_id_index IF NOT EXISTS
FOR (li:ListalImage) ON (li.image_id);

CREATE INDEX listal_image_normalized_url_index IF NOT EXISTS
FOR (li:ListalImage) ON (li.normalized_url);

CREATE INDEX listal_profile_slug_index IF NOT EXISTS
FOR (lp:ListalProfile) ON (lp.slug);

CREATE INDEX listal_user_username_index IF NOT EXISTS
FOR (lu:ListalUser) ON (lu.username);

CREATE INDEX listal_list_slug_index IF NOT EXISTS
FOR (ll:ListalList) ON (ll.slug);

// Note: ListalImage properties:
// - image_id: String (e.g., "16806755")
// - normalized_url: String (canonical URL)
// - source_url: String (original URL)
// - thumbnail_url: String
// - views: Integer
// - vote_count: Integer
// - added_date: DateTime
// - added_by: String (curator username)
// - discovered_at: DateTime
// - created_at: DateTime
// - updated_at: DateTime

// Note: ListalProfile properties:
// - slug: String (e.g., "maddie-teeuws")
// - name: String (display name)
// - image_count: Integer
// - url: String
// - discovered_at: DateTime
// - created_at: DateTime
// - updated_at: DateTime

// Note: ListalList properties:
// - slug: String (e.g., "russian-model-kristina-romanova")
// - name: String
// - curator: String
// - image_count: Integer
// - url: String
// - discovered_at: DateTime
// - created_at: DateTime
// - updated_at: DateTime

// Note: ListalUser properties:
// - username: String
// - avatar_url: String
// - discovered_at: DateTime
// - created_at: DateTime

// Relationship types:
// - (lp:ListalProfile)-[:HAS_IMAGE]->(li:ListalImage)
// - (li:ListalImage)-[:SUBJECT_OF]->(lp:ListalProfile)
// - (li:ListalImage)-[:SIMILAR_TO]->(li:ListalImage)  // People also voted for
// - (li:ListalImage)-[:IN_LIST]->(ll:ListalList)
// - (ll:ListalList)-[:CONTAINS]->(li:ListalImage)
// - (li:ListalImage)-[:VOTED_FOR]->(li:ListalImage)  // From user perspective
// - (lu:ListalUser)-[:VOTED_FOR]->(li:ListalImage)
// - (li:ListalImage)-[:VOTES_FROM]->(lu:ListalUser)
// - (lu:ListalUser)-[:CURATED]->(ll:ListalList)
// - (ll:ListalList)-[:CURATED_BY]->(lu:ListalUser)
// - (lp:ListalProfile)-[:LINKED_TO]->(c:Creator)  // Link to existing Creator node
// - (c:Creator)-[:LISTAL_PROFILE]->(lp:ListalProfile)
