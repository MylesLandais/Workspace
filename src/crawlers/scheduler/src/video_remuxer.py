#!/usr/bin/env python3
"""
Video Remuxing Engine

This module provides functionality for remuxing video files with subtitle embedding
using FFmpeg. Supports various input formats and outputs to .mkv containers.
"""

import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Information about a video file."""
    duration: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: Optional[str]
    bitrate: Optional[int]
    file_size: int
    format_name: str


@dataclass
class RemuxJob:
    """Represents a video remuxing job."""
    input_video: Path
    output_video: Path
    subtitle_files: List[Path]
    audio_extract: Optional[Path] = None
    preserve_quality: bool = True
    custom_options: Optional[Dict[str, Any]] = None


class VideoRemuxer:
    """Handles video remuxing operations using FFmpeg."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize VideoRemuxer.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable
            ffprobe_path: Path to ffprobe executable
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        
        # Verify FFmpeg is available
        if not self._check_ffmpeg_available():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and ensure it's in PATH.")
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run([self.ffmpeg_path, "-version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_video_info(self, video_path: Union[str, Path]) -> VideoInfo:
        """
        Get detailed information about a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoInfo object with file details
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Use ffprobe to get video information
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            audio_stream = None
            
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video" and video_stream is None:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and audio_stream is None:
                    audio_stream = stream
            
            if not video_stream:
                raise ValueError("No video stream found in file")
            
            # Parse video information
            duration = float(data["format"].get("duration", 0))
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            
            # Calculate FPS
            fps_str = video_stream.get("r_frame_rate", "0/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) != 0 else 0
            else:
                fps = float(fps_str)
            
            video_codec = video_stream.get("codec_name", "unknown")
            audio_codec = audio_stream.get("codec_name") if audio_stream else None
            bitrate = int(data["format"].get("bit_rate", 0)) if data["format"].get("bit_rate") else None
            file_size = int(data["format"].get("size", 0))
            format_name = data["format"].get("format_name", "unknown")
            
            return VideoInfo(
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                video_codec=video_codec,
                audio_codec=audio_codec,
                bitrate=bitrate,
                file_size=file_size,
                format_name=format_name
            )
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffprobe timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse ffprobe output: {e}")
    
    def extract_audio(self, video_path: Union[str, Path], 
                     output_path: Union[str, Path],
                     audio_format: str = "wav") -> Path:
        """
        Extract audio from video file.
        
        Args:
            video_path: Input video file
            output_path: Output audio file path
            audio_format: Output audio format (wav, mp3, flac, etc.)
            
        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command for audio extraction
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le" if audio_format == "wav" else "copy",
            "-ar", "16000",  # 16kHz sample rate for ASR
            "-ac", "1",      # Mono
            "-y",            # Overwrite output
            str(output_path)
        ]
        
        logger.info(f"Extracting audio: {video_path.name} -> {output_path.name}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RuntimeError(f"Audio extraction failed: {result.stderr}")
            
            if not output_path.exists():
                raise RuntimeError("Audio extraction completed but output file not found")
            
            logger.info(f"Audio extracted successfully: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio extraction timed out")
    
    def remux_with_subtitles(self, remux_job: RemuxJob) -> Path:
        """
        Remux video with embedded subtitles.
        
        Args:
            remux_job: RemuxJob configuration
            
        Returns:
            Path to output video file
        """
        input_video = remux_job.input_video
        output_video = remux_job.output_video
        subtitle_files = remux_job.subtitle_files
        
        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")
        
        # Create output directory
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command
        cmd = [self.ffmpeg_path, "-i", str(input_video)]
        
        # Add subtitle inputs
        for subtitle_file in subtitle_files:
            if subtitle_file.exists():
                cmd.extend(["-i", str(subtitle_file)])
            else:
                logger.warning(f"Subtitle file not found: {subtitle_file}")
        
        # Video and audio codec options
        if remux_job.preserve_quality:
            cmd.extend(["-c:v", "copy"])  # Copy video stream without re-encoding
            cmd.extend(["-c:a", "copy"])  # Copy audio stream without re-encoding
        else:
            # Re-encode with reasonable quality
            cmd.extend(["-c:v", "libx264", "-crf", "23"])
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        
        # Subtitle mapping and options
        subtitle_count = len([f for f in subtitle_files if f.exists()])
        for i in range(subtitle_count):
            cmd.extend(["-map", f"{i+1}:0"])  # Map subtitle streams
            cmd.extend([f"-c:s:{i}", "ass"])  # Use ASS codec for subtitles
        
        # Map video and audio from input
        cmd.extend(["-map", "0:v:0"])  # Map first video stream
        cmd.extend(["-map", "0:a:0"])  # Map first audio stream
        
        # Output options
        cmd.extend(["-f", "matroska"])  # Use Matroska container (.mkv)
        cmd.extend(["-y"])  # Overwrite output
        
        # Add custom options if provided
        if remux_job.custom_options:
            for key, value in remux_job.custom_options.items():
                cmd.extend([key, str(value)])
        
        cmd.append(str(output_video))
        
        logger.info(f"Remuxing video: {input_video.name} -> {output_video.name}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise RuntimeError(f"Video remuxing failed: {result.stderr}")
            
            if not output_video.exists():
                raise RuntimeError("Remuxing completed but output file not found")
            
            logger.info(f"Video remuxed successfully: {output_video}")
            return output_video
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Video remuxing timed out")
    
    def remux_without_subtitles(self, input_video: Union[str, Path], 
                              output_video: Union[str, Path],
                              preserve_quality: bool = True) -> Path:
        """
        Remux video to .mkv format without subtitles (format conversion only).
        
        Args:
            input_video: Input video file
            output_video: Output video file (.mkv)
            preserve_quality: Whether to preserve original quality
            
        Returns:
            Path to output video file
        """
        input_video = Path(input_video)
        output_video = Path(output_video)
        
        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")
        
        # Create output directory
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command for format conversion
        cmd = [
            self.ffmpeg_path,
            "-i", str(input_video)
        ]
        
        if preserve_quality:
            cmd.extend(["-c", "copy"])  # Copy all streams without re-encoding
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "23"])
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        
        cmd.extend([
            "-f", "matroska",  # Output to Matroska container
            "-y",              # Overwrite output
            str(output_video)
        ])
        
        logger.info(f"Converting video format: {input_video.name} -> {output_video.name}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise RuntimeError(f"Video conversion failed: {result.stderr}")
            
            if not output_video.exists():
                raise RuntimeError("Conversion completed but output file not found")
            
            logger.info(f"Video converted successfully: {output_video}")
            return output_video
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Video conversion timed out")
    
    def batch_remux(self, input_dir: Union[str, Path], 
                   output_dir: Union[str, Path],
                   subtitle_dir: Optional[Union[str, Path]] = None,
                   video_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """
        Batch remux multiple video files.
        
        Args:
            input_dir: Directory containing input videos
            output_dir: Directory for output videos
            subtitle_dir: Directory containing subtitle files (optional)
            video_extensions: List of video file extensions to process
            
        Returns:
            List of processing results
        """
        if video_extensions is None:
            video_extensions = ['.wmv', '.avi', '.mp4', '.mov', '.mkv', '.flv']
        
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        subtitle_dir = Path(subtitle_dir) if subtitle_dir else None
        
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all video files
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_dir.rglob(f"*{ext}"))
            video_files.extend(input_dir.rglob(f"*{ext.upper()}"))
        
        results = []
        
        for video_file in video_files:
            try:
                # Generate output filename
                output_file = output_dir / f"{video_file.stem}.mkv"
                
                # Look for subtitle files
                subtitle_files = []
                if subtitle_dir:
                    for ext in ['.ass', '.srt', '.vtt']:
                        subtitle_file = subtitle_dir / f"{video_file.stem}{ext}"
                        if subtitle_file.exists():
                            subtitle_files.append(subtitle_file)
                
                # Create remux job
                if subtitle_files:
                    remux_job = RemuxJob(
                        input_video=video_file,
                        output_video=output_file,
                        subtitle_files=subtitle_files
                    )
                    result_file = self.remux_with_subtitles(remux_job)
                else:
                    result_file = self.remux_without_subtitles(video_file, output_file)
                
                results.append({
                    'input_file': str(video_file),
                    'output_file': str(result_file),
                    'subtitle_files': [str(f) for f in subtitle_files],
                    'status': 'success'
                })
                
            except Exception as e:
                logger.error(f"Failed to process {video_file}: {e}")
                results.append({
                    'input_file': str(video_file),
                    'output_file': None,
                    'subtitle_files': [],
                    'status': 'error',
                    'error': str(e)
                })
        
        return results


def main():
    """Example usage of VideoRemuxer."""
    remuxer = VideoRemuxer()
    
    # Example: Get video info
    try:
        video_path = Path("example.wmv")
        if video_path.exists():
            info = remuxer.get_video_info(video_path)
            print(f"Video Info: {info}")
        else:
            print("No example video file found")
    except Exception as e:
        print(f"Error getting video info: {e}")
    
    # Example: Extract audio
    try:
        if video_path.exists():
            audio_path = remuxer.extract_audio(video_path, "output/audio.wav")
            print(f"Audio extracted to: {audio_path}")
    except Exception as e:
        print(f"Error extracting audio: {e}")
    
    # Example: Remux without subtitles
    try:
        if video_path.exists():
            output_path = remuxer.remux_without_subtitles(
                video_path, 
                "output/remuxed.mkv"
            )
            print(f"Video remuxed to: {output_path}")
    except Exception as e:
        print(f"Error remuxing video: {e}")


if __name__ == "__main__":
    main()