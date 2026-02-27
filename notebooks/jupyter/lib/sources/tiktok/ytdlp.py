"""yt-dlp configuration for TikTok archives."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TikTokPlatformConfig:
    platform: str = "tiktok"
    extra_flags: List[str] = field(default_factory=list)

    def build_flags(self) -> List[str]:
        # TikTok videos don't have chapters; skip chapter embedding
        return [
            "--embed-thumbnail",
            "--no-playlist",
        ] + self.extra_flags


DEFAULT_CONFIG = TikTokPlatformConfig()
