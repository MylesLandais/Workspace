#!/usr/bin/env python3
"""Subscribe to a YouTube channel from a video URL reference."""
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from feed.services.youtube_subscription_service import YouTubeSubscriptionService
    from feed.storage.neo4j_connection import get_connection
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def extract_video_id(youtube_url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    import re
    
    # Short URL: youtu.be/VIDEO_ID
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[-1].split("?")[0]
    
    # Watch URL: youtube.com/watch?v=VIDEO_ID
    elif "watch?v=" in youtube_url:
        return youtube_url.split("v=")[-1].split("&")[0]
    
    # Other formats
    elif "/v=" in youtube_url:
        return youtube_url.split("/v=")[-1].split("?")[0]
    
    return None


def subscribe_by_video_url(
    video_url: str,
    creator_slug: str,
    channel_name: str,
    poll_interval_hours: int = 24
):
    """Subscribe to a channel using a video URL for reference."""
    
    video_id = extract_video_id(video_url)
    
    if not video_id:
        print(f"Failed to extract video ID from: {video_url}")
        return False
    
    print(f"\nSubscribing to channel...")
    print(f"Video URL: {video_url}")
    print(f"Video ID: {video_id}")
    print(f"Channel Name: {channel_name}")
    print(f"Creator Slug: {creator_slug}")
    print()
    
    # Initialize subscription service
    print("Initializing YouTube subscription service...")
    service = YouTubeSubscriptionService()
    
    # Ensure creator exists
    print(f"Creating/updating creator: {creator_slug}")
    service.create_creator(
        name=channel_name,
        slug=creator_slug,
        bio=f"YouTube channel (subscribed via video {video_id})",
        avatar_url=None
    )
    
    # Add YouTube handle (using @ format)
    handle = f"@{creator_slug}"
    profile_url = f"https://www.youtube.com/@{creator_slug}"
    
    print(f"Adding YouTube handle for: {handle}")
    success = service.add_youtube_handle(
        creator_slug=creator_slug,
        handle=handle,
        display_name=channel_name,
        profile_url=profile_url,
        follower_count=None,
        verified=True
    )
    
    if not success:
        print("Failed to add YouTube handle")
        return False
    
    # Create subscription
    print(f"Creating subscription for: {creator_slug}")
    success = service.create_subscription(
        creator_slug=creator_slug,
        poll_interval_hours=poll_interval_hours
    )
    
    if not success:
        print("Failed to create subscription")
        return False
    
    # Link video to creator (for reference)
    print(f"Linking video {video_id} to creator {creator_slug}")
    try:
        neo4j = get_connection()
        
        video_link_query = """
        MATCH (c:Creator {slug: $creator_slug})
        MERGE (v:YouTubeVideo {video_id: $video_id})
        ON CREATE SET v.title = $video_title,
                      v.url = $video_url,
                      v.platform_slug = 'youtube',
                      v.created_at = datetime()
        MERGE (c)-[:PRODUCED]->(v)
        RETURN v
        """
        
        neo4j.execute_write(
            video_link_query,
            parameters={
                "creator_slug": creator_slug,
                "video_id": video_id,
                "video_title": "Subscribed via video",
                "video_url": f"https://www.youtube.com/watch?v={video_id}"
            }
        )
        print(f"Linked video {video_id} to creator {creator_slug}")
    except Exception as e:
        print(f"Warning: Failed to link video to creator: {e}")
    
    # Invalidate cache
    print("Invalidating cache...")
    service.invalidate_creator_cache(creator_slug)
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Subscribed to YouTube channel: {channel_name}")
    print(f"Creator slug: {creator_slug}")
    print(f"Handle: {handle}")
    print(f"Poll interval: {poll_interval_hours} hours")
    print(f"Reference video: {video_id}")
    print("=" * 60)
    
    return True


def list_current_subscriptions():
    """List all current YouTube subscriptions."""
    print("Current YouTube subscriptions:")
    print("-" * 60)
    
    service = YouTubeSubscriptionService()
    subscriptions = service.list_all_subscriptions()
    
    if not subscriptions:
        print("No active subscriptions found.")
        return
    
    for sub in subscriptions:
        print(f"  - {sub['handle_username']} ({sub['creator_name']})")
        print(f"    Slug: {sub['creator_slug']}")
        print(f"    Status: {sub['subscription_status']}")
        print(f"    Last polled: {sub['last_polled_at']}")
        print(f"    Poll interval: {sub['poll_interval_hours']}h")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subscribe to YouTube channel (simplified version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Subscribe using video URL and creator info
  python simple_youtube_subscribe.py https://youtu.be/zPg4-YoGnF0 --slug mychannel --name \"My Channel\"

  # Subscribe with custom poll interval
  python simple_youtube_subscribe.py https://youtu.be/zPg4-YoGnF0 --slug mychannel --name \"My Channel\" --interval 12

  # List all subscriptions
  python simple_youtube_subscribe.py --list
        """
    )
    
    parser.add_argument("url", nargs="?", help="YouTube video URL (for reference)")
    parser.add_argument("--slug", help="Creator slug (URL-friendly identifier)")
    parser.add_argument("--name", help="Channel display name")
    parser.add_argument("--interval", type=int, default=24, help="Poll interval in hours (default: 24)")
    parser.add_argument("--list", action="store_true", help="List all current subscriptions")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.list and (args.url or args.slug or args.name):
        parser.error("--list cannot be used with url, --slug, or --name")
    
    if not args.list and not (args.url and args.slug and args.name):
        parser.error("When not using --list, you must provide url, --slug, and --name")
    
    try:
        if args.list:
            list_current_subscriptions()
        else:
            subscribe_by_video_url(
                args.url,
                args.slug,
                args.name,
                args.interval
            )
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
