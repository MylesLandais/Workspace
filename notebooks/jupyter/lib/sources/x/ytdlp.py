"""yt-dlp configuration for X (Twitter) archives."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class XPlatformConfig:
    platform: str = "x"
    extra_flags: List[str] = field(default_factory=list)

    def build_flags(self) -> List[str]:
        return [
            "--embed-thumbnail",
            "--no-playlist",
        ] + self.extra_flags


DEFAULT_CONFIG = XPlatformConfig()
