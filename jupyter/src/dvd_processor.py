#!/usr/bin/env python3
"""
DVD Processing Module - Module 1: The Ripper

Extracts all titles from DVD VIDEO_TS backups using MakeMKV (preferred) or FFmpeg (fallback).
Supports quality-preserving remuxing to MKV containers.
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DVDProcessor:
    """Module 1: Extracts DVD titles to MKV files using MakeMKV or FFmpeg."""
    
    def __init__(self, makemkv_path: str = "makemkvcon", ffmpeg_path: str = "ffmpeg"):
        """
        Initialize DVD processor.
        
        Args:
            makemkv_path: Path to makemkvcon executable
            ffmpeg_path: Path to ffmpeg executable
        """
        self.makemkv_path = makemkv_path
        self.ffmpeg_path = ffmpeg_path
        self.makemkv_available = self._check_makemkv_available()
        self.ffmpeg_available = self._check_ffmpeg_available()
        
        if not self.ffmpeg_available and not self.makemkv_available:
            raise RuntimeError(
                "Neither MakeMKV nor FFmpeg available. Please install at least one:\n"
                "  - FFmpeg: apt-get install ffmpeg (or system package manager)\n"
                "  - MakeMKV: See https://www.makemkv.com/download/"
            )
    
    def _check_makemkv_available(self) -> bool:
        """Check if MakeMKV is available."""
        try:
            result = subprocess.run(
                [self.makemkv_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def extract_titles_makemkv(
        self,
        video_ts_path: Path,
        output_dir: Path,
        min_length_seconds: int = 120
    ) -> List[Path]:
        """
        Extract all titles from VIDEO_TS using MakeMKV.
        
        Args:
            video_ts_path: Path to VIDEO_TS directory
            output_dir: Directory to output MKV files
            min_length_seconds: Minimum title length to extract (filters junk)
            
        Returns:
            List of paths to extracted MKV files
        """
        if not self.makemkv_available:
            raise RuntimeError("MakeMKV not available. Use extract_titles_ffmpeg() instead.")
        
        video_ts_path = Path(video_ts_path)
        output_dir = Path(output_dir)
        
        if not video_ts_path.exists():
            raise FileNotFoundError(f"VIDEO_TS directory not found: {video_ts_path}")
        
        if not video_ts_path.is_dir():
            raise ValueError(f"VIDEO_TS path must be a directory: {video_ts_path}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extracting titles from {video_ts_path} using MakeMKV...")
        logger.info(f"  Output directory: {output_dir}")
        logger.info(f"  Minimum length: {min_length_seconds} seconds")
        
        # MakeMKV file: protocol syntax
        # Format: makemkvcon mkv file:/path/to/VIDEO_TS all /output/dir --minlength=seconds
        cmd = [
            self.makemkv_path,
            "mkv",
            f"file:{video_ts_path}",
            "all",  # Extract all titles
            str(output_dir),
            f"--minlength={min_length_seconds}"
        ]
        
        try:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"MakeMKV failed: {result.stderr}")
                raise RuntimeError(f"MakeMKV extraction failed: {result.stderr}")
            
            # Find extracted MKV files
            mkv_files = sorted(output_dir.glob("*.mkv"))
            logger.info(f"Extracted {len(mkv_files)} titles")
            
            return mkv_files
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("MakeMKV extraction timed out (exceeded 1 hour)")
    
    def extract_titles_ffmpeg(
        self,
        video_ts_path: Path,
        output_dir: Path,
        min_length_seconds: int = 120
    ) -> List[Path]:
        """
        Extract titles from VIDEO_TS using FFmpeg (fallback method).
        
        This method processes VOB files directly. It's less elegant than MakeMKV
        but works when MakeMKV is unavailable.
        
        Args:
            video_ts_path: Path to VIDEO_TS directory
            output_dir: Directory to output MKV files
            min_length_seconds: Minimum title length (used for filtering after extraction)
            
        Returns:
            List of paths to extracted MKV files
        """
        if not self.ffmpeg_available:
            raise RuntimeError("FFmpeg not available. Cannot extract titles.")
        
        video_ts_path = Path(video_ts_path)
        output_dir = Path(output_dir)
        
        if not video_ts_path.exists():
            raise FileNotFoundError(f"VIDEO_TS directory not found: {video_ts_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extracting titles from {video_ts_path} using FFmpeg (fallback)...")
        logger.warning("FFmpeg method processes VOB files directly - may not handle all DVD structures perfectly")
        
        # Find VTS directories (VTS_01, VTS_02, etc.)
        vts_dirs = []
        for item in video_ts_path.iterdir():
            if item.name.startswith("VTS_") and item.is_dir():
                vts_dirs.append(item)
        
        if not vts_dirs:
            # Check if VOB files are directly in VIDEO_TS
            vob_files = list(video_ts_path.glob("*.VOB"))
            if vob_files:
                logger.info("Found VOB files directly in VIDEO_TS directory")
                # Group by VTS number
                vts_groups = {}
                for vob in vob_files:
                    # Extract VTS number from filename (e.g., VTS_01_1.VOB -> VTS_01)
                    parts = vob.stem.split("_")
                    if len(parts) >= 2:
                        vts_key = f"{parts[0]}_{parts[1]}"
                        if vts_key not in vts_groups:
                            vts_groups[vts_key] = []
                        vts_groups[vts_key].append(vob)
                
                extracted_files = []
                for vts_key, vobs in vts_groups.items():
                    # Sort VOB files by part number
                    vobs_sorted = sorted(vobs, key=lambda x: int(x.stem.split("_")[-1]) if x.stem.split("_")[-1].isdigit() else 999)
                    
                    if len(vobs_sorted) == 1:
                        # Single VOB file - simple remux
                        output_file = output_dir / f"{vts_key}.mkv"
                        self._remux_vob_ffmpeg(vobs_sorted[0], output_file)
                        extracted_files.append(output_file)
                    else:
                        # Multiple VOB files - concatenate
                        output_file = output_dir / f"{vts_key}.mkv"
                        self._concatenate_vobs_ffmpeg(vobs_sorted, output_file)
                        extracted_files.append(output_file)
                
                # Filter by minimum length
                return self._filter_by_duration(extracted_files, min_length_seconds)
        
        logger.warning("FFmpeg method: Direct VOB processing may not work for all DVD structures")
        logger.warning("Consider using MakeMKV for better results")
        raise NotImplementedError(
            "FFmpeg-based VOB extraction for complex DVD structures not fully implemented.\n"
            "Please install MakeMKV or manually process VOB files."
        )
    
    def _remux_vob_ffmpeg(self, vob_file: Path, output_file: Path) -> Path:
        """Remux a single VOB file to MKV using FFmpeg."""
        cmd = [
            self.ffmpeg_path,
            "-i", str(vob_file),
            "-c", "copy",  # Stream copy, no re-encoding
            "-f", "matroska",
            "-y",  # Overwrite
            str(output_file)
        ]
        
        logger.debug(f"Remuxing {vob_file.name} -> {output_file.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg remux failed: {result.stderr}")
        
        return output_file
    
    def _concatenate_vobs_ffmpeg(self, vob_files: List[Path], output_file: Path) -> Path:
        """
        Concatenate multiple VOB files into a single MKV.
        
        Uses FFmpeg with proper VOB handling to strip navigation packets.
        """
        # For VOB files, we need to use a different approach - process each VOB
        # and then concatenate the streams, or use copyts to preserve timestamps
        
        # Create concat file for FFmpeg with proper format
        concat_file = output_file.parent / f"{output_file.stem}_concat.txt"
        
        with open(concat_file, "w") as f:
            for vob in vob_files:
                # Use absolute path and escape properly
                vob_path = str(vob.resolve())
                f.write(f"file '{vob_path}'\n")
        
        # Use FFmpeg with copyts and proper VOB handling
        # The -fflags +genpts generates presentation timestamps for VOB streams
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-fflags", "+genpts",  # Generate presentation timestamps
            "-i", str(concat_file),
            "-c", "copy",  # Stream copy, no re-encoding
            "-f", "matroska",
            "-y",
            str(output_file)
        ]
        
        logger.debug(f"Concatenating {len(vob_files)} VOB files -> {output_file.name}")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        # Clean up concat file
        concat_file.unlink(missing_ok=True)
        
        if result.returncode != 0:
            # If concat fails, try alternative: process first VOB as main and append others
            logger.warning("Standard concat failed, trying alternative VOB processing method")
            return self._process_vobs_alternative(vob_files, output_file)
        
        return output_file
    
    def _process_vobs_alternative(self, vob_files: List[Path], output_file: Path) -> Path:
        """
        Alternative VOB processing: process VOBs individually then merge.
        
        This is a workaround for VOB files with navigation packets.
        """
        logger.warning("Using alternative VOB processing (may be slower)")
        
        # Process first VOB
        temp_dir = output_file.parent / "temp_vobs"
        temp_dir.mkdir(exist_ok=True)
        
        temp_mkvs = []
        for i, vob in enumerate(vob_files):
            temp_mkv = temp_dir / f"part_{i:03d}.mkv"
            
            # Process individual VOB, stripping navigation
            cmd = [
                self.ffmpeg_path,
                "-i", str(vob),
                "-map", "0:v",  # Map video stream
                "-map", "0:a",  # Map audio stream
                "-c", "copy",
                "-f", "matroska",
                "-y",
                str(temp_mkv)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and temp_mkv.exists():
                temp_mkvs.append(temp_mkv)
            else:
                logger.warning(f"Failed to process {vob.name}: {result.stderr[:200]}")
        
        if not temp_mkvs:
            raise RuntimeError("Failed to process any VOB files")
        
        # Concatenate the processed MKV files
        if len(temp_mkvs) == 1:
            shutil.move(str(temp_mkvs[0]), str(output_file))
        else:
            concat_file = temp_dir / "concat.txt"
            with open(concat_file, "w") as f:
                for mkv in temp_mkvs:
                    f.write(f"file '{mkv.resolve()}'\n")
            
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-f", "matroska",
                "-y",
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            concat_file.unlink(missing_ok=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to concatenate processed VOBs: {result.stderr}")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return output_file
    
    def _filter_by_duration(
        self,
        mkv_files: List[Path],
        min_length_seconds: int
    ) -> List[Path]:
        """Filter MKV files by minimum duration using ffprobe."""
        from src.video_remuxer import VideoRemuxer
        
        remuxer = VideoRemuxer(ffmpeg_path=self.ffmpeg_path)
        filtered = []
        
        for mkv_file in mkv_files:
            try:
                info = remuxer.get_video_info(mkv_file)
                if info.duration >= min_length_seconds:
                    filtered.append(mkv_file)
                else:
                    logger.info(f"Skipping {mkv_file.name} (duration: {info.duration:.1f}s < {min_length_seconds}s)")
            except Exception as e:
                logger.warning(f"Could not get duration for {mkv_file.name}: {e}")
                # Include it anyway if we can't check
                filtered.append(mkv_file)
        
        return filtered
    
    def extract_titles(
        self,
        video_ts_path: Path,
        output_dir: Path,
        min_length_seconds: int = 120,
        prefer_makemkv: bool = True
    ) -> List[Path]:
        """
        Extract titles using best available method.
        
        Args:
            video_ts_path: Path to VIDEO_TS directory
            output_dir: Directory to output MKV files
            min_length_seconds: Minimum title length to extract
            prefer_makemkv: Prefer MakeMKV if available
            
        Returns:
            List of paths to extracted MKV files
        """
        if prefer_makemkv and self.makemkv_available:
            try:
                return self.extract_titles_makemkv(video_ts_path, output_dir, min_length_seconds)
            except Exception as e:
                logger.warning(f"MakeMKV extraction failed: {e}")
                logger.info("Falling back to FFmpeg method...")
        
        if self.ffmpeg_available:
            return self.extract_titles_ffmpeg(video_ts_path, output_dir, min_length_seconds)
        
        raise RuntimeError("No extraction method available")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    processor = DVDProcessor()
    print(f"MakeMKV available: {processor.makemkv_available}")
    print(f"FFmpeg available: {processor.ffmpeg_available}")

