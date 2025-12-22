#!/usr/bin/env python3
"""
Plex Organization Module - Module 3: The Organizer

Organizes extracted and classified DVD titles into Plex-compatible directory structure
with proper naming conventions for automatic extras detection.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from src.dvd_classifier import TitleClassification

logger = logging.getLogger(__name__)


# Plex extras suffix mappings
PLEX_EXTRAS_SUFFIXES = {
    "trailer": "trailer",
    "behindthescenes": "behindthescenes",
    "featurette": "featurette",
    "deleted": "deleted",
    "interview": "interview",
    "short": "short",
    "scene": "scene",  # Generic fallback
}


class PlexOrganizer:
    """Module 3: Organizes files for Plex library structure."""
    
    def __init__(self):
        """Initialize Plex organizer."""
        self.extras_suffixes = PLEX_EXTRAS_SUFFIXES.copy()
    
    def create_plex_structure(
        self,
        output_base: Path,
        movie_name: str,
        year: Optional[int] = None
    ) -> Path:
        """
        Create Plex directory structure for a movie.
        
        Plex structure: Movies/Movie Name (Year)/
        
        Args:
            output_base: Base directory (e.g., /path/to/Movies)
            movie_name: Movie name
            year: Release year (optional)
            
        Returns:
            Path to created movie directory
        """
        output_base = Path(output_base)
        
        if year:
            folder_name = f"{movie_name} ({year})"
        else:
            folder_name = movie_name
        
        movie_dir = output_base / folder_name
        movie_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created Plex directory: {movie_dir}")
        return movie_dir
    
    def generate_plex_filename(
        self,
        movie_name: str,
        year: Optional[int],
        extra_name: Optional[str] = None,
        plex_suffix: Optional[str] = None,
        is_main_feature: bool = False
    ) -> str:
        """
        Generate Plex-compliant filename.
        
        Main feature: "Movie Name (Year).mkv"
        Extras: "Movie Name (Year) - Extra Name-suffix.mkv"
        
        Args:
            movie_name: Movie name
            year: Release year
            extra_name: Name of the extra (for extras only)
            plex_suffix: Plex extras suffix (trailer, featurette, etc.)
            is_main_feature: Whether this is the main feature
            
        Returns:
            Plex-compliant filename (without directory)
        """
        base = movie_name
        if year:
            base = f"{base} ({year})"
        
        if is_main_feature:
            return f"{base}.mkv"
        
        if not extra_name:
            extra_name = "Extra"
        
        if plex_suffix and plex_suffix in self.extras_suffixes:
            return f"{base} - {extra_name}-{plex_suffix}.mkv"
        else:
            # Default to scene if suffix invalid
            return f"{base} - {extra_name}-scene.mkv"
    
    def organize_main_feature(
        self,
        classification: TitleClassification,
        movie_dir: Path,
        movie_name: str,
        year: Optional[int] = None
    ) -> Path:
        """
        Move and rename main feature file.
        
        Args:
            classification: TitleClassification for main feature
            movie_dir: Plex movie directory
            movie_name: Movie name
            year: Release year
            
        Returns:
            Path to final main feature file
        """
        filename = self.generate_plex_filename(
            movie_name=movie_name,
            year=year,
            is_main_feature=True
        )
        
        dest_path = movie_dir / filename
        
        logger.info(f"Moving main feature:")
        logger.info(f"  From: {classification.file_path.name}")
        logger.info(f"  To: {dest_path.name}")
        
        shutil.move(str(classification.file_path), str(dest_path))
        
        return dest_path
    
    def organize_extra(
        self,
        classification: TitleClassification,
        movie_dir: Path,
        movie_name: str,
        year: Optional[int] = None,
        extra_name: Optional[str] = None,
        plex_suffix: Optional[str] = None
    ) -> Path:
        """
        Move and rename an extra file.
        
        Args:
            classification: TitleClassification for extra
            movie_dir: Plex movie directory
            movie_name: Movie name
            year: Release year
            extra_name: Custom name for the extra (uses suggested if not provided)
            plex_suffix: Plex suffix (uses suggested if not provided)
            
        Returns:
            Path to final extra file
        """
        if not extra_name:
            # Extract name from suggested name or filename
            extra_name = classification.suggested_name
            if extra_name and " - " in extra_name:
                extra_name = extra_name.split(" - ", 1)[1]
            else:
                extra_name = classification.file_path.stem
        
        if not plex_suffix:
            plex_suffix = classification.suggested_plex_suffix or "scene"
        
        filename = self.generate_plex_filename(
            movie_name=movie_name,
            year=year,
            extra_name=extra_name,
            plex_suffix=plex_suffix,
            is_main_feature=False
        )
        
        dest_path = movie_dir / filename
        
        logger.info(f"Moving extra:")
        logger.info(f"  From: {classification.file_path.name}")
        logger.info(f"  To: {dest_path.name}")
        
        shutil.move(str(classification.file_path), str(dest_path))
        
        return dest_path
    
    def organize_all(
        self,
        main_feature: TitleClassification,
        extras: List[TitleClassification],
        output_base: Path,
        movie_name: str,
        year: Optional[int] = None,
        extra_names: Optional[Dict[Path, Dict[str, str]]] = None
    ) -> Dict[str, Path]:
        """
        Organize all titles into Plex structure.
        
        Args:
            main_feature: Main feature classification
            extras: List of extra classifications
            output_base: Base output directory
            movie_name: Movie name
            year: Release year
            extra_names: Optional dict mapping file paths to {name, suffix} for extras
            
        Returns:
            Dictionary with 'main_feature' and 'extras' keys containing lists of final paths
        """
        movie_dir = self.create_plex_structure(output_base, movie_name, year)
        
        # Organize main feature
        main_path = self.organize_main_feature(
            main_feature,
            movie_dir,
            movie_name,
            year
        )
        
        # Organize extras
        extra_paths = []
        for i, extra in enumerate(extras):
            extra_config = None
            if extra_names and extra.file_path in extra_names:
                extra_config = extra_names[extra.file_path]
            
            extra_path = self.organize_extra(
                extra,
                movie_dir,
                movie_name,
                year,
                extra_name=extra_config.get("name") if extra_config else None,
                plex_suffix=extra_config.get("suffix") if extra_config else None
            )
            extra_paths.append(extra_path)
        
        return {
            "main_feature": main_path,
            "extras": extra_paths,
            "movie_dir": movie_dir
        }
    
    def list_plex_suffixes(self) -> List[str]:
        """List available Plex extras suffixes."""
        return list(self.extras_suffixes.keys())


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    organizer = PlexOrganizer()
    print("Available Plex extras suffixes:")
    for suffix in organizer.list_plex_suffixes():
        print(f"  -{suffix}")

