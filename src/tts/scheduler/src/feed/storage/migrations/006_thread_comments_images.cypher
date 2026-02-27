// Migration: Add Comment and Image nodes for Reddit thread crawling
// This extends the schema to support full thread crawling with comments and images

// Create constraints for unique properties
CREATE CONSTRAINT comment_id_unique IF NOT EXISTS
FOR (c:Comment) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT image_url_unique IF NOT EXISTS
FOR (i:Image) REQUIRE i.url IS UNIQUE;

// Create indexes for common queries
CREATE INDEX comment_created_utc_index IF NOT EXISTS
FOR (c:Comment) ON (c.created_utc);

CREATE INDEX comment_score_index IF NOT EXISTS
FOR (c:Comment) ON (c.score);

CREATE INDEX comment_is_submitter_index IF NOT EXISTS
FOR (c:Comment) ON (c.is_submitter);

CREATE INDEX image_created_at_index IF NOT EXISTS
FOR (i:Image) ON (i.created_at);








