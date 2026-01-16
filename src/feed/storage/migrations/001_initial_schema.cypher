// Initial graph schema for feed engine
// Run this migration to set up the graph database

// Create constraints for unique properties
CREATE CONSTRAINT post_id_unique IF NOT EXISTS
FOR (p:Post) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT subreddit_name_unique IF NOT EXISTS
FOR (s:Subreddit) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE;

// Create indexes for common queries
CREATE INDEX post_created_utc_index IF NOT EXISTS
FOR (p:Post) ON (p.created_utc);

CREATE INDEX post_score_index IF NOT EXISTS
FOR (p:Post) ON (p.score);

CREATE INDEX post_subreddit_index IF NOT EXISTS
FOR (p:Post) ON (p.subreddit);








