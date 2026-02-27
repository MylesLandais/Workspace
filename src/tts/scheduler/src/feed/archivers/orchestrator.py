"""Orchestrator for imageboard archiver services - runs all components together."""

import asyncio
import signal
from typing import Optional
import argparse

from .catalog_poller import CatalogPoller
from .media_downloader import MediaDownloader
from .ingestion_processor import IngestionProcessor


class ArchiverOrchestrator:
    """
    Orchestrates all archiver services:
    - Catalog poller (monitors board)
    - Media downloader (downloads media to MinIO)
    - Ingestion processor (stores in Neo4j)
    """

    def __init__(
        self,
        board: str,
        poll_interval: int = 45,
        download_thumbs: bool = True,
        download_full: bool = False,
        num_media_workers: int = 2,
        num_ingestion_workers: int = 2,
    ):
        """
        Initialize orchestrator.
        
        Args:
            board: Board name (e.g., "b")
            poll_interval: Catalog poll interval in seconds
            download_thumbs: Download thumbnails
            download_full: Download full images
            num_media_workers: Number of media downloader workers
            num_ingestion_workers: Number of ingestion processor workers
        """
        self.board = board
        self.running = False
        
        # Initialize services
        self.poller = CatalogPoller(board=board, poll_interval=poll_interval)
        self.downloader = MediaDownloader(
            board=board,
            download_thumbs=download_thumbs,
            download_full=download_full,
        )
        self.processor = IngestionProcessor(board=board)
        
        self.num_media_workers = num_media_workers
        self.num_ingestion_workers = num_ingestion_workers
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutdown signal received. Stopping all services...")
        self.stop()

    async def run(self):
        """Run all archiver services concurrently."""
        self.running = True
        
        print("=" * 70)
        print(f"IMAGEBOARD ARCHIVER ORCHESTRATOR - /{self.board}/")
        print("=" * 70)
        print("Starting services:")
        print(f"  - Catalog Poller (interval: {self.poller.poll_interval}s)")
        print(f"  - Media Downloader (thumbs: {self.downloader.download_thumbs}, full: {self.downloader.download_full})")
        print(f"  - Ingestion Processor")
        print()
        
        # Start all services as concurrent tasks
        tasks = [
            asyncio.create_task(self.poller.run()),
            asyncio.create_task(self.downloader.run(num_workers=self.num_media_workers)),
            asyncio.create_task(self.processor.run(num_workers=self.num_ingestion_workers)),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("Tasks cancelled")
        except Exception as e:
            print(f"Error in orchestrator: {e}")
            import traceback
            traceback.print_exc()

    def stop(self):
        """Stop all services."""
        self.running = False
        self.poller.stop()
        self.downloader.stop()
        self.processor.stop()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="imageboard archiver orchestrator - runs all archiver services"
    )
    parser.add_argument("board", help="Board name (e.g., 'b')")
    parser.add_argument("--interval", type=int, default=45, help="Catalog poll interval (seconds)")
    parser.add_argument("--thumbs", action="store_true", default=True, help="Download thumbnails")
    parser.add_argument("--full", action="store_true", help="Download full images")
    parser.add_argument("--media-workers", type=int, default=2, help="Media downloader workers")
    parser.add_argument("--ingestion-workers", type=int, default=2, help="Ingestion processor workers")
    
    args = parser.parse_args()
    
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
        orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())




