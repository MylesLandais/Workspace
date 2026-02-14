"""Neo4j schema for full YouTube feed features."""

CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:YouTubeVideo) REQUIRE v.video_id IS UNIQUE;
CREATE CONSTRAINT comment_id_unique IF NOT EXISTS FOR (c:YouTubeComment) REQUIRE c.comment_id IS UNIQUE;

CREATE FULLTEXT INDEX video_title_ft IF NOT EXISTS FOR (v:YouTubeVideo) ON EACH [v.title, v.description];
CREATE FULLTEXT INDEX comment_text_ft IF NOT EXISTS FOR (c:YouTubeComment) ON EACH [c.text];

CREATE INDEX video_published_at IF NOT EXISTS FOR (v:YouTubeVideo) ON (v.published_at);
CREATE INDEX channel_videos IF NOT EXISTS FOR (c:YouTubeChannel) ON (c.channel_id);

// Enhanced YouTube Video Node
// Properties: video_id, title, description, duration, view_count, like_count, comment_count, published_at, thumbnail_url, channel_id, transcript, chapters, related_videos
