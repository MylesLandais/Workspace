#!/usr/bin/env python3
"""
File Renamer Module

Orchestrates discovery, IMDB matching, and renaming of video files and folders
according to naming policy with IMDB tags.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from src.imdb_matcher import IMDBMatcher, IMDBResult
from src.file_naming_policy import FileNamingPolicy
from src.video_file_discovery import VideoFileDiscovery, VideoFile

logger = logging.getLogger(__name__)


@dataclass
class RenamingResult:
    """Result of a renaming operation."""
    original_path: Path
    new_path: Optional[Path]
    imdb_match: Optional[IMDBResult]
    status: str  # "success", "skipped", "error", "dry_run"
    error: Optional[str] = None
    is_file: bool = True


class FileRenamer:
    """Main orchestrator for file/folder discovery, matching, and renaming."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        interactive: bool = True
    ):
        """
        Initialize file renamer.
        
        Args:
            cache_dir: Directory for IMDB lookup cache
            interactive: Whether to use interactive mode (prompt for confirmation)
        """
        self.imdb_matcher = IMDBMatcher(cache_dir=cache_dir)
        self.naming_policy = FileNamingPolicy()
        self.file_discovery = VideoFileDiscovery()
        self.interactive = interactive
    
    def process_directory(
        self,
        directory: Path,
        dry_run: bool = False,
        rename_folders: bool = False,
        auto_confirm: bool = False
    ) -> List[RenamingResult]:
        """
        Process a directory: discover files, match to IMDB, and rename.
        
        Args:
            directory: Directory to process
            dry_run: If True, don't actually rename files
            rename_folders: If True, also rename parent folders if they match
            auto_confirm: If True, skip interactive prompts
            
        Returns:
            List of RenamingResult objects
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return []
        
        logger.info(f"Processing directory: {directory}")
        logger.info(f"  Dry run: {dry_run}")
        logger.info(f"  Rename folders: {rename_folders}")
        logger.info(f"  Auto confirm: {auto_confirm}")
        
        # Discover video files
        video_files = self.file_discovery.discover_video_files(directory, recursive=True)
        
        if not video_files:
            logger.info("No video files found")
            return []
        
        logger.info(f"Found {len(video_files)} video file(s) to process")
        
        results = []
        
        # Process each file
        for video_file in video_files:
            try:
                result = self._process_video_file(
                    video_file,
                    dry_run=dry_run,
                    auto_confirm=auto_confirm
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {video_file.file_path}: {e}", exc_info=True)
                results.append(RenamingResult(
                    original_path=video_file.file_path,
                    new_path=None,
                    imdb_match=None,
                    status="error",
                    error=str(e),
                    is_file=True
                ))
        
        # Optionally rename folders
        if rename_folders:
            folder_results = self._process_folders(results, dry_run=dry_run, auto_confirm=auto_confirm)
            results.extend(folder_results)
        
        return results
    
    def process_single_file(
        self,
        file_path: Path,
        dry_run: bool = False,
        auto_confirm: bool = False
    ) -> Optional[RenamingResult]:
        """
        Process a single video file.
        
        Args:
            file_path: Path to video file
            dry_run: If True, don't actually rename
            auto_confirm: If True, skip interactive prompts
            
        Returns:
            RenamingResult or None if file doesn't exist
        """
        video_file = self.file_discovery.discover_single_file(file_path)
        
        if not video_file:
            return None
        
        return self._process_video_file(video_file, dry_run=dry_run, auto_confirm=auto_confirm)
    
    def _process_video_file(
        self,
        video_file: VideoFile,
        dry_run: bool = False,
        auto_confirm: bool = False
    ) -> RenamingResult:
        """
        Process a single video file: match to IMDB and rename.
        
        Args:
            video_file: VideoFile object
            dry_run: If True, don't actually rename
            auto_confirm: If True, skip interactive prompts
            
        Returns:
            RenamingResult
        """
        file_path = video_file.file_path
        
        # Check if already has IMDB ID in filename
        if video_file.imdb_id:
            logger.info(f"File already has IMDB ID: {file_path.name}")
            # Could still verify it matches, but for now skip
            return RenamingResult(
                original_path=file_path,
                new_path=file_path,
                imdb_match=None,
                status="skipped",
                is_file=True
            )
        
        # Search IMDB
        imdb_result = self._search_imdb(video_file)
        
        if not imdb_result:
            logger.warning(f"No IMDB match found for: {video_file.current_name}")
            # Still generate new name without IMDB tag
            new_name = self.naming_policy.generate_filename(
                title=video_file.title or file_path.stem,
                year=video_file.year,
                imdb_id=None,
                extension=video_file.extension
            )
            new_path = file_path.parent / new_name
            
            # Check if renaming is needed
            if not self.naming_policy.should_rename(file_path.name, new_name):
                return RenamingResult(
                    original_path=file_path,
                    new_path=file_path,
                    imdb_match=None,
                    status="skipped",
                    is_file=True
                )
            
            # Confirm if interactive
            if not auto_confirm and self.interactive:
                if not self._confirm_rename(file_path, new_path, imdb_result):
                    return RenamingResult(
                        original_path=file_path,
                        new_path=None,
                        imdb_match=None,
                        status="skipped",
                        is_file=True
                    )
        else:
            # Generate new name with IMDB tag
            new_name = self.naming_policy.generate_filename(
                title=imdb_result.title,
                year=imdb_result.year,
                imdb_id=imdb_result.imdb_id,
                extension=video_file.extension
            )
            new_path = file_path.parent / new_name
            
            # Check if renaming is needed
            if not self.naming_policy.should_rename(file_path.name, new_name):
                return RenamingResult(
                    original_path=file_path,
                    new_path=file_path,
                    imdb_match=imdb_result,
                    status="skipped",
                    is_file=True
                )
            
            # Confirm if interactive
            if not auto_confirm and self.interactive:
                if not self._confirm_rename(file_path, new_path, imdb_result):
                    return RenamingResult(
                        original_path=file_path,
                        new_path=None,
                        imdb_match=imdb_result,
                        status="skipped",
                        is_file=True
                    )
        
        # Perform rename
        if dry_run:
            logger.info(f"[DRY RUN] Would rename: {file_path.name} -> {new_name}")
            return RenamingResult(
                original_path=file_path,
                new_path=new_path,
                imdb_match=imdb_result,
                status="dry_run",
                is_file=True
            )
        else:
            try:
                # Check if target already exists
                if new_path.exists():
                    logger.warning(f"Target already exists, skipping: {new_path}")
                    return RenamingResult(
                        original_path=file_path,
                        new_path=None,
                        imdb_match=imdb_result,
                        status="skipped",
                        error="Target file already exists",
                        is_file=True
                    )
                
                # Rename file
                file_path.rename(new_path)
                logger.info(f"Renamed: {file_path.name} -> {new_name}")
                
                return RenamingResult(
                    original_path=file_path,
                    new_path=new_path,
                    imdb_match=imdb_result,
                    status="success",
                    is_file=True
                )
            except Exception as e:
                logger.error(f"Error renaming {file_path}: {e}", exc_info=True)
                return RenamingResult(
                    original_path=file_path,
                    new_path=None,
                    imdb_match=imdb_result,
                    status="error",
                    error=str(e),
                    is_file=True
                )
    
    def _search_imdb(self, video_file: VideoFile) -> Optional[IMDBResult]:
        """
        Search IMDB for a video file.
        
        Args:
            video_file: VideoFile object
            
        Returns:
            IMDBResult if match found, None otherwise
        """
        if not video_file.title:
            logger.warning(f"Cannot search IMDB without title for: {video_file.file_path}")
            return None
        
        return self.imdb_matcher.search_imdb(
            title=video_file.title,
            year=video_file.year
        )
    
    def _confirm_rename(
        self,
        original_path: Path,
        new_path: Path,
        imdb_result: Optional[IMDBResult]
    ) -> bool:
        """
        Prompt user to confirm rename (interactive mode).
        
        Args:
            original_path: Original file path
            new_path: New file path
            imdb_result: IMDB match result (if any)
            
        Returns:
            True if user confirms, False otherwise
        """
        print(f"\nRename file?")
        print(f"  From: {original_path.name}")
        print(f"  To:   {new_path.name}")
        
        if imdb_result:
            print(f"  IMDB: {imdb_result.title} ({imdb_result.year}) [{imdb_result.imdb_id}]")
            if imdb_result.rating:
                print(f"  Rating: {imdb_result.rating}/10")
        
        response = input("  Proceed? [Y/n]: ").strip().lower()
        return response in ('', 'y', 'yes')
    
    def rename_folder(
        self,
        folder_path: Path,
        imdb_result: IMDBResult,
        dry_run: bool = False
    ) -> RenamingResult:
        """
        Rename a folder using IMDB metadata.
        
        Args:
            folder_path: Path to folder
            imdb_result: IMDB metadata
            dry_run: If True, don't actually rename
            
        Returns:
            RenamingResult
        """
        new_name = self.naming_policy.generate_foldername(
            title=imdb_result.title,
            year=imdb_result.year,
            imdb_id=imdb_result.imdb_id
        )
        new_path = folder_path.parent / new_name
        
        # Check if renaming is needed
        if not self.naming_policy.should_rename(folder_path.name, new_name):
            return RenamingResult(
                original_path=folder_path,
                new_path=folder_path,
                imdb_match=imdb_result,
                status="skipped",
                is_file=False
            )
        
        if dry_run:
            logger.info(f"[DRY RUN] Would rename folder: {folder_path.name} -> {new_name}")
            return RenamingResult(
                original_path=folder_path,
                new_path=new_path,
                imdb_match=imdb_result,
                status="dry_run",
                is_file=False
            )
        
        try:
            if new_path.exists():
                logger.warning(f"Target folder already exists, skipping: {new_path}")
                return RenamingResult(
                    original_path=folder_path,
                    new_path=None,
                    imdb_match=imdb_result,
                    status="skipped",
                    error="Target folder already exists",
                    is_file=False
                )
            
            folder_path.rename(new_path)
            logger.info(f"Renamed folder: {folder_path.name} -> {new_name}")
            
            return RenamingResult(
                original_path=folder_path,
                new_path=new_path,
                imdb_match=imdb_result,
                status="success",
                is_file=False
            )
        except Exception as e:
            logger.error(f"Error renaming folder {folder_path}: {e}", exc_info=True)
            return RenamingResult(
                original_path=folder_path,
                new_path=None,
                imdb_match=imdb_result,
                status="error",
                error=str(e),
                is_file=False
            )
    
    def _process_folders(
        self,
        file_results: List[RenamingResult],
        dry_run: bool = False,
        auto_confirm: bool = False
    ) -> List[RenamingResult]:
        """
        Process folders that contain renamed files.
        
        Groups files by parent folder and renames folders if all files
        in the folder have the same IMDB match.
        
        Args:
            file_results: Results from file processing
            dry_run: If True, don't actually rename
            auto_confirm: If True, skip interactive prompts
            
        Returns:
            List of RenamingResult for folders
        """
        # Group files by parent folder
        folder_groups: Dict[Path, List[RenamingResult]] = {}
        
        for result in file_results:
            if result.status in ("success", "dry_run") and result.new_path:
                parent = result.new_path.parent
                if parent not in folder_groups:
                    folder_groups[parent] = []
                folder_groups[parent].append(result)
        
        folder_results = []
        
        for folder_path, file_results_in_folder in folder_groups.items():
            # Check if all files in folder have the same IMDB match
            imdb_results = [r.imdb_match for r in file_results_in_folder if r.imdb_match]
            
            if not imdb_results:
                continue
            
            # Use the first IMDB result (assuming they're all the same)
            imdb_result = imdb_results[0]
            
            # Verify all matches are the same
            if not all(r.imdb_match and r.imdb_match.imdb_id == imdb_result.imdb_id 
                      for r in file_results_in_folder if r.imdb_match):
                logger.debug(f"Mixed IMDB matches in folder {folder_path}, skipping folder rename")
                continue
            
            # Rename folder
            result = self.rename_folder(folder_path, imdb_result, dry_run=dry_run)
            folder_results.append(result)
        
        return folder_results


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.file_renamer <directory>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    renamer = FileRenamer(interactive=False)
    
    results = renamer.process_directory(directory, dry_run=True)
    
    print(f"\nProcessed {len(results)} file(s)")
    print(f"  Success: {sum(1 for r in results if r.status == 'success')}")
    print(f"  Skipped: {sum(1 for r in results if r.status == 'skipped')}")
    print(f"  Errors:  {sum(1 for r in results if r.status == 'error')}")








