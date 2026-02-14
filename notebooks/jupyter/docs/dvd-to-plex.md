# DVD to Plex Processing Guide

## Overview

This guide explains how to use the DVD to Plex processing pipeline to convert raw PAL DVD backups (VIDEO_TS structure) into Plex-compatible MKV files with proper naming and organization.

## Architecture

The pipeline uses a modular three-stage architecture:

1. **Module 1: The Ripper** (`src/dvd_processor.py`)
   - Extracts all titles from DVD VIDEO_TS structure
   - Uses MakeMKV (preferred) or FFmpeg (fallback)
   - Preserves quality with stream copy (no re-encoding)

2. **Module 2: The Analyzer** (`src/dvd_classifier.py`)
   - Analyzes extracted titles by duration
   - Classifies main feature vs extras using heuristics
   - Suggests Plex naming conventions

3. **Module 3: The Organizer** (`src/plex_organizer.py`)
   - Organizes files into Plex library structure
   - Applies Plex naming conventions for automatic extras detection
   - Creates proper directory hierarchy

## Dependencies

### System Packages (Container)

**Required:**
- **FFmpeg** - Already installed in Dockerfile
  - Used for video analysis and as fallback extraction method
  - Includes `ffmpeg` and `ffprobe`

**Optional (Recommended):**
- **MakeMKV** (`makemkvcon`) - Better DVD handling
  - Proprietary/unfree software
  - Provides cleaner title extraction
  - **Note**: Not currently in Dockerfile due to licensing

### Python Packages

All Python dependencies are standard library or already in `requirements.txt`:
- `subprocess` (standard library)
- `pathlib` (standard library)
- `dataclasses` (standard library)
- `logging` (standard library)

### Installing MakeMKV (Optional)

MakeMKV is recommended but not required. The pipeline gracefully falls back to FFmpeg if MakeMKV is unavailable.

**In Container (Manual Install):**
```bash
# Inside container
docker compose exec jupyterlab bash

# Download and install MakeMKV (example - adjust for your architecture)
# Note: MakeMKV requires a license key (free beta keys available)
wget https://www.makemkv.com/download/makemkv-bin-*.tar.gz
wget https://www.makemkv.com/download/makemkv-oss-*.tar.gz
# Follow MakeMKV installation instructions
```

**Or install on host and use host path:**
- Install MakeMKV on NixOS host
- Mount executable or use host PATH in container

**NixOS Host Setup (for reference):**
```nix
# In configuration.nix
{
  nixpkgs.config.allowUnfree = true;
  environment.systemPackages = with pkgs; [ makemkv ];
  boot.kernelModules = [ "sg" ];  # For optical drives
  users.users.youruser.extraGroups = [ "cdrom" ];
}
```

## Usage

### Basic Usage

```bash
# Inside container
docker compose exec jupyterlab bash
cd /home/jovyan/workspaces

python process_dvd_to_plex.py \
  --input /home/jovyan/assets/inputs/remux/Ballerina.2006.PAL.DVDR-0MNiDVD/VIDEO_TS \
  --output /home/jovyan/assets/outputs/plex/Movies \
  --movie-name "Ballerina" \
  --year 2006 \
  --min-length 120
```

### Interactive Mode

If you omit `--movie-name` and `--year`, the script will prompt:

```bash
python process_dvd_to_plex.py \
  --input /home/jovyan/assets/inputs/remux/DVD_NAME/VIDEO_TS \
  --output /home/jovyan/workspaces/outputs/plex/Movies
```

### Command Line Options

- `--input`, `-i`: Path to VIDEO_TS directory (required)
- `--output`, `-o`: Base output directory for Plex library (required)
- `--movie-name`, `-n`: Movie name (optional, will prompt if not provided)
- `--year`, `-y`: Release year (optional)
- `--min-length`: Minimum title length in seconds (default: 120)
- `--staging-dir`: Custom staging directory (default: temporary)
- `--no-interactive`: Skip interactive prompts (use defaults)
- `--prefer-ffmpeg`: Use FFmpeg instead of MakeMKV if both available

## Path Reference

### Container Paths

- **Workspace**: `/home/jovyan/workspaces` (mounted from host workspace directory)
- **Assets (input)**: `/home/jovyan/assets` (read-only mount from `~/assets`)
- **Output (persistent)**: `/home/jovyan/assets/outputs/` (writable, maps to `~/assets/outputs/` on host)

### Example Paths

```
Input (VIDEO_TS):
  /home/jovyan/assets/inputs/remux/Ballerina.2006.PAL.DVDR-0MNiDVD/VIDEO_TS
  (Host: ~/assets/inputs/remux/...)

Output (Plex structure):
  /home/jovyan/assets/outputs/plex/Movies/Ballerina (2006)/
    Ballerina (2006).mkv                    # Main feature
    Ballerina (2006) - Trailer-trailer.mkv  # Extra
  (Host: ~/assets/outputs/plex/Movies/...)
```

## Plex Naming Conventions

The pipeline uses Plex's standard extras naming format:

**Main Feature:**
- `Movie Name (Year).mkv`

**Extras:**
- `Movie Name (Year) - Extra Name-suffix.mkv`

### Available Extras Suffixes

- `-trailer`: Movie trailers
- `-behindthescenes`: Behind the scenes content
- `-featurette`: Featurettes, making-of documentaries
- `-deleted`: Deleted scenes
- `-interview`: Cast/crew interviews
- `-short`: Short films
- `-scene`: Generic scene-specific extras (default fallback)

## Classification Rules

The analyzer uses duration-based heuristics:

- **Main Feature**: Longest title (typically >80 minutes)
- **Long Extras**: 10-60 minutes (featurettes, making-of)
- **Short Extras**: 2-10 minutes (trailers, interviews)
- **Junk**: <2 minutes (filtered by `--min-length`)

You can customize these thresholds in `src/dvd_classifier.py`.

## Workflow

1. **Extraction**: All titles extracted to staging directory
2. **Analysis**: Durations analyzed, titles classified
3. **Review**: Interactive prompts for confirmation and extras naming
4. **Organization**: Files moved to final Plex structure
5. **Cleanup**: Staging directory removed

## Troubleshooting

### MakeMKV Not Available

The pipeline automatically falls back to FFmpeg. You'll see:
```
Using FFmpeg (MakeMKV not available)
```

**Note**: FFmpeg fallback may not handle all DVD structures perfectly. For best results, install MakeMKV.

### FFmpeg Not Found

Ensure FFmpeg is installed in container:
```bash
docker compose exec jupyterlab ffmpeg -version
```

If missing, rebuild container or install manually in container.

### Permission Errors

Ensure output directory is writable:
```bash
# Inside container
mkdir -p /home/jovyan/workspaces/outputs/plex
chown -R jovyan:jovyan /home/jovyan/workspaces/outputs
```

### No Titles Extracted

- Check `--min-length` setting (may be filtering valid titles)
- Verify VIDEO_TS directory structure is correct
- Check logs for MakeMKV/FFmpeg errors

## Integration with Existing Remux System

This DVD processor integrates with the existing remux pipeline:

- Uses `VideoRemuxer.get_video_info()` for duration analysis
- Follows same quality preservation patterns (`-c copy`)
- Uses consistent logging format
- Compatible with existing subtitle processing if needed

## Output Structure

```
Movies/
  Movie Name (Year)/
    Movie Name (Year).mkv                           # Main feature
    Movie Name (Year) - Trailer-trailer.mkv
    Movie Name (Year) - Making Of-featurette.mkv
    Movie Name (Year) - Behind The Scenes-behindthescenes.mkv
```

Files are ready for Plex library scanning after processing completes.

