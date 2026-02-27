# ADR-003: Platform yt-dlp configs live in lib/sources/{platform}/

## Status

Accepted

## Context

FeedVault needs per-platform yt-dlp flag sets (YouTube embeds chapters, TikTok skips
them, Reddit needs `--no-playlist`, etc.). The initial design placed these under
`src/feedvault/platforms/`. However, `lib/sources/` already contains platform adapters
(reddit, youtube, tumblr, imageboard) following the `PlatformAdapter` ABC.

Splitting platform knowledge across `lib/sources/` and `src/feedvault/platforms/` would
create two places to update when adding or changing a platform.

## Decision

Place yt-dlp platform configs in `lib/sources/{platform}/ytdlp.py` alongside existing
platform adapters. Each file exposes a `DEFAULT_CONFIG` dataclass with a `build_flags()`
method.

The runner discovers configs by importing `lib.sources.{platform}.ytdlp.DEFAULT_CONFIG`
by name, which is a lightweight form of the registry pattern. A formal self-registering
registry (`lib/sources/registry.py`) is the natural next step if the number of platforms
grows.

## Consequences

- Single location for all platform-specific knowledge.
- Adding a new platform means adding one directory under `lib/sources/` — no central
  manifest to update (once the registry pattern is formalised).
- `src/feedvault/` contains only orchestration logic (archiver, runner); it imports from
  `lib/sources/` but adds no platform-specific code.
