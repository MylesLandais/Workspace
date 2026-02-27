"""YtdlpArchiver — wraps yt-dlp subprocess and uploads results to SeaweedFS."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Protocol

from filelock import FileLock

logger = logging.getLogger(__name__)


class PlatformConfig(Protocol):
    platform: str

    def build_flags(self) -> List[str]: ...


@dataclass
class FeedEntry:
    name: str
    url: str
    platform: str


@dataclass
class ArchiveResult:
    entry: FeedEntry
    files_downloaded: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


# Shared yt-dlp flags applied to every platform
_BASE_FLAGS = [
    "-f", "bestvideo+bestaudio/best",
    "--merge-output-format", "mkv",
    "--embed-metadata",
    "--embed-chapters",
    "--embed-thumbnail",
    "--embed-subs",
    "--write-info-json",
    "--write-description",
    "--no-overwrites",
    "--ignore-errors",
    "--continue",
]


class YtdlpArchiver:
    """Archive a feed entry using yt-dlp and upload results to SeaweedFS.

    Args:
        s3_store: An S3Store instance pointing at the 'yt-archives' bucket.
        state_dir: Root directory for per-platform/per-feed download-archive files.
        temp_dir: Scratch directory for yt-dlp output (cleared after each upload).
    """

    def __init__(self, s3_store, state_dir: Path, temp_dir: Path):
        self._s3 = s3_store
        self._state_dir = state_dir
        self._temp_dir = temp_dir

    def archive(self, entry: FeedEntry, platform_config: PlatformConfig) -> ArchiveResult:
        """Run yt-dlp for *entry* and upload the results to SeaweedFS.

        Returns an ArchiveResult describing what happened.
        """
        state_file = self._state_dir / entry.platform / f"{entry.name}.txt"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        run_dir = Path(tempfile.mkdtemp(dir=self._temp_dir, prefix=f"{entry.name}_"))
        lock_path = state_file.with_suffix(".txt.lock")

        with FileLock(str(lock_path)):
            try:
                return self._run(entry, platform_config, state_file, run_dir)
            finally:
                shutil.rmtree(run_dir, ignore_errors=True)

    def _run(
        self,
        entry: FeedEntry,
        platform_config: PlatformConfig,
        state_file: Path,
        run_dir: Path,
    ) -> ArchiveResult:
        output_tmpl = str(run_dir / "%(upload_date>%Y-%m-%d)s_%(id)s_%(title).150B.%(ext)s")

        cmd = [
            "yt-dlp",
            *_BASE_FLAGS,
            *platform_config.build_flags(),
            "--download-archive", str(state_file),
            "-o", output_tmpl,
            entry.url,
        ]

        logger.info("archiving %s/%s: %s", entry.platform, entry.name, entry.url)
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode not in (0, 1):
            # yt-dlp exits 1 for partial failures; anything else is a hard error
            error_msg = result.stderr[-2000:] if result.stderr else "unknown error"
            logger.error("yt-dlp failed for %s: %s", entry.name, error_msg)
            return ArchiveResult(entry=entry, error=error_msg)

        uploaded: List[str] = []
        for local_file in run_dir.iterdir():
            if not local_file.is_file():
                continue
            key = f"yt-archives/{entry.platform}/{entry.name}/{local_file.name}"
            try:
                self._s3.upload_file(str(local_file), key, bucket="yt-archives")
                uploaded.append(key)
                logger.debug("uploaded %s", key)
            except Exception as exc:
                logger.error("upload failed for %s: %s", local_file.name, exc)

        return ArchiveResult(entry=entry, files_downloaded=uploaded)
