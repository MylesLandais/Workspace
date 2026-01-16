#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.services.youtube_subscription_service import YouTubeSubscriptionService


def extract_channel_from_video_url(video_url: str) -> dict | None:
    """Extract channel information from a YouTube video URL using yt-dlp."""
    print(f"Extracting channel info from: {video_url}")
    
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            "--quiet",
            video_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Extract channel information
        uploader = data.get("uploader", "")
        uploader_id = data.get("uploader_id", "")
        channel_url = data.get("channel", "")
        channel_follower_count = data.get("channel_follower_count")
        channel_is_verified = data.get("channel_is_verified", False)
        
        # Build handle from uploader ID
        if uploader_id:
            handle = f"@{uploader_id}"
        else:
            handle = None
        
        # Build profile URL from channel URL
        if not channel_url and handle:
            channel_url = f"https://www.youtube.com/{handle}"
        elif not channel_url:
            channel_url = video_url  # Fallback to video URL
        
        return {
            "uploader": uploader,
            "uploader_id": uploader_id,
            "handle": handle,
            "channel_url": channel_url,
            "follower_count": channel_follower_count,
            "verified": channel_is_verified
        }
    except subprocess.CalledProcessError as e:
        print(f"Error extracting channel info: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def subscribe_to_channel(
    video_url: str,
    poll_interval_hours: int = 24
):
    """Subscribe to the channel from a YouTube video URL."""
    
    # Extract channel info
    channel_info = extract_channel_from_video_url(video_url)
    
    if not channel_info or not channel_info.get("handle"):
        print("Failed to extract channel information")
        return False
    
    handle = channel_info["handle"]
    display_name = channel_info.get("uploader", handle)
    profile_url = channel_info.get("channel_url", video_url)
    follower_count = channel_info.get("follower_count")
    verified = channel_info.get("verified", False)
    
    print(f"\nChannel Information:")
    print(f"  Handle: {handle}")
    print(f"  Display Name: {display_name}")
    print(f"  Profile URL: {profile_url}")
    print(f"  Followers: {follower_count}")
    print(f"  Verified: {verified}")
    print()
    
    # Create creator slug from handle
    creator_slug = handle.replace("@", "").lower().replace(".", "_")
    
    # Initialize subscription service
    print("Initializing YouTube subscription service...")
    service = YouTubeSubscriptionService()
    
    # Ensure creator exists
    print(f"Creating/updating creator: {creator_slug}")
    service.create_creator(
        name=display_name,
        slug=creator_slug,
        bio=f"YouTube channel with {follower_count} followers" if follower_count else "YouTube channel",
        avatar_url=None
    )
    
    # Add YouTube handle
    print(f"Adding YouTube handle for: {handle}")
    success = service.add_youtube_handle(
        creator_slug=creator_slug,
        handle=handle,
        display_name=display_name,
        profile_url=profile_url,
        follower_count=follower_count,
        verified=verified
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
    
    # Invalidate cache
    print("Invalidating cache...")
    service.invalidate_creator_cache(creator_slug)
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Subscribed to YouTube channel: {handle}")
    print(f"Creator slug: {creator_slug}")
    print(f"Poll interval: {poll_interval_hours} hours")
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


def check_subscription_health():
    """Check health of all YouTube subscriptions."""
    print("YouTube subscription health:")
    print("-" * 60)
    
    service = YouTubeSubscriptionService()
    health_data = service.get_subscription_health()
    
    if not health_data:
        print("No subscriptions found.")
        return
    
    healthy_count = sum(1 for h in health_data if h.get("status") == "healthy")
    warning_count = sum(1 for h in health_data if h.get("status") == "warning")
    unhealthy_count = sum(1 for h in health_data if h.get("status") == "unhealthy")
    
    print(f"Total: {len(health_data)}")
    print(f"Healthy: {healthy_count}")
    print(f"Warning: {warning_count}")
    print(f"Unhealthy: {unhealthy_count}")
    print()
    
    for health in health_data:
        status_emoji = {
            "healthy": "✓",
            "warning": "⚠",
            "unhealthy": "✗"
        }.get(health.get("status"), "?")
        
        print(f"{status_emoji} {health['youtube_handle']} ({health['creator_name']})")
        print(f"   Status: {health['status']}")
        print(f"   Last successful poll: {health.get('last_successful_poll', 'N/A')}")
        print(f"   Last polled: {health.get('last_polled_at', 'N/A')}")
        print(f"   Poll count (24h): {health.get('poll_count_24h', 0)}")
        print(f"   Error count (24h): {health.get('error_count_24h', 0)}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YouTube channel subscription manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Subscribe to channel from a video URL
  python subscribe_youtube_channel.py https://youtu.be/zPg4-YoGnF0

  # Subscribe with custom poll interval
  python subscribe_youtube_channel.py https://youtu.be/zPg4-YoGnF0 --interval 12

  # List all subscriptions
  python subscribe_youtube_channel.py --list

  # Check subscription health
  python subscribe_youtube_channel.py --health
        """
    )
    
    parser.add_argument("url", nargs="?", help="YouTube video URL to subscribe to channel")
    parser.add_argument("--interval", type=int, default=24, help="Poll interval in hours (default: 24)")
    parser.add_argument("--list", action="store_true", help="List all current subscriptions")
    parser.add_argument("--health", action="store_true", help="Check subscription health")
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_current_subscriptions()
        elif args.health:
            check_subscription_health()
        elif args.url:
            subscribe_to_channel(args.url, args.interval)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
