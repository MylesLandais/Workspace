// Migration: Add YouTube video tracking support
// This enables tracking YouTube videos mentioned in Reddit threads

// Create constraint for unique video IDs
CREATE CONSTRAINT youtube_video_id_unique IF NOT EXISTS
FOR (v:YouTubeVideo) REQUIRE v.video_id IS UNIQUE;

// Create indexes for common queries
CREATE INDEX youtube_video_created_at_index IF NOT EXISTS
FOR (v:YouTubeVideo) ON (v.created_at);

CREATE INDEX youtube_video_url_index IF NOT EXISTS
FOR (v:YouTubeVideo) ON (v.url);

// Note: Relationships are created programmatically:
// - (Post)-[:REFERENCES_VIDEO {source_type: "comment", source_author: "username", discovered_at: datetime()}]->(YouTubeVideo)
//   Used when a comment/post contains a YouTube URL







