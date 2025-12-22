"""Media adapters for normalizing platform-specific API responses."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.media import Media, VideoMedia, ImageMedia, TextMedia
from ..ontology.schema import MediaType


class MediaAdapter(ABC):
    """Abstract base class for platform media adapters."""

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> Media:
        """
        Normalize platform-specific data to standard Media format.

        Args:
            raw_data: Raw API response or data from platform

        Returns:
            Normalized Media object
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform name."""
        pass

    @abstractmethod
    def get_platform_slug(self) -> str:
        """Return platform slug."""
        pass


class YouTubeAdapter(MediaAdapter):
    """Adapter for YouTube API responses."""

    def normalize(self, raw_data: Dict[str, Any]) -> VideoMedia:
        """Normalize YouTube video data."""
        snippet = raw_data.get("snippet", {})
        content_details = raw_data.get("contentDetails", {})
        statistics = raw_data.get("statistics", {})

        # Parse duration (ISO 8601 format: PT1H2M10S)
        duration_seconds = self._parse_duration(content_details.get("duration", ""))

        # Extract aspect ratio from thumbnails
        thumbnails = snippet.get("thumbnails", {})
        default_thumb = thumbnails.get("default", {})
        aspect_ratio = self._calculate_aspect_ratio(
            default_thumb.get("width"), default_thumb.get("height")
        )

        return VideoMedia(
            title=snippet.get("title"),
            source_url=f"https://www.youtube.com/watch?v={raw_data.get('id', '')}",
            publish_date=self._parse_datetime(snippet.get("publishedAt")),
            thumbnail_url=thumbnails.get("high", {}).get("url") or thumbnails.get("default", {}).get("url"),
            media_type=MediaType.VIDEO,
            duration=duration_seconds,
            view_count=int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
            aspect_ratio=aspect_ratio,
            resolution=None,  # YouTube API doesn't provide this directly
            platform_name=self.get_platform_name(),
            platform_slug=self.get_platform_slug(),
            platform_icon_url="https://www.youtube.com/favicon.ico",
        )

    def get_platform_name(self) -> str:
        return "YouTube"

    def get_platform_slug(self) -> str:
        return "youtube"

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse ISO 8601 duration to seconds."""
        if not duration_str:
            return None
        import re
        pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
        match = re.match(pattern, duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return None

    def _calculate_aspect_ratio(self, width: Optional[int], height: Optional[int]) -> Optional[str]:
        """Calculate aspect ratio from dimensions."""
        if not width or not height:
            return None
        # Common ratios
        ratio = width / height
        if abs(ratio - 16/9) < 0.1:
            return "16:9"
        elif abs(ratio - 9/16) < 0.1:
            return "9:16"
        elif abs(ratio - 1) < 0.1:
            return "1:1"
        elif abs(ratio - 4/3) < 0.1:
            return "4:3"
        return f"{width}:{height}"

    def _parse_datetime(self, dt_str: Optional[str]) -> datetime:
        """Parse ISO 8601 datetime string."""
        if not dt_str:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()


class TikTokAdapter(MediaAdapter):
    """Adapter for TikTok API responses."""

    def normalize(self, raw_data: Dict[str, Any]) -> VideoMedia:
        """Normalize TikTok video data."""
        video = raw_data.get("video", {})
        stats = raw_data.get("stats", {})
        author = raw_data.get("author", {})

        return VideoMedia(
            title=raw_data.get("desc") or raw_data.get("title"),
            source_url=f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{raw_data.get('id', '')}",
            publish_date=self._parse_timestamp(raw_data.get("createTime", 0)),
            thumbnail_url=raw_data.get("video", {}).get("cover") or raw_data.get("thumbnail"),
            media_type=MediaType.VIDEO,
            duration=video.get("duration"),  # TikTok provides duration in milliseconds
            view_count=stats.get("playCount"),
            aspect_ratio="9:16",  # TikTok videos are typically vertical
            resolution=None,
            platform_name=self.get_platform_name(),
            platform_slug=self.get_platform_slug(),
            platform_icon_url="https://www.tiktok.com/favicon.ico",
        )

    def get_platform_name(self) -> str:
        return "TikTok"

    def get_platform_slug(self) -> str:
        return "tiktok"

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """Parse Unix timestamp to datetime."""
        try:
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return datetime.utcnow()


class InstagramAdapter(MediaAdapter):
    """Adapter for Instagram API responses."""

    def normalize(self, raw_data: Dict[str, Any]) -> Media:
        """Normalize Instagram post data."""
        media_type = raw_data.get("media_type", "IMAGE")
        is_video = media_type == "VIDEO"

        base_media = {
            "title": raw_data.get("caption", "")[:200] if raw_data.get("caption") else None,
            "source_url": raw_data.get("permalink") or f"https://www.instagram.com/p/{raw_data.get('id', '')}/",
            "publish_date": self._parse_timestamp(raw_data.get("timestamp", 0)),
            "thumbnail_url": raw_data.get("thumbnail_url") or raw_data.get("media_url"),
            "media_type": MediaType.VIDEO if is_video else MediaType.IMAGE,
            "platform_name": self.get_platform_name(),
            "platform_slug": self.get_platform_slug(),
            "platform_icon_url": "https://www.instagram.com/favicon.ico",
        }

        if is_video:
            return VideoMedia(
                **base_media,
                duration=None,  # Instagram API doesn't provide duration
                view_count=raw_data.get("like_count"),
                aspect_ratio=None,
                resolution=None,
            )
        else:
            # Try to extract dimensions from media_url or use defaults
            return ImageMedia(
                **base_media,
                width=None,
                height=None,
                aspect_ratio="1:1",  # Instagram posts are typically square
            )

    def get_platform_name(self) -> str:
        return "Instagram"

    def get_platform_slug(self) -> str:
        return "instagram"

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """Parse Unix timestamp to datetime."""
        try:
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return datetime.utcnow()


class RedditAdapter(MediaAdapter):
    """Adapter for Reddit API responses."""

    def normalize(self, raw_data: Dict[str, Any]) -> Media:
        """Normalize Reddit post data."""
        post_hint = raw_data.get("post_hint", "")
        is_video = post_hint == "hosted:video" or raw_data.get("is_video", False)
        is_image = post_hint == "image" or "i.redd.it" in raw_data.get("url", "")

        base_media = {
            "title": raw_data.get("title"),
            "source_url": f"https://www.reddit.com{raw_data.get('permalink', '')}",
            "publish_date": datetime.fromtimestamp(raw_data.get("created_utc", 0)),
            "thumbnail_url": raw_data.get("thumbnail") if raw_data.get("thumbnail") != "self" else None,
            "media_type": MediaType.VIDEO if is_video else (MediaType.IMAGE if is_image else MediaType.TEXT),
            "platform_name": self.get_platform_name(),
            "platform_slug": self.get_platform_slug(),
            "platform_icon_url": "https://www.reddit.com/favicon.ico",
        }

        if is_video:
            media = raw_data.get("media", {})
            reddit_video = media.get("reddit_video", {})
            return VideoMedia(
                **base_media,
                duration=reddit_video.get("duration"),
                view_count=None,  # Reddit doesn't provide view counts
                aspect_ratio=None,
                resolution=None,
            )
        elif is_image:
            return ImageMedia(
                **base_media,
                width=None,
                height=None,
                aspect_ratio=None,
            )
        else:
            return TextMedia(
                **base_media,
                body_content=raw_data.get("selftext", ""),
                word_count=len(raw_data.get("selftext", "").split()) if raw_data.get("selftext") else None,
            )

    def get_platform_name(self) -> str:
        return "Reddit"

    def get_platform_slug(self) -> str:
        return "reddit"


def get_adapter_for_platform(platform_slug: str) -> Optional[MediaAdapter]:
    """
    Get the appropriate adapter for a platform.

    Args:
        platform_slug: Platform slug (e.g., 'youtube', 'tiktok')

    Returns:
        MediaAdapter instance or None
    """
    adapters = {
        "youtube": YouTubeAdapter(),
        "tiktok": TikTokAdapter(),
        "instagram": InstagramAdapter(),
        "reddit": RedditAdapter(),
    }
    return adapters.get(platform_slug.lower())

