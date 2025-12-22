#!/usr/bin/env python3
"""
Video File Discovery Module

Discovers video files in directories and extracts metadata from filenames.
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import logging
import re

from src.file_naming_policy import FileNamingPolicy

logger = logging.getLogger(__name__)


# Common video file extensions
VIDEO_EXTENSIONS = {
    '.mkv', '.mp4', '.avi', '.wmv', '.mov', '.flv', '.webm',
    '.m4v', '.mpg', '.mpeg', '.vob', '.ts', '.m2ts',
    # Uppercase variants
    '.MKV', '.MP4', '.AVI', '.WMV', '.MOV', '.FLV', '.WEBM',
    '.M4V', '.MPG', '.MPEG', '.VOB', '.TS', '.M2TS'
}


@dataclass
class VideoFile:
    """Represents a discovered video file with parsed metadata."""
    file_path: Path
    title: Optional[str] = None
    year: Optional[int] = None
    imdb_id: Optional[str] = None
    extension: str = ""
    
    @property
    def current_name(self) -> str:
        """Get current filename."""
        return self.file_path.name
    
    @property
    def stem(self) -> str:
        """Get filename stem (without extension)."""
        return self.file_path.stem


class VideoFileDiscovery:
    """Discovers video files and extracts metadata from filenames."""
    
    def __init__(self):
        """Initialize video file discovery."""
        self.naming_policy = FileNamingPolicy()
    
    def discover_video_files(
        self,
        directory: Path,
        recursive: bool = True
    ) -> List[VideoFile]:
        """
        Discover all video files in a directory.
        
        Args:
            directory: Directory to search
            recursive: Whether to search recursively
            
        Returns:
            List of VideoFile objects with parsed metadata
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []
        
        if not directory.is_dir():
            logger.warning(f"Path is not a directory: {directory}")
            return []
        
        video_files = []
        
        # Search for video files
        if recursive:
            for ext in VIDEO_EXTENSIONS:
                video_files.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in VIDEO_EXTENSIONS:
                video_files.extend(directory.glob(f"*{ext}"))
        
        # Remove duplicates (case-insensitive matching can create duplicates)
        seen = set()
        unique_files = []
        for vf in video_files:
            key = str(vf).lower()
            if key not in seen:
                seen.add(key)
                unique_files.append(vf)
        
        logger.info(f"Found {len(unique_files)} video file(s) in {directory}")
        
        # Parse metadata from each file
        result = []
        for file_path in unique_files:
            try:
                video_file = self._parse_video_file(file_path)
                result.append(video_file)
            except Exception as e:
                logger.error(f"Error parsing file {file_path}: {e}", exc_info=True)
        
        return result
    
    def _parse_video_file(self, file_path: Path) -> VideoFile:
        """
        Parse a video file to extract metadata from filename.
        
        Args:
            file_path: Path to video file
            
        Returns:
            VideoFile object with parsed metadata
        """
        filename = file_path.name
        extension = file_path.suffix
        
        # Use naming policy to parse existing filename
        parsed = self.naming_policy.parse_existing_filename(filename)
        
        # If title wasn't parsed, try to extract from stem
        if not parsed['title'] or parsed['title'].strip() == '':
            # Try to clean up the stem to get a reasonable title
            stem = file_path.stem
            # Remove common release group tags, quality tags, etc.
            stem = self._clean_filename_stem(stem)
            parsed['title'] = stem.strip()
        
        return VideoFile(
            file_path=file_path,
            title=parsed['title'],
            year=parsed['year'],
            imdb_id=parsed['imdb_id'],
            extension=extension
        )
    
    def _clean_filename_stem(self, stem: str) -> str:
        """
        Clean filename stem by removing common release tags and metadata.
        
        Args:
            stem: Filename stem
            
        Returns:
            Cleaned stem
        """
        # Remove common patterns that appear in release filenames
        # This is a best-effort attempt to extract the actual title
        
        # Remove resolution tags: 1080p, 720p, 4K, etc.
        stem = re.sub(r'\b\d+p\b', '', stem, flags=re.IGNORECASE)
        stem = re.sub(r'\b\d+K\b', '', stem, flags=re.IGNORECASE)
        
        # Remove codec tags: x264, x265, H264, etc.
        stem = re.sub(r'\b(x26[45]|H\.?264|H\.?265|HEVC|AVC)\b', '', stem, flags=re.IGNORECASE)
        
        # Remove release group tags (usually in brackets or parentheses at the end)
        # e.g., [RARBG], (RARBG), -RARBG
        stem = re.sub(r'[\[\(-][A-Z0-9-]+\][\)]?$', '', stem)
        
        # Remove quality tags: BluRay, WEB-DL, DVD, etc.
        stem = re.sub(r'\b(BluRay|WEB-DL|WEBRip|DVDRip|BDRip|HDTV|DVD|BRRip)\b', '', stem, flags=re.IGNORECASE)
        
        # Remove audio codec tags: DTS, AC3, AAC, etc.
        stem = re.sub(r'\b(DTS|AC3|AAC|MP3|FLAC|TrueHD)\b', '', stem, flags=re.IGNORECASE)
        
        # Clean up multiple spaces/separators
        stem = re.sub(r'[.\-_\[\]()]+', ' ', stem)
        stem = re.sub(r'\s+', ' ', stem)
        
        return stem.strip()
    
    def discover_single_file(self, file_path: Path) -> Optional[VideoFile]:
        """
        Discover and parse a single video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            VideoFile object if file exists and is a video file, None otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return None
        
        if not file_path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return None
        
        if file_path.suffix not in VIDEO_EXTENSIONS:
            logger.warning(f"File is not a recognized video format: {file_path}")
            return None
        
        try:
            return self._parse_video_file(file_path)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}", exc_info=True)
            return None


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    discovery = VideoFileDiscovery()
    
    # Test discovery (using current directory as example)
    import os
    test_dir = Path(os.getcwd())
    
    print(f"Discovering video files in: {test_dir}")
    video_files = discovery.discover_video_files(test_dir, recursive=False)
    
    for vf in video_files[:5]:  # Show first 5
        print(f"\nFile: {vf.current_name}")
        print(f"  Title: {vf.title}")
        print(f"  Year: {vf.year}")
        print(f"  IMDB ID: {vf.imdb_id}")

