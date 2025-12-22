#!/usr/bin/env python3
"""
File Naming Policy Module

Defines and enforces file/folder naming conventions that include IMDB tags.
Format: {Title} ({Year}) [{imdb_id}].{ext}
"""

import re
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileNamingPolicy:
    """Defines file and folder naming conventions with IMDB tags."""
    
    # Characters that are problematic in filenames
    INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    
    def __init__(self):
        """Initialize naming policy."""
        pass
    
    def sanitize_title(self, title: str) -> str:
        """
        Sanitize title for filesystem compatibility.
        
        Args:
            title: Original title
            
        Returns:
            Sanitized title safe for filesystem
        """
        # Replace invalid filesystem characters
        sanitized = self.INVALID_FS_CHARS.sub('_', title)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Replace multiple underscores/spaces with single underscore
        sanitized = re.sub(r'[_\s]+', ' ', sanitized)
        
        return sanitized.strip()
    
    def generate_filename(
        self,
        title: str,
        year: Optional[int] = None,
        imdb_id: Optional[str] = None,
        extension: str = "mkv"
    ) -> str:
        """
        Generate filename according to naming policy.
        
        Format: {Title} ({Year}) [{imdb_id}].{ext}
        
        Edge cases:
        - If no year: {Title} [{imdb_id}].{ext}
        - If no IMDB ID: {Title} ({Year}).{ext} or {Title}.{ext}
        
        Args:
            title: Movie/TV show title
            year: Release year (optional)
            imdb_id: IMDB ID (optional, e.g., "tt0898897")
            extension: File extension (default: "mkv")
            
        Returns:
            Generated filename
        """
        # Sanitize title
        safe_title = self.sanitize_title(title)
        
        # Build filename parts
        parts = [safe_title]
        
        # Add year if available
        if year:
            parts.append(f"({year})")
        
        # Add IMDB ID if available
        if imdb_id:
            # Normalize IMDB ID
            imdb_id = imdb_id.strip().lower()
            if not imdb_id.startswith('tt'):
                imdb_id = f"tt{imdb_id}"
            parts.append(f"[{imdb_id}]")
        
        # Join parts
        base_name = " ".join(parts)
        
        # Ensure extension doesn't start with dot if not provided
        if extension and not extension.startswith('.'):
            extension = f".{extension}"
        elif not extension:
            extension = ""
        
        filename = f"{base_name}{extension}"
        
        return filename
    
    def generate_foldername(
        self,
        title: str,
        year: Optional[int] = None,
        imdb_id: Optional[str] = None
    ) -> str:
        """
        Generate folder name according to naming policy.
        
        Format: {Title} ({Year}) [{imdb_id}]/
        
        Args:
            title: Movie/TV show title
            year: Release year (optional)
            imdb_id: IMDB ID (optional)
            
        Returns:
            Generated folder name
        """
        # Use same logic as filename but without extension
        return self.generate_filename(title, year, imdb_id, extension="")
    
    def parse_existing_filename(self, filename: str) -> dict:
        """
        Parse existing filename to extract title, year, and IMDB ID.
        
        Attempts to extract metadata from filenames that may already
        follow the naming convention or similar formats.
        
        Args:
            filename: Existing filename (with or without extension)
            
        Returns:
            Dictionary with 'title', 'year', 'imdb_id' keys
        """
        # Remove extension
        base = Path(filename).stem
        
        result = {
            'title': None,
            'year': None,
            'imdb_id': None
        }
        
        # Try to extract IMDB ID: [tt\d+]
        imdb_match = re.search(r'\[(tt\d+)\]', base)
        if imdb_match:
            result['imdb_id'] = imdb_match.group(1)
            base = base[:imdb_match.start()] + base[imdb_match.end():]
            base = base.strip()
        
        # Try to extract year: (YYYY)
        year_match = re.search(r'\((\d{4})\)', base)
        if year_match:
            try:
                result['year'] = int(year_match.group(1))
                base = base[:year_match.start()] + base[year_match.end():]
                base = base.strip()
            except ValueError:
                pass
        
        # Remaining text is title
        result['title'] = base.strip()
        
        return result
    
    def should_rename(
        self,
        current_name: str,
        target_name: str
    ) -> bool:
        """
        Check if a file/folder should be renamed.
        
        Args:
            current_name: Current name
            target_name: Target name
            
        Returns:
            True if names differ (case-insensitive), False otherwise
        """
        # Compare case-insensitively
        if current_name.lower() == target_name.lower():
            return False
        
        # Also check if they're the same after normalization
        current_norm = self._normalize_for_comparison(current_name)
        target_norm = self._normalize_for_comparison(target_name)
        
        return current_norm != target_norm
    
    def _normalize_for_comparison(self, name: str) -> str:
        """
        Normalize name for comparison (removes extension, lowercases, trims).
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized name
        """
        # Remove extension
        base = Path(name).stem
        # Lowercase and strip
        return base.lower().strip()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    policy = FileNamingPolicy()
    
    # Test filename generation
    print("Filename generation examples:")
    print(f"  {policy.generate_filename('Ballerina', 2006, 'tt0898897', 'mkv')}")
    print(f"  {policy.generate_filename('Ballerina', 2006, None, 'mkv')}")
    print(f"  {policy.generate_filename('Ballerina', None, 'tt0898897', 'mkv')}")
    print(f"  {policy.generate_filename('Ballerina', None, None, 'mkv')}")
    
    # Test foldername generation
    print("\nFoldername generation examples:")
    print(f"  {policy.generate_foldername('Ballerina', 2006, 'tt0898897')}")
    print(f"  {policy.generate_foldername('Ballerina', 2006, None)}")
    
    # Test parsing
    print("\nFilename parsing examples:")
    parsed = policy.parse_existing_filename("Ballerina (2006) [tt0898897].mkv")
    print(f"  Parsed: {parsed}")
    
    parsed2 = policy.parse_existing_filename("Ballerina (2006).mkv")
    print(f"  Parsed: {parsed2}")

