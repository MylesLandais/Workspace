#!/usr/bin/env python3
"""
Private Dataset Processing Script Template

This script processes .wmv files in private datasets using the CanaryQwen ASR model.
It is designed to be run after Vaporeon baseline testing passes validation.

Usage:
    python src/process_private_datasets.py --dataset .princesslexie --model canary-qwen-2.5b
    python src/process_private_datasets.py --dataset .shay --model canary-qwen-2.5b --dry-run
    python src/process_private_datasets.py --list-datasets
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from asr_evaluation.adapters.canary_qwen_adapter import CanaryQwenAdapter
from asr_evaluation.core.interfaces import TranscriptionResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('private_dataset_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PrivateDatasetProcessor:
    """Processes .wmv files in private datasets with privacy controls."""
    
    def __init__(self, base_datasets_dir: Path = Path("Datasets")):
        """
        Initialize the processor.
        
        Args:
            base_datasets_dir: Base directory containing datasets
        """
        self.base_datasets_dir = base_datasets_dir
        self.processed_files = []
        self.failed_files = []
        
    def discover_private_datasets(self) -> List[Path]:
        """
        Discover private datasets (hidden directories starting with .).
        
        Returns:
            List of private dataset directories
        """
        if not self.base_datasets_dir.exists():
            logger.warning(f"Datasets directory not found: {self.base_datasets_dir}")
            return []
        
        private_datasets = []
        
        for item in self.base_datasets_dir.iterdir():
            if item.is_dir() and item.name.startswith('.'):
                private_datasets.append(item)
                logger.info(f"Found private dataset: {item.name}")
        
        return private_datasets
    
    def discover_wmv_files(self, dataset_dir: Path) -> List[Path]:
        """
        Recursively discover .wmv files in a dataset directory.
        
        Args:
            dataset_dir: Dataset directory to search
            
        Returns:
            List of .wmv file paths
        """
        wmv_files = []
        
        # Look for .wmv files recursively
        for wmv_file in dataset_dir.rglob("*.wmv"):
            wmv_files.append(wmv_file)
        
        # Also check for .WMV (uppercase)
        for wmv_file in dataset_dir.rglob("*.WMV"):
            wmv_files.append(wmv_file)
        
        logger.info(f"Found {len(wmv_files)} .wmv files in {dataset_dir.name}")
        return wmv_files
    
    def create_dataset_structure(self, dataset_dir: Path) -> Dict[str, Path]:
        """
        Create output directory structure within the dataset.
        
        Args:
            dataset_dir: Dataset root directory
            
        Returns:
            Dictionary of output directories
        """
        structure = {
            'outputs': dataset_dir / 'outputs',
            'transcripts': dataset_dir / 'outputs' / 'transcripts',
            'remux': dataset_dir / 'outputs' / 'remux',
            'subtitles': dataset_dir / 'subtitles',
            'metadata': dataset_dir / 'metadata'
        }
        
        # Create directories if they don't exist
        for dir_type, dir_path in structure.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")
        
        return structure
    
    def get_output_paths(self, wmv_file: Path, dataset_structure: Dict[str, Path], 
                        model_name: str) -> Dict[str, Path]:
        """
        Generate output file paths for a .wmv file.
        
        Args:
            wmv_file: Input .wmv file path
            dataset_structure: Dataset directory structure
            model_name: ASR model name for file naming
            
        Returns:
            Dictionary of output file paths
        """
        # Create safe filename from original
        base_name = wmv_file.stem
        safe_name = "".join(c for c in base_name if c.isalnum() or c in "._-")
        
        # Add model prefix to distinguish between different ASR models
        model_prefix = model_name.replace("/", "_").replace("-", "_")
        
        return {
            'transcript': dataset_structure['transcripts'] / f"{model_prefix}_{safe_name}.txt",
            'subtitle_ass': dataset_structure['subtitles'] / f"{model_prefix}_{safe_name}.ass",
            'subtitle_srt': dataset_structure['subtitles'] / f"{model_prefix}_{safe_name}.srt",
            'remuxed_video': dataset_structure['remux'] / f"{safe_name}.mkv",
            'metadata': dataset_structure['metadata'] / f"{model_prefix}_{safe_name}_metadata.json"
        }
    
    def validate_vaporeon_baseline(self) -> bool:
        """
        Validate that CanaryQwen performs well on Vaporeon baseline.
        
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Validating CanaryQwen performance on Vaporeon baseline...")
        
        vaporeon_audio = Path("evaluation_datasets/vaporeon/-EWMgB26bmU_Vaporeon copypasta (animated).mp3")
        reference_file = Path("evaluation_datasets/vaporeon/reference_transcript.txt")
        
        if not vaporeon_audio.exists():
            logger.error(f"Vaporeon audio file not found: {vaporeon_audio}")
            return False
        
        if not reference_file.exists():
            logger.error(f"Vaporeon reference transcript not found: {reference_file}")
            return False
        
        # Load reference text
        with open(reference_file, 'r') as f:
            reference_text = f.read().strip()
        
        # Test CanaryQwen
        try:
            adapter = CanaryQwenAdapter()
            
            if not adapter.is_available():
                logger.error("CanaryQwen model not available")
                return False
            
            # Transcribe Vaporeon
            result = adapter.transcribe(str(vaporeon_audio))
            
            # Simple validation - check for key terms
            predicted_lower = result.text.lower()
            reference_lower = reference_text.lower()
            
            key_terms = ["vaporeon", "pokemon", "human", "breeding"]
            found_terms = [term for term in key_terms if term in predicted_lower]
            
            # Calculate basic word overlap
            predicted_words = set(predicted_lower.split())
            reference_words = set(reference_lower.split())
            overlap_ratio = len(predicted_words & reference_words) / len(reference_words)
            
            logger.info(f"Vaporeon validation results:")
            logger.info(f"  Processing time: {result.processing_time:.2f}s")
            logger.info(f"  Key terms found: {found_terms}")
            logger.info(f"  Word overlap ratio: {overlap_ratio:.2%}")
            logger.info(f"  Transcription length: {len(result.text)} chars")
            
            # Validation criteria
            if len(found_terms) >= 2 and overlap_ratio >= 0.3:
                logger.info("✅ Vaporeon baseline validation PASSED")
                return True
            else:
                logger.warning("❌ Vaporeon baseline validation FAILED")
                logger.warning("  Criteria: >=2 key terms and >=30% word overlap")
                return False
                
        except Exception as e:
            logger.error(f"Vaporeon validation failed with error: {e}")
            return False
    
    def process_wmv_file(self, wmv_file: Path, output_paths: Dict[str, Path], 
                        adapter: CanaryQwenAdapter, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process a single .wmv file to generate transcript.
        
        Args:
            wmv_file: Input .wmv file
            output_paths: Output file paths
            adapter: CanaryQwen adapter instance
            dry_run: If True, don't actually process files
            
        Returns:
            Processing result dictionary
        """
        logger.info(f"Processing: {wmv_file.name}")
        
        if dry_run:
            logger.info(f"  DRY RUN - Would create:")
            logger.info(f"    Transcript: {output_paths['transcript']}")
            logger.info(f"    Metadata: {output_paths['metadata']}")
            return {
                'status': 'dry_run',
                'wmv_file': str(wmv_file),
                'output_paths': {k: str(v) for k, v in output_paths.items()}
            }
        
        # Check if transcript already exists
        if output_paths['transcript'].exists():
            logger.info(f"  Transcript already exists: {output_paths['transcript'].name}")
            return {
                'status': 'skipped',
                'reason': 'transcript_exists',
                'wmv_file': str(wmv_file),
                'transcript_file': str(output_paths['transcript'])
            }
        
        try:
            start_time = time.time()
            
            # Convert .wmv to audio format that ASR can handle
            # Note: This would require ffmpeg integration for production use
            logger.warning("  NOTE: .wmv to audio conversion not implemented yet")
            logger.warning("  This template assumes audio extraction is handled separately")
            
            # For now, skip actual processing and create placeholder
            # In production, you would:
            # 1. Extract audio from .wmv using ffmpeg
            # 2. Transcribe the audio
            # 3. Save clean transcript
            # 4. Generate subtitles (optional)
            # 5. Remux video with subtitles (optional)
            
            processing_time = time.time() - start_time
            
            # Create placeholder transcript for template
            placeholder_text = f"[PLACEHOLDER] Transcript for {wmv_file.name} would be generated here"
            
            # Save transcript
            with open(output_paths['transcript'], 'w') as f:
                f.write(placeholder_text)
            
            # Save metadata
            metadata = {
                'source_file': str(wmv_file),
                'model_name': adapter.model_name,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'transcript_length': len(placeholder_text),
                'word_count': len(placeholder_text.split()),
                'status': 'placeholder'
            }
            
            with open(output_paths['metadata'], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"  ✅ Created placeholder files in {processing_time:.2f}s")
            
            return {
                'status': 'success',
                'wmv_file': str(wmv_file),
                'transcript_file': str(output_paths['transcript']),
                'metadata_file': str(output_paths['metadata']),
                'processing_time': processing_time,
                'transcript_length': len(placeholder_text),
                'word_count': len(placeholder_text.split())
            }
            
        except Exception as e:
            logger.error(f"  ❌ Failed to process {wmv_file.name}: {e}")
            return {
                'status': 'error',
                'wmv_file': str(wmv_file),
                'error': str(e)
            }
    
    def process_dataset(self, dataset_name: str, model_name: str = "nvidia/canary-qwen-2.5b", 
                       dry_run: bool = False, skip_validation: bool = False) -> Dict[str, Any]:
        """
        Process all .wmv files in a private dataset.
        
        Args:
            dataset_name: Name of the dataset (e.g., '.princesslexie')
            model_name: ASR model to use
            dry_run: If True, don't actually process files
            skip_validation: If True, skip Vaporeon baseline validation
            
        Returns:
            Processing summary
        """
        logger.info(f"Starting processing of dataset: {dataset_name}")
        
        # Validate Vaporeon baseline first (unless skipped)
        if not skip_validation:
            if not self.validate_vaporeon_baseline():
                logger.error("Vaporeon baseline validation failed - aborting private dataset processing")
                return {
                    'status': 'validation_failed',
                    'message': 'Vaporeon baseline validation failed'
                }
        else:
            logger.info("Skipping Vaporeon baseline validation (--skip-validation)")
        
        # Find dataset directory
        dataset_dir = self.base_datasets_dir / dataset_name
        
        if not dataset_dir.exists():
            logger.error(f"Dataset directory not found: {dataset_dir}")
            return {
                'status': 'dataset_not_found',
                'dataset_name': dataset_name,
                'expected_path': str(dataset_dir)
            }
        
        # Create dataset structure
        dataset_structure = self.create_dataset_structure(dataset_dir)
        
        # Discover .wmv files
        wmv_files = self.discover_wmv_files(dataset_dir)
        
        if not wmv_files:
            logger.warning(f"No .wmv files found in {dataset_name}")
            return {
                'status': 'no_files',
                'dataset_name': dataset_name,
                'wmv_count': 0
            }
        
        # Initialize ASR adapter
        if not dry_run:
            try:
                adapter = CanaryQwenAdapter(model_name=model_name)
                if not adapter.is_available():
                    logger.error(f"ASR model not available: {model_name}")
                    return {
                        'status': 'model_unavailable',
                        'model_name': model_name
                    }
            except Exception as e:
                logger.error(f"Failed to initialize ASR adapter: {e}")
                return {
                    'status': 'adapter_error',
                    'error': str(e)
                }
        else:
            adapter = None
        
        # Process each .wmv file
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        for wmv_file in wmv_files:
            output_paths = self.get_output_paths(wmv_file, dataset_structure, model_name)
            result = self.process_wmv_file(wmv_file, output_paths, adapter, dry_run)
            
            results.append(result)
            
            if result['status'] == 'success':
                successful += 1
            elif result['status'] == 'error':
                failed += 1
            elif result['status'] == 'skipped':
                skipped += 1
        
        # Generate summary
        summary = {
            'status': 'completed',
            'dataset_name': dataset_name,
            'model_name': model_name,
            'dry_run': dry_run,
            'wmv_files_found': len(wmv_files),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'results': results,
            'output_directories': {k: str(v) for k, v in dataset_structure.items()},
            'timestamp': datetime.now().isoformat()
        }
        
        # Save processing summary
        summary_file = dataset_structure['metadata'] / f"processing_summary_{int(time.time())}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Processing completed:")
        logger.info(f"  Dataset: {dataset_name}")
        logger.info(f"  Files found: {len(wmv_files)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Skipped: {skipped}")
        logger.info(f"  Summary saved: {summary_file}")
        
        return summary


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Process .wmv files in private datasets using CanaryQwen ASR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available private datasets
  python src/process_private_datasets.py --list-datasets
  
  # Dry run on a specific dataset
  python src/process_private_datasets.py --dataset .princesslexie --dry-run
  
  # Process a dataset with CanaryQwen
  python src/process_private_datasets.py --dataset .shay --model nvidia/canary-qwen-2.5b
  
  # Process without Vaporeon validation (not recommended)
  python src/process_private_datasets.py --dataset .princesslexie --skip-validation
        """
    )
    
    parser.add_argument(
        '--dataset', '-d',
        help='Private dataset name to process (e.g., .princesslexie, .shay)'
    )
    
    parser.add_argument(
        '--model', '-m',
        default='nvidia/canary-qwen-2.5b',
        help='ASR model to use (default: nvidia/canary-qwen-2.5b)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually doing it'
    )
    
    parser.add_argument(
        '--list-datasets',
        action='store_true',
        help='List available private datasets and exit'
    )
    
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip Vaporeon baseline validation (not recommended)'
    )
    
    parser.add_argument(
        '--datasets-dir',
        type=Path,
        default=Path('Datasets'),
        help='Base datasets directory (default: Datasets)'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = PrivateDatasetProcessor(base_datasets_dir=args.datasets_dir)
    
    # List datasets if requested
    if args.list_datasets:
        print("Discovering private datasets...")
        private_datasets = processor.discover_private_datasets()
        
        if private_datasets:
            print(f"\nFound {len(private_datasets)} private datasets:")
            for dataset_dir in private_datasets:
                wmv_files = processor.discover_wmv_files(dataset_dir)
                print(f"  {dataset_dir.name}: {len(wmv_files)} .wmv files")
        else:
            print("No private datasets found (directories starting with '.')")
        
        return
    
    # Validate arguments
    if not args.dataset:
        parser.error("--dataset is required (or use --list-datasets)")
    
    if not args.dataset.startswith('.'):
        logger.warning(f"Dataset name '{args.dataset}' doesn't start with '.' - are you sure it's private?")
    
    # Process the dataset
    try:
        result = processor.process_dataset(
            dataset_name=args.dataset,
            model_name=args.model,
            dry_run=args.dry_run,
            skip_validation=args.skip_validation
        )
        
        if result['status'] == 'completed':
            print(f"\n✅ Processing completed successfully!")
            print(f"   Dataset: {result['dataset_name']}")
            print(f"   Files processed: {result['successful']}")
            print(f"   Files failed: {result['failed']}")
            print(f"   Files skipped: {result['skipped']}")
        else:
            print(f"\n❌ Processing failed: {result.get('message', result['status'])}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()