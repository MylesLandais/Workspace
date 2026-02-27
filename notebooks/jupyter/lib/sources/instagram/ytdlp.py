"""yt-dlp configuration for Instagram archives."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class InstagramPlatformConfig:
    platform: str = "instagram"
    extra_flags: List[str] = field(default_factory=list)

    def build_flags(self) -> List[str]:
        return [
            "--embed-thumbnail",
            "--no-playlist",
        ] + self.extra_flags


DEFAULT_CONFIG = InstagramPlatformConfig()
