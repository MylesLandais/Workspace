#!/usr/bin/env python3
"""
IMDB File Namer CLI

Command-line tool to discover video files, match them to IMDB entries,
and rename files/folders according to naming policy with IMDB tags.

Usage:
    python imdb_file_namer.py --directory /path/to/videos --dry-run
    python imdb_file_namer.py --file /path/to/video.mkv --yes
    python imdb_file_namer.py --directory /path/to/videos --rename-folders
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.file_renamer import FileRenamer, RenamingResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_results(results: List[RenamingResult], dry_run: bool = False):
    """
    Print summary of renaming results.
    
    Args:
        results: List of RenamingResult objects
        dry_run: Whether this was a dry run
    """
    if not results:
        print("No files processed.")
        return
    
    # Count by status
    status_counts = {}
    for result in results:
        status = result.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n{'='*60}")
    if dry_run:
        print("DRY RUN RESULTS")
    else:
        print("RENAMING RESULTS")
    print(f"{'='*60}")
    
    print(f"\nTotal processed: {len(results)}")
    print(f"  Success:  {status_counts.get('success', 0)}")
    print(f"  Skipped:  {status_counts.get('skipped', 0)}")
    print(f"  Errors:   {status_counts.get('error', 0)}")
    if dry_run:
        print(f"  (dry run): {status_counts.get('dry_run', 0)}")
    
    # Show errors if any
    errors = [r for r in results if r.status == 'error']
    if errors:
        print(f"\nErrors:")
        for result in errors:
            print(f"  {result.original_path.name}: {result.error}")
    
    # Show successful renames
    successes = [r for r in results if r.status in ('success', 'dry_run') and r.new_path]
    if successes:
        print(f"\n{'Renamed' if not dry_run else 'Would rename'} files:")
        for result in successes[:20]:  # Show first 20
            print(f"  {result.original_path.name}")
            print(f"    -> {result.new_path.name}")
            if result.imdb_match:
                print(f"    IMDB: {result.imdb_match.title} ({result.imdb_match.year}) [{result.imdb_match.imdb_id}]")
        
        if len(successes) > 20:
            print(f"  ... and {len(successes) - 20} more")
    
    print(f"{'='*60}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Discover video files, match to IMDB, and rename with IMDB tags",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run on a directory
  python imdb_file_namer.py --directory /path/to/videos --dry-run
  
  # Process with auto-confirm (no prompts)
  python imdb_file_namer.py --directory /path/to/videos --yes
  
  # Process single file
  python imdb_file_namer.py --file /path/to/video.mkv
  
  # Process and rename folders
  python imdb_file_namer.py --directory /path/to/videos --rename-folders --yes
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--directory', '-d',
        type=Path,
        help='Directory to process (searches recursively for video files)'
    )
    input_group.add_argument(
        '--file', '-f',
        type=Path,
        help='Single video file to process'
    )
    
    # Processing options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='Show what would be renamed without actually renaming (default: False)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        default=False,
        help='Auto-confirm all matches (non-interactive mode)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        default=False,
        help='Interactive mode: prompt for confirmation before renaming'
    )
    parser.add_argument(
        '--rename-folders',
        action='store_true',
        default=False,
        help='Also rename parent folders if they match movie name'
    )
    
    # Cache options
    parser.add_argument(
        '--cache-dir',
        type=Path,
        help='Directory for IMDB lookup cache (default: no cache)'
    )
    
    # Verbosity
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine interactive mode
    interactive = args.interactive and not args.yes
    
    # Initialize renamer
    try:
        renamer = FileRenamer(
            cache_dir=args.cache_dir,
            interactive=interactive
        )
    except ImportError as e:
        logger.error(f"Error importing required module: {e}")
        logger.error("Make sure cinemagoer is installed: pip install cinemagoer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error initializing renamer: {e}", exc_info=True)
        sys.exit(1)
    
    # Process files
    results = []
    try:
        if args.file:
            # Process single file
            logger.info(f"Processing single file: {args.file}")
            
            result = renamer.process_single_file(
                args.file,
                dry_run=args.dry_run,
                auto_confirm=args.yes
            )
            
            if result:
                results = [result]
                print_results(results, dry_run=args.dry_run)
            else:
                logger.error(f"File not found or not a video file: {args.file}")
                sys.exit(1)
        
        elif args.directory:
            # Process directory
            logger.info(f"Processing directory: {args.directory}")
            
            if not args.directory.exists():
                logger.error(f"Directory does not exist: {args.directory}")
                sys.exit(1)
            
            if not args.directory.is_dir():
                logger.error(f"Path is not a directory: {args.directory}")
                sys.exit(1)
            
            results = renamer.process_directory(
                args.directory,
                dry_run=args.dry_run,
                rename_folders=args.rename_folders,
                auto_confirm=args.yes
            )
            
            print_results(results, dry_run=args.dry_run)
        
        # Exit with error code if there were errors
        # (but allow dry-run to succeed even if matches fail)
        if args.dry_run:
            sys.exit(0)
        
        errors = [r for r in results if r.status == 'error']
        if errors:
            logger.warning(f"Completed with {len(errors)} error(s)")
            sys.exit(1)
        else:
            logger.info("Completed successfully")
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

