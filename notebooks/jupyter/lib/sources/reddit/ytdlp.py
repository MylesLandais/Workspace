"""yt-dlp configuration for Reddit video archives."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RedditPlatformConfig:
    platform: str = "reddit"
    extra_flags: List[str] = field(default_factory=list)

    def build_flags(self) -> List[str]:
        return [
            "--no-playlist",
            "--embed-thumbnail",
        ] + self.extra_flags


DEFAULT_CONFIG = RedditPlatformConfig()
