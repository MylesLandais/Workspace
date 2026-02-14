"""YouTube video metadata enhancement service with full features."""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from feed.storage.neo4j_connection import get_connection

class YouTubeEnhancedService:
    """Service for enhanced YouTube data fetching and storage."""
    
    def __init__(self):
        self.neo4j = get_connection()
    
    def _run_ytdlp(self, args: List[str]) -> Optional[Dict]:
        """Run yt-dlp and return parsed JSON output."""
        cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--quiet"] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout.strip():
                return json.loads(result.stdout)
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error running yt-dlp: {e.stderr}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def fetch_video_metadata(self, video_url: str) -> Optional[Dict]:
        """Fetch comprehensive video metadata including comments, transcript, chapters."""
        print(f"Fetching metadata for: {video_url}")
        
        # Fetch basic video info with all details
        metadata = self._run_ytdlp([
            "--write-info-json",
            "--write-subtitles",
            "--write-auto-sub",
            "--sub-langs", "en,en-US,en-GB",
            "--skip-download",
            video_url
        ])
        
        if not metadata:
            print("Failed to fetch video metadata")
            return None
        
        # Extract video ID
        video_id = metadata.get("id") or video_url.split("v=")[-1].split("&")[0]
        
        # Extract chapters
        chapters = self._extract_chapters(metadata)
        
        # Extract transcript (if available from auto-captions)
        transcript = self._extract_transcript(metadata)
        
        # Fetch comments (using yt-dlp's comment extraction)
        comments = self._fetch_comments(video_url)
        
        # Fetch related videos
        related = self._fetch_related_videos(video_url)
        
        enhanced_data = {
            "video_id": video_id,
            "title": metadata.get("title"),
            "description": metadata.get("description"),
            "url": metadata.get("webpage_url"),
            "duration": metadata.get("duration"),
            "view_count": metadata.get("view_count"),
            "like_count": metadata.get("like_count"),
            "comment_count": metadata.get("comment_count"),
            "published_at": metadata.get("upload_date"),
            "thumbnail_url": metadata.get("thumbnail"),
            "channel_id": metadata.get("channel_id"),
            "channel_name": metadata.get("channel"),
            "uploader_id": metadata.get("uploader_id"),
            "tags": metadata.get("tags", []),
            "categories": metadata.get("categories", []),
            "transcript": transcript,
            "chapters": chapters,
            "comments": comments,
            "related_videos": related
        }
        
        return enhanced_data
    
    def _extract_chapters(self, metadata: Dict) -> List[Dict[str, Any]]:
        """Extract chapter markers from metadata."""
        chapters = metadata.get("chapters", [])
        if not chapters:
            # Try to extract chapters from description (if available)
            chapters = self._parse_chapters_from_description(metadata.get("description", ""))
        
        enhanced_chapters = []
        for i, chapter in enumerate(chapters):
            enhanced_chapters.append({
                "index": i,
                "title": chapter.get("title", f"Chapter {i+1}"),
                "start_time": chapter.get("start_time", 0),
                "end_time": chapter.get("end_time", 0),
                "timestamp": self._format_timestamp(chapter.get("start_time", 0))
            })
        
        return enhanced_chapters
    
    def _parse_chapters_from_description(self, description: str) -> List[Dict]:
        """Parse chapter timestamps from video description."""
        chapters = []
        import re
        
        # Pattern: "0:00 Intro", "0:00 - Intro", "00:00 Intro"
        patterns = [
            r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]?\s*(.+?)(?:\n|$)',
            r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, description, re.MULTILINE)
            for i, match in enumerate(matches):
                timestamp = match.group(1)
                title = match.group(2).strip()
                
                # Parse timestamp to seconds
                parts = timestamp.split(':')
                if len(parts) == 2:
                    start_time = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    start_time = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    continue
                
                if chapters:
                    # Update previous chapter's end_time
                    chapters[-1]["end_time"] = start_time
                
                chapters.append({
                    "title": title,
                    "start_time": start_time,
                    "end_time": 0  # Will be set by next chapter
                })
            
            if chapters:
                break
        
        return chapters
    
    def _extract_transcript(self, metadata: Dict) -> Optional[List[Dict]]:
        """Extract transcript from auto-generated captions."""
        # Note: This is a simplified version
        # For full transcript, you'd need to parse the subtitle files
        # that yt-dlp writes with --write-auto-sub
        
        transcript = metadata.get("subtitles", [])
        if not transcript:
            return None
        
        # Return transcript segments
        return [
            {
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", "")
            }
            for seg in transcript
        ]
    
    def _fetch_comments(self, video_url: str, max_comments: int = 100) -> List[Dict]:
        """Fetch comments for a video."""
        print(f"Fetching comments (max {max_comments})...")
        
        comments_data = self._run_ytdlp([
            "--write-comments",
            "--skip-download",
            "--max-comments", str(max_comments),
            video_url
        ])
        
        if not comments_data:
            return []
        
        comments = comments_data.get("comments", [])
        enhanced_comments = []
        
        for i, comment in enumerate(comments):
            comment_id = comment.get("id", f"comment_{uuid4()}")
            enhanced_comments.append({
                "comment_id": comment_id,
                "video_id": comment.get("parent", ""),
                "text": comment.get("text", ""),
                "author": comment.get("author", ""),
                "author_id": comment.get("author_id", ""),
                "like_count": comment.get("like_count", 0),
                "reply_count": comment.get("reply_count", 0),
                "is_reply": comment.get("is_reply", False),
                "parent_id": comment.get("parent", ""),
                "timestamp": comment.get("timestamp", 0),
                "html": comment.get("html", "")
            })
        
        return enhanced_comments
    
    def _fetch_related_videos(self, video_url: str, max_related: int = 20) -> List[Dict]:
        """Fetch related/recommended videos."""
        print(f"Fetching related videos (max {max_related})...")
        
        # yt-dlp doesn't directly provide related videos
        # This would require using YouTube API or scraping
        # For now, return empty list to be implemented with API
        
        return []
    
    def store_video_with_all_features(self, video_data: Dict, creator_slug: Optional[str] = None) -> str:
        """Store complete video data with all features in Neo4j."""
        video_id = video_data["video_id"]
        
        print(f"Storing video {video_id} with all features...")
        
        # 1. Create or update YouTube Video node
        video_query = """
        MERGE (v:YouTubeVideo {video_id: $video_id})
        ON CREATE SET
            v.uuid = $uuid,
            v.title = $title,
            v.url = $url,
            v.description = $description,
            v.duration = $duration,
            v.view_count = $view_count,
            v.like_count = $like_count,
            v.comment_count = $comment_count,
            v.published_at = datetime($published_at),
            v.thumbnail_url = $thumbnail_url,
            v.channel_id = $channel_id,
            v.channel_name = $channel_name,
            v.tags = $tags,
            v.categories = $categories,
            v.created_at = datetime(),
            v.updated_at = datetime()
        ON MATCH SET
            v.title = COALESCE($title, v.title),
            v.description = COALESCE($description, v.description),
            v.duration = COALESCE($duration, v.duration),
            v.view_count = COALESCE($view_count, v.view_count),
            v.like_count = COALESCE($like_count, v.like_count),
            v.comment_count = COALESCE($comment_count, v.comment_count),
            v.thumbnail_url = COALESCE($thumbnail_url, v.thumbnail_url),
            v.tags = COALESCE($tags, v.tags),
            v.categories = COALESCE($categories, v.categories),
            v.updated_at = datetime()
        RETURN v
        """
        
        params = {
            "video_id": video_id,
            "uuid": str(uuid4()),
            "title": video_data.get("title"),
            "url": video_data.get("url"),
            "description": video_data.get("description"),
            "duration": video_data.get("duration"),
            "view_count": video_data.get("view_count"),
            "like_count": video_data.get("like_count"),
            "comment_count": video_data.get("comment_count"),
            "published_at": video_data.get("published_at"),
            "thumbnail_url": video_data.get("thumbnail_url"),
            "channel_id": video_data.get("channel_id"),
            "channel_name": video_data.get("channel_name"),
            "tags": json.dumps(video_data.get("tags", [])),
            "categories": json.dumps(video_data.get("categories", []))
        }
        
        self.neo4j.execute_write(video_query, parameters=params)
        
        # 2. Link to creator if provided
        if creator_slug:
            link_query = """
            MATCH (v:YouTubeVideo {video_id: $video_id})
            MATCH (c:Creator {slug: $creator_slug})
            MATCH (h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
            WHERE h.profile_url = 'https://www.youtube.com/@' + $channel_name
            OR h.profile_url CONTAINS $channel_id
            MERGE (c)-[r:PUBLISHED]->(v)
            ON CREATE SET
                r.published_at = datetime($published_at),
                r.created_at = datetime()
            RETURN r
            """
            
            self.neo4j.execute_write(link_query, parameters={
                "video_id": video_id,
                "creator_slug": creator_slug,
                "channel_name": video_data.get("channel_name", ""),
                "channel_id": video_data.get("channel_id", ""),
                "published_at": video_data.get("published_at")
            })
        
        # 3. Store chapters
        if video_data.get("chapters"):
            self._store_chapters(video_id, video_data["chapters"])
        
        # 4. Store comments
        if video_data.get("comments"):
            self._store_comments(video_id, video_data["comments"])
        
        # 5. Store transcript
        if video_data.get("transcript"):
            self._store_transcript(video_id, video_data["transcript"])
        
        print(f"✓ Stored video {video_id} with all features")
        return video_id
    
    def _store_chapters(self, video_id: str, chapters: List[Dict]) -> None:
        """Store chapter markers for a video."""
        print(f"  Storing {len(chapters)} chapters...")
        
        chapter_query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})
        UNWIND $chapters as chapter
        MERGE (v)-[:HAS_CHAPTER]->(c:YouTubeChapter {
            video_id: $video_id,
            index: chapter.index
        })
        ON CREATE SET
            c.uuid = chapter.uuid,
            c.title = chapter.title,
            c.start_time = chapter.start_time,
            c.end_time = chapter.end_time,
            c.timestamp = chapter.timestamp,
            c.created_at = datetime()
        ON MATCH SET
            c.title = chapter.title,
            c.start_time = chapter.start_time,
            c.end_time = chapter.end_time,
            c.updated_at = datetime()
        """
        
        chapters_with_uuid = [
            {**ch, "uuid": str(uuid4())}
            for ch in chapters
        ]
        
        self.neo4j.execute_write(chapter_query, parameters={
            "video_id": video_id,
            "chapters": chapters_with_uuid
        })
    
    def _store_comments(self, video_id: str, comments: List[Dict]) -> None:
        """Store comments for a video."""
        print(f"  Storing {len(comments)} comments...")
        
        # Delete existing comments for this video (optional, based on your strategy)
        delete_query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        DETACH DELETE c
        """
        self.neo4j.execute_write(delete_query, parameters={"video_id": video_id})
        
        # Store new comments
        comment_query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})
        UNWIND $comments as comment
        MERGE (c:YouTubeComment {comment_id: comment.comment_id})
        ON CREATE SET
            c.uuid = comment.uuid,
            c.text = comment.text,
            c.author = comment.author,
            c.author_id = comment.author_id,
            c.like_count = comment.like_count,
            c.reply_count = comment.reply_count,
            c.is_reply = comment.is_reply,
            c.parent_id = comment.parent_id,
            c.timestamp = datetime(),
            c.created_at = datetime()
        ON MATCH SET
            c.text = comment.text,
            c.like_count = comment.like_count,
            c.reply_count = comment.reply_count,
            c.updated_at = datetime()
        MERGE (v)-[:HAS_COMMENT]->(c)
        """
        
        comments_with_uuid = [
            {**c, "uuid": str(uuid4())}
            for c in comments
        ]
        
        self.neo4j.execute_write(comment_query, parameters={
            "video_id": video_id,
            "comments": comments_with_uuid
        })
    
    def _store_transcript(self, video_id: str, transcript: List[Dict]) -> None:
        """Store transcript segments for a video."""
        print(f"  Storing transcript with {len(transcript)} segments...")
        
        # Delete existing transcript
        delete_query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_TRANSCRIPT_SEGMENT]->(t:YouTubeTranscript)
        DETACH DELETE t
        """
        self.neo4j.execute_write(delete_query, parameters={"video_id": video_id})
        
        # Store new transcript
        transcript_query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})
        UNWIND $transcript as segment
        CREATE (v)-[:HAS_TRANSCRIPT_SEGMENT]->(t:YouTubeTranscript {
            uuid: segment.uuid,
            start_time: segment.start,
            end_time: segment.end,
            text: segment.text,
            created_at = datetime()
        })
        """
        
        transcript_with_uuid = [
            {**seg, "uuid": str(uuid4())}
            for seg in transcript
        ]
        
        self.neo4j.execute_write(transcript_query, parameters={
            "video_id": video_id,
            "transcript": transcript_with_uuid
        })
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to timestamp string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced YouTube video fetcher")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--creator", help="Creator slug to link to")
    
    args = parser.parse_args()
    
    service = YouTubeEnhancedService()
    
    # Fetch and store video with all features
    video_data = service.fetch_video_metadata(args.url)
    
    if video_data:
        video_id = service.store_video_with_all_features(video_data, creator_slug=args.creator)
        print(f"\n✓ Successfully stored video {video_id} with full features")
    else:
        print("\n✗ Failed to fetch video metadata")
