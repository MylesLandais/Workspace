#!/usr/bin/env python3
"""
DVD Title Classification Module - Module 2: The Analyzer

Analyzes extracted MKV files by duration and classifies them as main feature vs extras.
Uses heuristic rules based on duration to automatically categorize content.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from src.video_remuxer import VideoRemuxer, VideoInfo

logger = logging.getLogger(__name__)


@dataclass
class TitleClassification:
    """Classification result for a title."""
    file_path: Path
    duration: float
    category: str  # "main_feature", "long_extra", "short_extra", "junk"
    suggested_name: Optional[str] = None
    suggested_plex_suffix: Optional[str] = None


class TitleClassifier:
    """Module 2: Analyzes and classifies DVD titles by duration."""
    
    def __init__(
        self,
        main_feature_threshold: int = 80 * 60,  # 80 minutes in seconds
        long_extra_min: int = 10 * 60,  # 10 minutes
        long_extra_max: int = 60 * 60,  # 60 minutes
        short_extra_min: int = 2 * 60,  # 2 minutes
        short_extra_max: int = 10 * 60,  # 10 minutes
    ):
        """
        Initialize title classifier with duration thresholds.
        
        Args:
            main_feature_threshold: Minimum duration (seconds) to be considered main feature
            long_extra_min: Minimum duration for long extras (featurettes, making-of)
            long_extra_max: Maximum duration for long extras
            short_extra_min: Minimum duration for short extras (trailers)
            short_extra_max: Maximum duration for short extras
        """
        self.main_feature_threshold = main_feature_threshold
        self.long_extra_min = long_extra_min
        self.long_extra_max = long_extra_max
        self.short_extra_min = short_extra_min
        self.short_extra_max = short_extra_max
    
    def analyze_durations(
        self,
        mkv_files: List[Path],
        remuxer: Optional[VideoRemuxer] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze duration of all MKV files.
        
        Args:
            mkv_files: List of MKV file paths
            remuxer: Optional VideoRemuxer instance (creates new if not provided)
            
        Returns:
            List of metadata dictionaries with file path and duration
        """
        if remuxer is None:
            remuxer = VideoRemuxer()
        
        metadata = []
        
        for mkv_file in mkv_files:
            try:
                info = remuxer.get_video_info(mkv_file)
                metadata.append({
                    "path": mkv_file,
                    "duration": info.duration,
                    "duration_minutes": info.duration / 60,
                    "file_size": info.file_size,
                    "video_codec": info.video_codec,
                    "video_info": info
                })
                logger.debug(f"{mkv_file.name}: {info.duration / 60:.1f} minutes")
            except Exception as e:
                logger.warning(f"Could not analyze {mkv_file.name}: {e}")
                # Include with unknown duration
                metadata.append({
                    "path": mkv_file,
                    "duration": 0,
                    "duration_minutes": 0,
                    "file_size": mkv_file.stat().st_size if mkv_file.exists() else 0,
                    "error": str(e)
                })
        
        # Sort by duration descending (longest first)
        metadata.sort(key=lambda x: x["duration"], reverse=True)
        
        return metadata
    
    def classify_by_duration(
        self,
        metadata: List[Dict[str, Any]]
    ) -> List[TitleClassification]:
        """
        Classify titles based on duration heuristics.
        
        Args:
            metadata: List of title metadata from analyze_durations()
            
        Returns:
            List of TitleClassification objects
        """
        if not metadata:
            return []
        
        classifications = []
        
        for i, title_data in enumerate(metadata):
            duration = title_data["duration"]
            file_path = title_data["path"]
            
            # Main feature: longest file (if it's reasonably long, >45 min)
            # Use a lower threshold to catch movies that are shorter than typical
            main_feature_min = 45 * 60  # 45 minutes minimum
            if i == 0 and duration >= main_feature_min:
                category = "main_feature"
                suggested_plex_suffix = None  # Main feature has no suffix
            # Long extras: 10-60 minutes (featurettes, making-of, deleted scenes)
            elif self.long_extra_min <= duration <= self.long_extra_max:
                category = "long_extra"
                suggested_plex_suffix = "featurette"  # Default, user can change
            # Short extras: 2-10 minutes (trailers, interviews)
            elif self.short_extra_min <= duration <= self.short_extra_max:
                category = "short_extra"
                suggested_plex_suffix = "trailer"  # Default, user can change
            # Junk: <2 minutes (FBI warnings, logos) - should have been filtered
            else:
                category = "junk"
                suggested_plex_suffix = None
            
            # Generate suggested name from filename
            suggested_name = self._suggest_name(file_path, category, i)
            
            classifications.append(TitleClassification(
                file_path=file_path,
                duration=duration,
                category=category,
                suggested_name=suggested_name,
                suggested_plex_suffix=suggested_plex_suffix
            ))
        
        return classifications
    
    def _suggest_name(
        self,
        file_path: Path,
        category: str,
        index: int
    ) -> str:
        """Generate a suggested name for the title."""
        base_name = file_path.stem
        
        if category == "main_feature":
            return base_name
        elif category == "long_extra":
            return f"{base_name} - Extra {index}"
        elif category == "short_extra":
            return f"{base_name} - Trailer"
        else:
            return base_name
    
    def print_classification_summary(
        self,
        classifications: List[TitleClassification]
    ) -> None:
        """Print a summary of classifications."""
        if not classifications:
            print("No titles to classify")
            return
        
        print("\n" + "=" * 70)
        print("TITLE CLASSIFICATION SUMMARY")
        print("=" * 70)
        
        for i, cls in enumerate(classifications, 1):
            duration_str = f"{cls.duration / 60:.1f} min"
            category_str = cls.category.replace("_", " ").title()
            
            print(f"\n{i}. {cls.file_path.name}")
            print(f"   Duration: {duration_str}")
            print(f"   Category: {category_str}")
            
            if cls.suggested_plex_suffix:
                print(f"   Suggested Plex suffix: -{cls.suggested_plex_suffix}")
            
            if cls.category == "main_feature":
                print("   >>> MAIN FEATURE (longest title)")
        
        print("\n" + "=" * 70)
    
    def get_main_feature(self, classifications: List[TitleClassification]) -> Optional[TitleClassification]:
        """Get the main feature classification (should be the longest)."""
        main_features = [c for c in classifications if c.category == "main_feature"]
        if main_features:
            return main_features[0]  # Should only be one
        return None
    
    def get_extras(self, classifications: List[TitleClassification]) -> List[TitleClassification]:
        """Get all extras (non-main-feature titles)."""
        return [c for c in classifications if c.category != "main_feature" and c.category != "junk"]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    classifier = TitleClassifier()
    print(f"Main feature threshold: {classifier.main_feature_threshold / 60:.0f} minutes")
    print(f"Long extras: {classifier.long_extra_min / 60:.0f}-{classifier.long_extra_max / 60:.0f} minutes")
    print(f"Short extras: {classifier.short_extra_min / 60:.0f}-{classifier.short_extra_max / 60:.0f} minutes")

