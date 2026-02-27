#!/usr/bin/env python3
"""
WMV File Processing Script

This script processes .wmv files by:
1. Extracting audio for potential ASR processing
2. Converting video to .mkv format
3. Optionally embedding subtitles if available

Designed to work with private datasets and handle cases where ASR validation fails.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.video_remuxer import VideoRemuxer, RemuxJob
from src.subtitle_processor import SubtitleProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wmv_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WMVProcessor:
    """Processes .wmv files with audio extraction and video remuxing."""
    
    def __init__(self):
        """Initialize the WMV processor."""
        self.video_remuxer = VideoRemuxer()
        self.subtitle_processor = SubtitleProcessor()
        
    def discover_wmv_files(self, dataset_dir: Path) -> List[Path]:
        """
        Discover .wmv files in a dataset directory.
        
        Args:
            dataset_dir: Directory to search
            
        Returns:
            List of .wmv file paths
        """
        wmv_files = []
        
        # Search for .wmv files (case insensitive)
        for pattern in ["*.wmv", "*.WMV"]:
            wmv_files.extend(dataset_dir.rglob(pattern))
        
        logger.info(f"Found {len(wmv_files)} .wmv files in {dataset_dir}")
        return wmv_files
    
    def create_output_structure(self, dataset_dir: Path) -> Dict[str, Path]:
        """
        Create output directory structure.
        
        Args:
            dataset_dir: Base dataset directory
            
        Returns:
            Dictionary of output directories
        """
        structure = {
            'remux': dataset_dir / 'outputs' / 'remux',
            'audio': dataset_dir / 'outputs' / 'audio',
            'subtitles': dataset_dir / 'outputs' / 'subtitles',
            'metadata': dataset_dir / 'outputs' / 'metadata'
        }
        
        # Create directories
        for dir_path in structure.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")
        
        return structure
    
    def process_single_wmv(self, wmv_file: Path, output_dirs: Dict[str, Path],
                          extract_audio: bool = True, 
                          preserve_quality: bool = True) -> Dict[str, Any]:
        """
        Process a single .wmv file.
        
        Args:
            wmv_file: Input .wmv file
            output_dirs: Output directory structure
            extract_audio: Whether to extract audio
            preserve_quality: Whether to preserve video quality
            
        Returns:
            Processing result dictionary
        """
        logger.info(f"Processing: {wmv_file.name}")
        
        start_time = time.time()
        result = {
            'input_file': str(wmv_file),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'processing'
        }
        
        try:
            # Get video information
            video_info = self.video_remuxer.get_video_info(wmv_file)
            result['video_info'] = {
                'duration': video_info.duration,
                'width': video_info.width,
                'height': video_info.height,
                'fps': video_info.fps,
                'video_codec': video_info.video_codec,
                'audio_codec': video_info.audio_codec,
                'file_size': video_info.file_size,
                'format_name': video_info.format_name
            }
            
            logger.info(f"  Video info: {video_info.width}x{video_info.height}, "
                       f"{video_info.duration:.1f}s, {video_info.video_codec}")
            
            # Extract audio if requested
            audio_file = None
            if extract_audio:
                audio_file = output_dirs['audio'] / f"{wmv_file.stem}.wav"
                try:
                    extracted_audio = self.video_remuxer.extract_audio(wmv_file, audio_file)
                    result['audio_file'] = str(extracted_audio)
                    logger.info(f"  Audio extracted: {extracted_audio.name}")
                except Exception as e:
                    logger.warning(f"  Audio extraction failed: {e}")
                    result['audio_extraction_error'] = str(e)
            
            # Remux video to .mkv
            output_video = output_dirs['remux'] / f"{wmv_file.stem}.mkv"
            
            try:
                remuxed_video = self.video_remuxer.remux_without_subtitles(
                    wmv_file, 
                    output_video, 
                    preserve_quality=preserve_quality
                )
                result['output_video'] = str(remuxed_video)
                logger.info(f"  Video remuxed: {remuxed_video.name}")
                
                # Get output file size for comparison
                output_size = remuxed_video.stat().st_size
                result['output_size'] = output_size
                result['size_ratio'] = output_size / video_info.file_size
                
            except Exception as e:
                logger.error(f"  Video remuxing failed: {e}")
                result['remux_error'] = str(e)
                result['status'] = 'error'
                return result
            
            # Save metadata
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            result['status'] = 'success'
            
            metadata_file = output_dirs['metadata'] / f"{wmv_file.stem}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            result['metadata_file'] = str(metadata_file)
            
            logger.info(f"  ✅ Completed in {processing_time:.2f}s")
            
        except Exception as e:
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"  ❌ Failed: {e}")
        
        return result
    
    def process_dataset(self, dataset_path: Path, extract_audio: bool = True,
                       preserve_quality: bool = True) -> Dict[str, Any]:
        """
        Process all .wmv files in a dataset.
        
        Args:
            dataset_path: Path to dataset directory
            extract_audio: Whether to extract audio from videos
            preserve_quality: Whether to preserve video quality during remuxing
            
        Returns:
            Processing summary
        """
        logger.info(f"Processing dataset: {dataset_path}")
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")
        
        # Create output structure
        output_dirs = self.create_output_structure(dataset_path)
        
        # Discover .wmv files
        wmv_files = self.discover_wmv_files(dataset_path)
        
        if not wmv_files:
            logger.warning("No .wmv files found in dataset")
            return {
                'status': 'no_files',
                'dataset_path': str(dataset_path),
                'wmv_count': 0
            }
        
        # Process each file
        results = []
        successful = 0
        failed = 0
        
        for wmv_file in wmv_files:
            result = self.process_single_wmv(
                wmv_file, 
                output_dirs, 
                extract_audio=extract_audio,
                preserve_quality=preserve_quality
            )
            results.append(result)
            
            if result['status'] == 'success':
                successful += 1
            else:
                failed += 1
        
        # Generate summary
        summary = {
            'status': 'completed',
            'dataset_path': str(dataset_path),
            'wmv_files_found': len(wmv_files),
            'successful': successful,
            'failed': failed,
            'extract_audio': extract_audio,
            'preserve_quality': preserve_quality,
            'output_directories': {k: str(v) for k, v in output_dirs.items()},
            'results': results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save summary
        summary_file = output_dirs['metadata'] / f"processing_summary_{int(time.time())}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Processing completed:")
        logger.info(f"  Files processed: {len(wmv_files)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Summary saved: {summary_file}")
        
        return summary


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Process .wmv files with audio extraction and video remuxing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific dataset
  python src/process_wmv_files.py --dataset Datasets/.princesslexie
  
  # Process without audio extraction
  python src/process_wmv_files.py --dataset Datasets/.shay --no-audio
  
  # Process with re-encoding (smaller files)
  python src/process_wmv_files.py --dataset Datasets/.princesslexie --no-preserve-quality
  
  # Process a single file
  python src/process_wmv_files.py --file Datasets/.princesslexie/hooters-girl-revenge.wmv
        """
    )
    
    parser.add_argument(
        '--dataset', '-d',
        type=Path,
        help='Dataset directory to process'
    )
    
    parser.add_argument(
        '--file', '-f',
        type=Path,
        help='Single .wmv file to process'
    )
    
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Skip audio extraction'
    )
    
    parser.add_argument(
        '--no-preserve-quality',
        action='store_true',
        help='Re-encode video (smaller files, quality loss)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Custom output directory (default: dataset/outputs)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.dataset and not args.file:
        parser.error("Either --dataset or --file must be specified")
    
    if args.dataset and args.file:
        parser.error("Cannot specify both --dataset and --file")
    
    # Initialize processor
    processor = WMVProcessor()
    
    try:
        if args.file:
            # Process single file
            file_path = args.file
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                sys.exit(1)
            
            # Create output structure in file's directory or custom output
            if args.output_dir:
                output_base = args.output_dir
            else:
                output_base = file_path.parent / 'outputs'
            
            output_dirs = {
                'remux': output_base / 'remux',
                'audio': output_base / 'audio',
                'subtitles': output_base / 'subtitles',
                'metadata': output_base / 'metadata'
            }
            
            for dir_path in output_dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)
            
            result = processor.process_single_wmv(
                file_path,
                output_dirs,
                extract_audio=not args.no_audio,
                preserve_quality=not args.no_preserve_quality
            )
            
            if result['status'] == 'success':
                print(f"\n✅ File processed successfully!")
                print(f"   Input: {result['input_file']}")
                print(f"   Output: {result['output_video']}")
                if 'audio_file' in result:
                    print(f"   Audio: {result['audio_file']}")
            else:
                print(f"\n❌ Processing failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
        else:
            # Process dataset
            dataset_path = args.dataset
            
            summary = processor.process_dataset(
                dataset_path,
                extract_audio=not args.no_audio,
                preserve_quality=not args.no_preserve_quality
            )
            
            if summary['status'] == 'completed':
                print(f"\n✅ Dataset processing completed!")
                print(f"   Dataset: {summary['dataset_path']}")
                print(f"   Files processed: {summary['wmv_files_found']}")
                print(f"   Successful: {summary['successful']}")
                print(f"   Failed: {summary['failed']}")
            else:
                print(f"\n❌ Dataset processing failed: {summary.get('error', 'Unknown error')}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()