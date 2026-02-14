#!/usr/bin/env python3
"""CLI script to run imageboard archiver."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.archivers.orchestrator import ArchiverOrchestrator


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Imageboard archiver - continuously archive board content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive /b/ with thumbnails only (recommended for high-volume boards)
  python run_imageboard_archiver.py b --thumbs

  # Archive /b/ with full images (high storage usage)
  python run_imageboard_archiver.py b --thumbs --full

  # Archive other board with custom poll interval
  python run_imageboard_archiver.py pol --interval 60 --thumbs
        """
    )
    parser.add_argument(
        "board",
        help="Board name (e.g., 'b', 'pol', 'g')"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=45,
        help="Catalog poll interval in seconds (default: 45)"
    )
    parser.add_argument(
        "--thumbs",
        action="store_true",
        default=True,
        help="Download thumbnails (default: True)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Download full images (default: False, saves storage)"
    )
    parser.add_argument(
        "--media-workers",
        type=int,
        default=2,
        help="Number of media downloader workers (default: 2)"
    )
    parser.add_argument(
        "--ingestion-workers",
        type=int,
        default=2,
        help="Number of ingestion processor workers (default: 2)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("IMAGEBOARD ARCHIVER")
    print("=" * 70)
    print(f"Board: /{args.board}/")
    print(f"Poll interval: {args.interval} seconds")
    print(f"Download thumbnails: {args.thumbs}")
    print(f"Download full images: {args.full}")
    print(f"Media workers: {args.media_workers}")
    print(f"Ingestion workers: {args.ingestion_workers}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    orchestrator = ArchiverOrchestrator(
        board=args.board,
        poll_interval=args.interval,
        download_thumbs=args.thumbs,
        download_full=args.full,
        num_media_workers=args.media_workers,
        num_ingestion_workers=args.ingestion_workers,
    )
    
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        orchestrator.stop()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))



