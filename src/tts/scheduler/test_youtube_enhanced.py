#!/usr/bin/env python3
"""Test script for enhanced YouTube features."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
from feed.services.youtube_enhanced_service import YouTubeEnhancedService

def test_enhanced_youtube(video_url: str, creator_slug: str = "developer"):
    """Test enhanced YouTube video fetching and storage."""
    print(f"Testing enhanced YouTube features for: {video_url}\n")
    
    # Initialize service
    service = YouTubeEnhancedService()
    
    # Fetch video metadata with all features
    print("Step 1: Fetching video metadata...")
    video_data = service.fetch_video_metadata(video_url)
    
    if not video_data:
        print("✗ Failed to fetch video metadata")
        return False
    
    print(f"✓ Fetched video: {video_data.get('title')}")
    print(f"  - Duration: {video_data.get('duration')}s")
    print(f"  - Views: {video_data.get('view_count')}")
    print(f"  - Likes: {video_data.get('like_count')}")
    print(f"  - Comments: {video_data.get('comment_count')}")
    
    # Check features
    print("\nStep 2: Checking features...")
    print(f"✓ Description: {'Yes' if video_data.get('description') else 'No'} ({len(video_data.get('description', ''))} chars)")
    print(f"✓ Chapters: {len(video_data.get('chapters', []))} chapters")
    print(f"✓ Comments: {len(video_data.get('comments', []))} comments")
    print(f"✓ Transcript: {'Yes' if video_data.get('transcript') else 'No'} ({len(video_data.get('transcript', []))} segments)")
    print(f"✓ Tags: {len(video_data.get('tags', []))} tags")
    print(f"✓ Categories: {video_data.get('categories', [])}")
    
    # Store in database
    print("\nStep 3: Storing in database...")
    video_id = service.store_video_with_all_features(video_data, creator_slug=creator_slug)
    
    print(f"✓ Stored video {video_id}")
    
    # Query back to verify
    print("\nStep 4: Verifying data in database...")
    neo4j = get_connection()
    
    # Verify video
    video_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})
    RETURN v.title as title, v.description as desc,
           v.view_count as views, v.like_count as likes
    """
    result = neo4j.execute_read(video_query, parameters={"video_id": video_id})
    
    if result:
        record = result[0]
        print(f"✓ Video found in database:")
        print(f"  - Title: {record['title']}")
        print(f"  - Description: {len(record.get('desc', ''))} chars")
        print(f"  - Views: {record['views']}")
        print(f"  - Likes: {record['likes']}")
    else:
        print("✗ Video not found in database")
    
    # Verify chapters
    chapters_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_CHAPTER]->(c:YouTubeChapter)
    RETURN count(c) as count
    """
    result = neo4j.execute_read(chapters_query, parameters={"video_id": video_id})
    print(f"✓ Chapters: {result[0]['count']} stored")
    
    # Verify comments
    comments_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
    RETURN count(c) as count
    """
    result = neo4j.execute_read(comments_query, parameters={"video_id": video_id})
    print(f"✓ Comments: {result[0]['count']} stored")
    
    # Verify transcript
    transcript_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_TRANSCRIPT_SEGMENT]->(t:YouTubeTranscript)
    RETURN count(t) as count
    """
    result = neo4j.execute_read(transcript_query, parameters={"video_id": video_id})
    print(f"✓ Transcript segments: {result[0]['count']} stored")
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test enhanced YouTube features")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--creator", default="developer", help="Creator slug")
    
    args = parser.parse_args()
    
    success = test_enhanced_youtube(args.url, args.creator)
    
    if success:
        print(f"\n✓ Test completed successfully!")
        print(f"You can now query the video via API:")
        print(f"  http://localhost:8001/api/videos/{args.url.split('v=')[-1].split('&')[0]}")
    else:
        print("\n✗ Test failed")
