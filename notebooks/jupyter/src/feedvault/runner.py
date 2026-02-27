"""FeedVault runner — reads feed config files and orchestrates archival."""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from lib.storage.s3 import S3Store
from .archiver import ArchiveResult, FeedEntry, YtdlpArchiver

logger = logging.getLogger(__name__)

# Map platform name -> module path for DEFAULT_CONFIG
_PLATFORM_CONFIG_MODULES: Dict[str, str] = {
    "youtube": "lib.sources.youtube.ytdlp",
    "tiktok": "lib.sources.tiktok.ytdlp",
    "reddit": "lib.sources.reddit.ytdlp",
    "instagram": "lib.sources.instagram.ytdlp",
    "x": "lib.sources.x.ytdlp",
}


@dataclass
class RunReport:
    successes: List[ArchiveResult] = field(default_factory=list)
    failures: List[ArchiveResult] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)


def _load_platform_config(platform: str):
    import importlib
    module_path = _PLATFORM_CONFIG_MODULES.get(platform)
    if module_path is None:
        raise ValueError(f"unsupported platform: {platform}")
    module = importlib.import_module(module_path)
    return module.DEFAULT_CONFIG


def _parse_feed_file(path: Path, platform: str) -> List[FeedEntry]:
    """Parse a feeds config file.

    Each non-empty, non-comment line has the form:
        name https://url
    """
    entries: List[FeedEntry] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            logger.warning("skipping malformed line in %s: %r", path.name, line)
            continue
        entries.append(FeedEntry(name=parts[0], url=parts[1], platform=platform))
    return entries


def _update_ytdlp() -> None:
    logger.info("updating yt-dlp")
    result = subprocess.run(["yt-dlp", "-U"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("yt-dlp update failed: %s", result.stderr[:500])


def run_all(config_dir: Path, state_dir: Path, temp_dir: Path) -> RunReport:
    """Read all feed config files and archive each entry.

    Args:
        config_dir: Directory containing *.txt feed lists (e.g. config/feeds/).
        state_dir:  Root directory for per-platform yt-dlp download-archive files.
        temp_dir:   Scratch directory for yt-dlp output.

    Returns:
        A RunReport summarising the run.
    """
    _update_ytdlp()

    s3 = S3Store(bucket="yt-archives")
    archiver = YtdlpArchiver(s3_store=s3, state_dir=state_dir, temp_dir=temp_dir)
    report = RunReport()

    for feed_file in sorted(config_dir.glob("*.txt")):
        platform = feed_file.stem
        try:
            platform_config = _load_platform_config(platform)
        except ValueError as exc:
            logger.warning("skipping %s: %s", feed_file.name, exc)
            report.skipped.append(feed_file.name)
            continue

        entries = _parse_feed_file(feed_file, platform)
        if not entries:
            logger.info("no entries in %s", feed_file.name)
            continue

        for entry in entries:
            result = archiver.archive(entry, platform_config)
            if result.success:
                report.successes.append(result)
                logger.info(
                    "archived %s/%s: %d file(s)",
                    entry.platform,
                    entry.name,
                    len(result.files_downloaded),
                )
            else:
                report.failures.append(result)
                logger.error("failed %s/%s: %s", entry.platform, entry.name, result.error)

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    base = Path(__file__).parent.parent.parent  # notebooks/jupyter/
    report = run_all(
        config_dir=base / "config" / "feeds",
        state_dir=base / "data" / "state",
        temp_dir=base / "data" / "tmp",
    )

    total = len(report.successes) + len(report.failures)
    print(f"done: {len(report.successes)}/{total} succeeded, {len(report.failures)} failed")
    if report.failures:
        sys.exit(1)
