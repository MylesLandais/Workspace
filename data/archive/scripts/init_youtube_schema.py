#!/usr/bin/env python3
"""Initialize Neo4j database schema for enhanced YouTube features."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def initialize_schema():
    """Initialize Neo4j database schema for YouTube."""
    neo4j = get_connection()
    
    print("Initializing Neo4j schema for enhanced YouTube features...")
    
    # Create constraints
    print("Creating constraints...")
    constraints = [
        # Video constraints
        "CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:YouTubeVideo) REQUIRE v.video_id IS UNIQUE",
        "CREATE CONSTRAINT youtube_video_uuid_unique IF NOT EXISTS FOR (v:YouTubeVideo) REQUIRE v.uuid IS UNIQUE",
        
        # Comment constraints
        "CREATE CONSTRAINT comment_id_unique IF NOT EXISTS FOR (c:YouTubeComment) REQUIRE c.comment_id IS UNIQUE",
        
        # Chapter constraints
        "CREATE CONSTRAINT chapter_unique IF NOT EXISTS FOR (c:YouTubeChapter) REQUIRE c.video_id IS NOT NULL AND c.index IS NOT NULL",
        
        # Transcript constraints
        "CREATE CONSTRAINT transcript_unique IF NOT EXISTS FOR (t:YouTubeTranscript) REQUIRE t.uuid IS UNIQUE"
    ]
    
    for constraint in constraints:
        try:
            neo4j.execute_write(constraint)
            print(f"  ✓ {constraint[:50]}...")
        except Exception as e:
            print(f"  ✗ {constraint[:50]}... ({e})")
    
    # Create indexes
    print("\nCreating indexes...")
    indexes = [
        # Video indexes
        "CREATE INDEX video_published_at IF NOT EXISTS FOR (v:YouTubeVideo) ON (v.published_at)",
        "CREATE INDEX video_channel_id IF NOT EXISTS FOR (v:YouTubeVideo) ON (v.channel_id)",
        
        # Comment indexes
        "CREATE INDEX comment_timestamp IF NOT EXISTS FOR (c:YouTubeComment) ON (c.timestamp)",
        "CREATE INDEX comment_author IF NOT EXISTS FOR (c:YouTubeComment) ON (c.author)",
        "CREATE INDEX comment_video_id IF NOT EXISTS FOR (c:YouTubeComment) ON (c.video_id)",
        
        # Chapter indexes
        "CREATE INDEX chapter_start_time IF NOT EXISTS FOR (c:YouTubeChapter) ON (c.start_time)",
        
        # Transcript indexes
        "CREATE INDEX transcript_start_time IF NOT EXISTS FOR (t:YouTubeTranscript) ON (t.start_time)"
    ]
    
    for index in indexes:
        try:
            neo4j.execute_write(index)
            print(f"  ✓ {index[:50]}...")
        except Exception as e:
            print(f"  ✗ {index[:50]}... ({e})")
    
    # Create fulltext indexes
    print("\nCreating fulltext indexes...")
    fulltext_indexes = [
        "CREATE FULLTEXT INDEX video_title_ft IF NOT EXISTS FOR (v:YouTubeVideo) ON EACH [v.title, v.description]",
        "CREATE FULLTEXT INDEX comment_text_ft IF NOT EXISTS FOR (c:YouTubeComment) ON EACH [c.text]"
    ]
    
    for index in fulltext_indexes:
        try:
            neo4j.execute_write(index)
            print(f"  ✓ {index[:50]}...")
        except Exception as e:
            print(f"  ✗ {index[:50]}... ({e})")
    
    print("\n✓ Schema initialization complete!")
    
    neo4j.close()

if __name__ == "__main__":
    initialize_schema()
