"""YouTube polling worker for monitoring channels and fetching new videos."""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from feed.storage.neo4j_connection import get_connection
from feed.services.youtube_enhanced_service import YouTubeEnhancedService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubePollingWorker:
    """Worker for polling YouTube channels and fetching new content."""
    
    def __init__(self, poll_interval_minutes: int = 60):
        self.poll_interval = poll_interval_minutes
        self.neo4j = get_connection()
        self.youtube_service = YouTubeEnhancedService()
    
    def get_subscribed_channels(self) -> List[Dict]:
        """Get all channels with active subscriptions."""
        query = """
        MATCH (c:Creator)-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
        WHERE sub.status = 'active'
        OPTIONAL MATCH (c)-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p)
        RETURN 
            c.slug as creator_slug,
            c.name as creator_name,
            h.profile_url as profile_url,
            h.username as handle,
            sub.poll_interval_hours as poll_interval_hours,
            sub.last_polled_at as last_polled_at
        ORDER BY sub.last_polled_at ASC
        """
        
        result = self.neo4j.execute_read(query)
        return [dict(record) for record in result]
    
    def fetch_channel_videos(self, profile_url: str, since_date: Optional[str] = None) -> List[Dict]:
        """Fetch videos from a channel, optionally since a specific date."""
        import subprocess
        import json
        
        cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--quiet", "--flat-playlist"]
        
        if since_date:
            cmd.extend(["--dateafter", since_date])
        
        cmd.append(profile_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    videos.append(json.loads(line))
            return videos
        except subprocess.CalledProcessError as e:
            logger.error(f"Error fetching channel videos: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def poll_channel(self, channel: Dict) -> Dict:
        """Poll a single channel for new videos."""
        creator_slug = channel["creator_slug"]
        profile_url = channel["profile_url"]
        handle = channel.get("handle", "")
        
        logger.info(f"Polling channel: {creator_slug} ({handle})")
        
        # Calculate last poll date
        last_polled = channel.get("last_polled_at")
        since_date = None
        if last_polled:
            since_date = last_polled.strftime("%Y%m%d")
        
        # Fetch videos
        videos = self.fetch_channel_videos(profile_url, since_date)
        
        if not videos:
            logger.info(f"No new videos for {creator_slug}")
            self.update_poll_status(creator_slug, success=True, new_videos=0)
            return {"creator_slug": creator_slug, "new_videos": 0}
        
        logger.info(f"Found {len(videos)} videos for {creator_slug}")
        
        # Process each video
        processed_count = 0
        for video in videos:
            try:
                video_url = video.get("webpage_url") or video.get("url")
                if not video_url:
                    continue
                
                # Check if video already exists
                video_id = video.get("id")
                if self.video_exists(video_id):
                    logger.debug(f"Video {video_id} already exists, skipping")
                    continue
                
                # Fetch and store enhanced metadata
                enhanced_data = self.youtube_service.fetch_video_metadata(video_url)
                if enhanced_data:
                    self.youtube_service.store_video_with_all_features(
                        enhanced_data,
                        creator_slug=creator_slug
                    )
                    processed_count += 1
                    logger.info(f"Processed video: {enhanced_data.get('title')}")
                    
            except Exception as e:
                logger.error(f"Error processing video: {e}")
                continue
        
        # Update poll status
        self.update_poll_status(
            creator_slug,
            success=True,
            new_videos=processed_count
        )
        
        return {
            "creator_slug": creator_slug,
            "new_videos": processed_count
        }
    
    def video_exists(self, video_id: str) -> bool:
        """Check if a video already exists in database."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})
        RETURN count(v) > 0 as exists
        """
        
        result = self.neo4j.execute_read(query, parameters={"video_id": video_id})
        return result[0]["exists"] if result else False
    
    def update_poll_status(
        self,
        creator_slug: str,
        success: bool,
        new_videos: int = 0
    ) -> None:
        """Update subscription poll status."""
        query = """
        MATCH (c:Creator {slug: $slug})-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
        SET sub.last_polled_at = datetime(),
            sub.updated_at = datetime()
        """
        
        params = {"slug": creator_slug}
        
        if success:
            query += ", sub.last_successful_poll = datetime()"
            query += ", sub.poll_count_24h = COALESCE(sub.poll_count_24h, 0) + 1"
        else:
            query += ", sub.error_count_24h = COALESCE(sub.error_count_24h, 0) + 1"
        
        self.neo4j.execute_write(query, parameters=params)
        
        logger.info(f"Updated poll status for {creator_slug}: {new_videos} new videos")
    
    def run_once(self) -> Dict[str, Dict]:
        """Run a single poll cycle for all channels."""
        logger.info("Starting poll cycle...")
        
        channels = self.get_subscribed_channels()
        
        if not channels:
            logger.warning("No subscribed channels found")
            return {}
        
        results = {}
        for channel in channels:
            try:
                result = self.poll_channel(channel)
                results[channel["creator_slug"]] = result
            except Exception as e:
                logger.error(f"Error polling {channel['creator_slug']}: {e}")
                self.update_poll_status(channel["creator_slug"], success=False)
                results[channel["creator_slug"]] = {
                    "creator_slug": channel["creator_slug"],
                    "error": str(e)
                }
        
        logger.info(f"Poll cycle completed. Processed {len(results)} channels.")
        return results
    
    def run_continuous(self) -> None:
        """Run continuous polling loop."""
        logger.info(f"Starting continuous polling (interval: {self.poll_interval} minutes)")
        
        while True:
            try:
                self.run_once()
                
                # Wait for next poll
                logger.info(f"Waiting {self.poll_interval} minutes until next poll...")
                time.sleep(self.poll_interval * 60)
                
            except KeyboardInterrupt:
                logger.info("Polling worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in polling cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube polling worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll cycle then exit"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in minutes (default: 60)"
    )
    
    args = parser.parse_args()
    
    worker = YouTubePollingWorker(poll_interval_minutes=args.interval)
    
    if args.once:
        results = worker.run_once()
        print("\nPoll results:")
        for creator_slug, result in results.items():
            print(f"  {creator_slug}: {result.get('new_videos', 0)} new videos")
    else:
        worker.run_continuous()


if __name__ == "__main__":
    main()
