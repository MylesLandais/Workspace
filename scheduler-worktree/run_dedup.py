#!/usr/bin/env python3
"""Run deduplication and CLIP embeddings on existing dataset."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.image_dedup.batch_process import BatchProcessor

def main():
    """Run batch processing with CLIP enabled."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run image deduplication on existing data")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of posts to process")
    parser.add_argument("--offset", type=int, default=0, help="Starting offset")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--no-clip", action="store_true", help="Disable CLIP embeddings")
    parser.add_argument("--storage-path", type=str, default=None, 
                       help="Storage path (default: from env or /tmp)")
    
    args = parser.parse_args()
    
    storage_path = args.storage_path or os.getenv(
        "IMAGE_DEDUP_STORAGE_PATH", "/tmp/image_dedup_storage"
    )
    
    print("=" * 80)
    print("IMAGE DEDUPLICATION AND CLIP EMBEDDING")
    print("=" * 80)
    print(f"Storage path: {storage_path}")
    print(f"CLIP enabled: {not args.no_clip}")
    print(f"Batch size: {args.batch_size}")
    if args.limit:
        print(f"Processing limit: {args.limit} posts")
    print("=" * 80)
    print()
    
    try:
        processor = BatchProcessor(
            storage_path=storage_path,
            enable_clip=not args.no_clip,
            batch_size=args.batch_size,
        )
        
        stats = processor.process_all(limit=args.limit, start_from=args.offset)
        
        print()
        print("=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"Processed: {stats['processed']:,}")
        print(f"Successful: {stats['successful']:,}")
        print(f"New images: {stats['new']:,}")
        print(f"Duplicates detected: {stats['duplicates']:,}")
        print(f"Errors: {stats['errors']:,}")
        print(f"Skipped: {stats['skipped']:,}")
        
        if stats['successful'] > 0:
            duplicate_rate = (stats['duplicates'] / stats['successful']) * 100
            print(f"Duplicate rate: {duplicate_rate:.2f}%")
        
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()







