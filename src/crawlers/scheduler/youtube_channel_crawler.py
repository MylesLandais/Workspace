#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 python3Packages.requests yt-dlp

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.feed.services.youtube_subscription_service import YouTubeSubscriptionService

class YouTubeChannelCrawler:
    def __init__(self, cache_dir: str = "./cache/youtube"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _run_ytdlp(self, args: List[str]) -> Optional[List[Dict]]:
        """Run yt-dlp and return parsed JSON output."""
        cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--quiet", "--flat-playlist"] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    videos.append(json.loads(line))
            return videos
        except subprocess.CalledProcessError as e:
            print(f"Error running yt-dlp: {e.stderr}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def get_channel_videos(self, channel_url: str, latest_count: int = 5, oldest_count: int = 10) -> Dict:
        """
        Fetch the latest and oldest videos from a channel.
        """
        print(f"Crawling channel: {channel_url}")
        
        # Fetch latest videos
        print(f"Fetching latest {latest_count} videos...")
        latest_videos = self._run_ytdlp([
            "--playlist-end", str(latest_count),
            channel_url
        ]) or []

        # Fetch oldest videos
        print(f"Fetching first {oldest_count} videos...")
        oldest_videos = self._run_ytdlp([
            "--playlist-reverse",
            "--playlist-end", str(oldest_count),
            channel_url
        ]) or []

        data = {
            "channel_url": channel_url,
            "crawled_at": datetime.utcnow().isoformat(),
            "latest_videos": self._simplify_metadata(latest_videos),
            "oldest_videos": self._simplify_metadata(oldest_videos)
        }

        self._save_to_cache(channel_url, data)
        return data

    def _simplify_metadata(self, videos: List[Dict]) -> List[Dict]:
        """Extract only relevant fields from yt-dlp output."""
        simplified = []
        for v in videos:
            simplified.append({
                "id": v.get("id"),
                "title": v.get("title"),
                "url": v.get("webpage_url"),
                "thumbnail": v.get("thumbnail"),
                "description": v.get("description"),
                "duration": v.get("duration"),
                "view_count": v.get("view_count"),
                "upload_date": v.get("upload_date"),
                "uploader": v.get("uploader"),
                "uploader_id": v.get("uploader_id")
            })
        return simplified

    def _save_to_cache(self, channel_url: str, data: Dict):
        """Save crawled data to local JSON cache."""
        # Create a safe filename from the URL
        safe_name = channel_url.split("/")[-1].replace("@", "")
        cache_file = self.cache_dir / f"{safe_name}_feed.json"
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Cached data to {cache_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Channel Crawler")
    parser.add_argument("url", help="YouTube channel URL (e.g., https://www.youtube.com/@Fasffy)")
    parser.add_argument("--latest", type=int, default=5, help="Number of latest videos to grab")
    parser.add_argument("--oldest", type=int, default=10, help="Number of oldest videos to grab")
    parser.add_argument("--cache-dir", default="./cache/youtube", help="Directory for offline caching")

    args = parser.parse_args()

    crawler = YouTubeChannelCrawler(cache_dir=args.cache_dir)
    result = crawler.get_channel_videos(args.url, latest_count=args.latest, oldest_count=args.oldest)
    
    print(f"\nSuccess! Found {len(result['latest_videos'])} latest and {len(result['oldest_videos'])} oldest videos.")

    # Integration with YouTubeSubscriptionService
    try:
        # Set VALKEY_URI to use the service name in docker network
        os.environ["VALKEY_URI"] = "cache.jupyter.dev.local:6379"
        service = YouTubeSubscriptionService()
        # Extract handle from URL
        handle = args.url.split("/")[-1]
        if not handle.startswith("@"):
            handle = f"@{handle}"
        
        creator_slug = handle.replace("@", "").lower().replace(".", "_")
        
        print(f"Updating graph for creator: {creator_slug}")
        
        # Ensure creator exists
        service.create_creator(name=handle, slug=creator_slug)
        
        # Add handle
        service.add_youtube_handle(
            creator_slug=creator_slug,
            handle=handle,
            display_name=handle,
            profile_url=args.url,
            verified=True
        )
        
        # Create subscription
        service.create_subscription(creator_slug=creator_slug)
        
        print(f"Graph updated successfully for {handle}")

        # Link specific video if provided
        video_url = "https://www.youtube.com/watch?v=2M4b4z_VEcM"
        print(f"Linking specific video: {video_url}")
        
        # We can use a raw query to link the video to the creator/handle
        video_id = video_url.split("v=")[-1].split("&")[0]
        link_query = """
        MATCH (c:Creator {slug: $creator_slug})
        MERGE (v:Media {source_url: $video_url})
        ON CREATE SET v.title = $video_title,
                      v.media_type = 'Video',
                      v.platform_slug = 'youtube',
                      v.created_at = datetime()
        MERGE (c)-[:PRODUCED]->(v)
        RETURN v
        """
        service.neo4j.execute_write(
            link_query,
            parameters={
                "creator_slug": creator_slug,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_title": "Paige Anastasi Video"
            }
        )
        print(f"Linked video {video_id} to {creator_slug}")
        
    except Exception as e:
        print(f"Failed to update graph: {e}")
