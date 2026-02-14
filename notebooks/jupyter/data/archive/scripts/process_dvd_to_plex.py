#!/usr/bin/env python3
"""
DVD to Plex Processing Script

Main orchestration script for the three-module DVD processing pipeline:
1. Module 1 (Ripper): Extract titles from VIDEO_TS using MakeMKV or FFmpeg
2. Module 2 (Analyzer): Classify titles by duration
3. Module 3 (Organizer): Organize files for Plex library structure

Usage:
    python process_dvd_to_plex.py \
      --input /path/to/VIDEO_TS \
      --output /path/to/Plex/Movies \
      --movie-name "Movie Name" \
      --year 2006 \
      --min-length 120
"""

import sys
import argparse
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.dvd_processor import DVDProcessor
from src.dvd_classifier import TitleClassifier
from src.plex_organizer import PlexOrganizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def interactive_get_movie_info() -> tuple[str, Optional[int]]:
    """Interactively get movie name and year from user."""
    movie_name = input("Enter Movie Name (e.g., 'Ballerina'): ").strip()
    if not movie_name:
        raise ValueError("Movie name is required")
    
    year_str = input("Enter Release Year (optional, press Enter to skip): ").strip()
    year = None
    if year_str:
        try:
            year = int(year_str)
        except ValueError:
            logger.warning(f"Invalid year '{year_str}', ignoring")
    
    return movie_name, year


def interactive_classify_extras(
    extras: List,
    organizer: PlexOrganizer
) -> Dict[Path, Dict[str, str]]:
    """
    Interactively get names and Plex suffixes for extras.
    
    Returns:
        Dictionary mapping file paths to {name, suffix} configs
    """
    extra_configs = {}
    
    print("\n" + "=" * 70)
    print("CLASSIFYING EXTRAS")
    print("=" * 70)
    print("\nAvailable Plex extras suffixes:")
    for suffix in organizer.list_plex_suffixes():
        print(f"  -{suffix}")
    
    print("\nFor each extra, you can:")
    print("  - Press Enter to use suggested defaults")
    print("  - Enter a custom name and/or suffix")
    print("  - Format: 'Name' or 'Name:suffix'")
    print()
    
    for i, extra in enumerate(extras, 1):
        duration_min = extra.duration / 60
        suggested_name = extra.suggested_name or extra.file_path.stem
        suggested_suffix = extra.suggested_plex_suffix or "scene"
        
        print(f"\nExtra {i}/{len(extras)}: {extra.file_path.name}")
        print(f"  Duration: {duration_min:.1f} minutes")
        print(f"  Suggested: '{suggested_name}' with suffix '-{suggested_suffix}'")
        
        user_input = input("  Enter name[:suffix] (or press Enter for suggested): ").strip()
        
        if not user_input:
            # Use suggested
            extra_configs[extra.file_path] = {
                "name": suggested_name,
                "suffix": suggested_suffix
            }
        else:
            # Parse user input
            if ":" in user_input:
                name, suffix = user_input.split(":", 1)
                extra_configs[extra.file_path] = {
                    "name": name.strip(),
                    "suffix": suffix.strip()
                }
            else:
                extra_configs[extra.file_path] = {
                    "name": user_input,
                    "suffix": suggested_suffix
                }
    
    return extra_configs


def main():
    """Main processing workflow."""
    parser = argparse.ArgumentParser(
        description="Process DVD VIDEO_TS backup to Plex-compatible MKV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full command with all options
  python process_dvd_to_plex.py \\
    --input /home/jovyan/assets/inputs/remux/Ballerina.2006.PAL.DVDR-0MNiDVD/VIDEO_TS \\
    --output /home/jovyan/workspaces/outputs/plex/Movies \\
    --movie-name "Ballerina" \\
    --year 2006 \\
    --min-length 120

  # Interactive mode (will prompt for movie name/year)
  python process_dvd_to_plex.py \\
    --input /path/to/VIDEO_TS \\
    --output /path/to/Movies

Note: This script runs inside the Jupyter dev container.
      Input paths should use container paths: /home/jovyan/assets/...
      Output paths should be writable: /home/jovyan/workspaces/...
        """
    )
    
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to VIDEO_TS directory"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("/home/jovyan/assets/output/plex/Movies"),
        help="Base output directory for Plex library (default: /home/jovyan/assets/output/plex/Movies)"
    )
    
    parser.add_argument(
        "--movie-name",
        "-n",
        type=str,
        help="Movie name (if not provided, will prompt)"
    )
    
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        help="Release year (optional)"
    )
    
    parser.add_argument(
        "--min-length",
        type=int,
        default=120,
        help="Minimum title length in seconds (default: 120)"
    )
    
    parser.add_argument(
        "--staging-dir",
        type=Path,
        default=None,
        help="Staging directory for extracted files (default: temporary)"
    )
    
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive prompts (use defaults for extras)"
    )
    
    parser.add_argument(
        "--prefer-ffmpeg",
        action="store_true",
        help="Prefer FFmpeg over MakeMKV (MakeMKV is preferred by default)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    video_ts_path = Path(args.input)
    if not video_ts_path.exists():
        logger.error(f"VIDEO_TS directory not found: {video_ts_path}")
        sys.exit(1)
    
    if not video_ts_path.is_dir():
        logger.error(f"Input path must be a directory: {video_ts_path}")
        sys.exit(1)
    
    output_base = Path(args.output)
    
    # Get movie info
    movie_name = args.movie_name
    year = args.year
    
    if not movie_name:
        movie_name, year = interactive_get_movie_info()
    
    # Setup staging directory
    if args.staging_dir:
        staging_dir = Path(args.staging_dir)
    else:
        staging_dir = Path(f"/tmp/dvd_rip_{movie_name.replace(' ', '_')}")
    
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("DVD TO PLEX PROCESSING PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Input: {video_ts_path}")
    logger.info(f"Output: {output_base}")
    logger.info(f"Movie: {movie_name} ({year})" if year else f"Movie: {movie_name}")
    logger.info(f"Staging: {staging_dir}")
    logger.info("=" * 70)
    
    try:
        # Module 1: The Ripper
        logger.info("\n[MODULE 1] Extracting titles from DVD...")
        processor = DVDProcessor()
        
        if processor.makemkv_available:
            logger.info("Using MakeMKV (recommended)")
        elif processor.ffmpeg_available:
            logger.info("Using FFmpeg (MakeMKV not available)")
        else:
            logger.error("Neither MakeMKV nor FFmpeg available!")
            sys.exit(1)
        
        extracted_files = processor.extract_titles(
            video_ts_path=video_ts_path,
            output_dir=staging_dir,
            min_length_seconds=args.min_length,
            prefer_makemkv=not args.prefer_ffmpeg
        )
        
        if not extracted_files:
            logger.error("No titles extracted. Check minimum length setting.")
            sys.exit(1)
        
        logger.info(f"Extracted {len(extracted_files)} titles")
        
        # Module 2: The Analyzer
        logger.info("\n[MODULE 2] Analyzing and classifying titles...")
        classifier = TitleClassifier()
        metadata = classifier.analyze_durations(extracted_files)
        classifications = classifier.classify_by_duration(metadata)
        
        classifier.print_classification_summary(classifications)
        
        main_feature = classifier.get_main_feature(classifications)
        extras = classifier.get_extras(classifications)
        
        if not main_feature:
            logger.error("No main feature identified. Check classification thresholds.")
            sys.exit(1)
        
        logger.info(f"\nMain feature: {main_feature.file_path.name} ({main_feature.duration / 60:.1f} min)")
        logger.info(f"Extras: {len(extras)} files")
        
        # Confirm main feature
        if not args.no_interactive:
            confirm = input(f"\nConfirm main feature '{main_feature.file_path.name}'? [Y/n]: ").strip().lower()
            if confirm and confirm != "y":
                logger.info("Processing cancelled")
                sys.exit(0)
        
        # Module 3: The Organizer
        logger.info("\n[MODULE 3] Organizing files for Plex...")
        organizer = PlexOrganizer()
        
        # Get extra names/suffixes (interactive or defaults)
        extra_configs = {}
        if extras and not args.no_interactive:
            extra_configs = interactive_classify_extras(extras, organizer)
        else:
            # Use defaults
            for extra in extras:
                extra_configs[extra.file_path] = {
                    "name": extra.suggested_name or extra.file_path.stem,
                    "suffix": extra.suggested_plex_suffix or "scene"
                }
        
        # Organize all files
        result = organizer.organize_all(
            main_feature=main_feature,
            extras=extras,
            output_base=output_base,
            movie_name=movie_name,
            year=year,
            extra_names=extra_configs
        )
        
        # Cleanup staging directory
        logger.info(f"\nCleaning up staging directory: {staging_dir}")
        shutil.rmtree(staging_dir, ignore_errors=True)
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Main feature: {result['main_feature']}")
        logger.info(f"Extras: {len(result['extras'])} files")
        logger.info(f"Movie directory: {result['movie_dir']}")
        logger.info("\nFiles are ready for Plex library scanning!")
        logger.info("=" * 70)
        
    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nError during processing: {e}", exc_info=True)
        logger.info(f"Staging directory preserved: {staging_dir}")
        sys.exit(1)


if __name__ == "__main__":
    main()

