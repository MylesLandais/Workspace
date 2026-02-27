"""yt-dlp configuration for YouTube archives."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class YouTubePlatformConfig:
    platform: str = "youtube"
    extra_flags: List[str] = field(default_factory=list)

    def build_flags(self) -> List[str]:
        return [
            "--embed-chapters",
            "--embed-thumbnail",
            "--embed-subs",
            "--all-subs",
        ] + self.extra_flags


DEFAULT_CONFIG = YouTubePlatformConfig()
