#!/usr/bin/env python3
"""
Subtitle Sync and MKV Muxing System
Synchronizes optimized transcripts with video timing and muxes subtitles into MKV containers.
"""

import os
import sys
import json
import time
import subprocess
import warnings
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.video_remuxer import VideoRemuxer

@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry with timing and text"""
    start_time: float
    end_time: float
    text: str
    index: int
    confidence: Optional[float] = None

class SubtitleFormatter:
    """Formats subtitles in various formats (SRT, VTT, ASS)"""

    @staticmethod
    def seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    @staticmethod
    def seconds_to_vtt_time(seconds: float) -> str:
        """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

    def generate_srt(self, entries: List[SubtitleEntry]) -> str:
        """Generate SRT format subtitles"""
        srt_content = []
        for entry in entries:
            start_time = self.seconds_to_srt_time(entry.start_time)
            end_time = self.seconds_to_srt_time(entry.end_time)

            srt_content.append(f"{entry.index}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(entry.text)
            srt_content.append("")  # Empty line between entries

        return "\n".join(srt_content)

    def generate_vtt(self, entries: List[SubtitleEntry]) -> str:
        """Generate WebVTT format subtitles"""
        vtt_content = ["WEBVTT", ""]

        for entry in entries:
            start_time = self.seconds_to_vtt_time(entry.start_time)
            end_time = self.seconds_to_vtt_time(entry.end_time)

            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(entry.text)
            vtt_content.append("")

        return "\n".join(vtt_content)

class SubtitleSynchronizer:
    """Synchronizes transcript segments with video timing"""

    def __init__(self, max_subtitle_length: int = 80, min_duration: float = 1.0, max_duration: float = 6.0):
        """
        Initialize synchronizer with timing constraints.

        Args:
            max_subtitle_length: Maximum characters per subtitle line
            min_duration: Minimum subtitle display duration in seconds
            max_duration: Maximum subtitle display duration in seconds
        """
        self.max_subtitle_length = max_subtitle_length
        self.min_duration = min_duration
        self.max_duration = max_duration

    def split_long_text(self, text: str, max_length: int) -> List[str]:
        """Split long text into readable chunks"""
        if len(text) <= max_length:
            return [text]

        # Try to split at sentence boundaries first
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add period back if it was removed (except for last sentence)
            if not sentence.endswith('.') and sentence != sentences[-1]:
                sentence += '.'

            test_chunk = current_chunk + (" " if current_chunk else "") + sentence

            if len(test_chunk) <= max_length:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        # If still too long, split by words
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= max_length:
                final_chunks.append(chunk)
            else:
                words = chunk.split()
                current_word_chunk = ""

                for word in words:
                    test_chunk = current_word_chunk + (" " if current_word_chunk else "") + word
                    if len(test_chunk) <= max_length:
                        current_word_chunk = test_chunk
                    else:
                        if current_word_chunk:
                            final_chunks.append(current_word_chunk)
                        current_word_chunk = word

                if current_word_chunk:
                    final_chunks.append(current_word_chunk)

        return final_chunks

    def optimize_timing(self, entries: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """Optimize subtitle timing for better readability"""
        optimized = []

        for i, entry in enumerate(entries):
            duration = entry.end_time - entry.start_time

            # Ensure minimum duration
            if duration < self.min_duration:
                # Extend end time, but don't overlap with next subtitle
                new_end_time = entry.start_time + self.min_duration
                if i + 1 < len(entries):
                    new_end_time = min(new_end_time, entries[i + 1].start_time - 0.1)
                entry.end_time = new_end_time

            # Limit maximum duration
            elif duration > self.max_duration:
                entry.end_time = entry.start_time + self.max_duration

            optimized.append(entry)

        return optimized

    def create_subtitles_from_segments(self, segments_data: Dict) -> List[SubtitleEntry]:
        """Create optimized subtitle entries from transcript segments"""
        segments = segments_data.get("segments", [])
        entries = []
        index = 1

        print(f"📝 Processing {len(segments)} transcript segments...")

        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue

            start_time = segment.get("start_time", 0.0)
            end_time = segment.get("end_time", start_time + 2.0)
            confidence = segment.get("confidence")

            # Split long text into multiple subtitles
            text_chunks = self.split_long_text(text, self.max_subtitle_length)

            if len(text_chunks) == 1:
                # Single subtitle
                entries.append(SubtitleEntry(
                    start_time=start_time,
                    end_time=end_time,
                    text=text_chunks[0],
                    index=index,
                    confidence=confidence
                ))
                index += 1
            else:
                # Multiple subtitles - distribute timing
                segment_duration = end_time - start_time
                chunk_duration = segment_duration / len(text_chunks)

                for i, chunk in enumerate(text_chunks):
                    chunk_start = start_time + (i * chunk_duration)
                    chunk_end = start_time + ((i + 1) * chunk_duration)

                    entries.append(SubtitleEntry(
                        start_time=chunk_start,
                        end_time=chunk_end,
                        text=chunk,
                        index=index,
                        confidence=confidence
                    ))
                    index += 1

        # Optimize timing
        entries = self.optimize_timing(entries)

        print(f"✅ Created {len(entries)} optimized subtitle entries")
        return entries

class MKVMuxer:
    """Handles MKV container creation and subtitle muxing"""

    def __init__(self, mkvmerge_path: str = "mkvmerge"):
        """
        Initialize MKV muxer.

        Args:
            mkvmerge_path: Path to mkvmerge executable
        """
        self.mkvmerge_path = mkvmerge_path
        self._check_mkvmerge_available()

    def _check_mkvmerge_available(self) -> bool:
        """Check if mkvmerge is available"""
        try:
            result = subprocess.run([self.mkvmerge_path, "--version"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ MKVToolNix available: {result.stdout.split()[1]}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        raise RuntimeError("mkvmerge not found. Please install MKVToolNix.")

    def mux_video_with_subtitles(self, video_path: Path, subtitle_path: Path,
                                output_path: Path, subtitle_language: str = "eng",
                                subtitle_name: str = "English") -> bool:
        """
        Mux video with subtitle track into MKV container.

        Args:
            video_path: Source video file
            subtitle_path: Subtitle file (.srt)
            output_path: Output MKV file
            subtitle_language: Language code for subtitle track
            subtitle_name: Display name for subtitle track

        Returns:
            True if successful, False otherwise
        """
        print(f"🎬 Muxing video with subtitles...")
        print(f"   📹 Video: {video_path.name}")
        print(f"   📝 Subtitles: {subtitle_path.name}")
        print(f"   🎯 Output: {output_path.name}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build mkvmerge command
        cmd = [
            self.mkvmerge_path,
            "--output", str(output_path),
            "--language", f"0:{subtitle_language}",
            "--track-name", f"0:{subtitle_name}",
            "--default-track", "0:yes",
            str(subtitle_path),
            str(video_path)
        ]

        try:
            print("⏳ Running mkvmerge...")
            start_time = time.time()

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            mux_time = time.time() - start_time

            if result.returncode == 0:
                output_size = output_path.stat().st_size / (1024 * 1024)
                print(f"✅ MKV muxing completed in {mux_time:.1f}s")
                print(f"   📦 Output size: {output_size:.1f}MB")
                return True
            else:
                print(f"❌ MKV muxing failed:")
                print(f"   Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ MKV muxing timed out")
            return False
        except Exception as e:
            print(f"❌ MKV muxing error: {e}")
            return False

def sync_and_mux_subtitles(video_path: Path, segments_path: Path, output_dir: Path,
                          subtitle_formats: List[str] = ["srt"], create_mkv: bool = True):
    """
    Complete subtitle synchronization and MKV muxing workflow.

    Args:
        video_path: Source video file
        segments_path: JSON file with transcript segments
        output_dir: Output directory for generated files
        subtitle_formats: List of subtitle formats to generate
        create_mkv: Whether to create MKV with embedded subtitles
    """
    print("🎯 SUBTITLE SYNC AND MKV MUXING WORKFLOW")
    print("=" * 60)
    print(f"📹 Video: {video_path.name}")
    print(f"📋 Segments: {segments_path.name}")
    print(f"📁 Output: {output_dir}")
    print(f"📝 Formats: {', '.join(subtitle_formats)}")
    print(f"🎬 Create MKV: {'Yes' if create_mkv else 'No'}")
    print("=" * 60)

    # Validate inputs
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return False

    if not segments_path.exists():
        print(f"❌ Segments file not found: {segments_path}")
        return False

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load segments data
    try:
        with open(segments_path, 'r', encoding='utf-8') as f:
            segments_data = json.load(f)
        print(f"✅ Loaded transcript segments: {len(segments_data.get('segments', []))} segments")
    except Exception as e:
        print(f"❌ Failed to load segments: {e}")
        return False

    # Step 1: Create synchronized subtitles
    print(f"\n🔄 Step 1: Creating Synchronized Subtitles")
    try:
        synchronizer = SubtitleSynchronizer()
        subtitle_entries = synchronizer.create_subtitles_from_segments(segments_data)

        if not subtitle_entries:
            print("❌ No subtitle entries created")
            return False

    except Exception as e:
        print(f"❌ Subtitle synchronization failed: {e}")
        return False

    # Step 2: Generate subtitle files
    print(f"\n📝 Step 2: Generating Subtitle Files")
    formatter = SubtitleFormatter()
    subtitle_files = {}

    base_name = video_path.stem

    for format_type in subtitle_formats:
        try:
            if format_type.lower() == "srt":
                content = formatter.generate_srt(subtitle_entries)
                subtitle_path = output_dir / f"{base_name}.srt"
            elif format_type.lower() == "vtt":
                content = formatter.generate_vtt(subtitle_entries)
                subtitle_path = output_dir / f"{base_name}.vtt"
            else:
                print(f"⚠️  Unsupported subtitle format: {format_type}")
                continue

            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(content)

            subtitle_files[format_type] = subtitle_path
            print(f"✅ Generated {format_type.upper()}: {subtitle_path.name}")

        except Exception as e:
            print(f"❌ Failed to generate {format_type} file: {e}")

    if not subtitle_files:
        print("❌ No subtitle files were generated")
        return False

    # Step 3: Create MKV with embedded subtitles
    if create_mkv and "srt" in subtitle_files:
        print(f"\n🎬 Step 3: Creating MKV with Embedded Subtitles")
        try:
            muxer = MKVMuxer()
            mkv_output = output_dir / f"{base_name}_with_subtitles.mkv"

            success = muxer.mux_video_with_subtitles(
                video_path=video_path,
                subtitle_path=subtitle_files["srt"],
                output_path=mkv_output,
                subtitle_language="eng",
                subtitle_name="English"
            )

            if success:
                print(f"✅ MKV created: {mkv_output.name}")
            else:
                print(f"❌ MKV creation failed")
                return False

        except Exception as e:
            print(f"❌ MKV muxing error: {e}")
            return False

    # Final summary
    print(f"\n" + "=" * 60)
    print("🎉 SUBTITLE SYNC AND MUXING COMPLETED")
    print("=" * 60)
    print(f"📊 Statistics:")
    print(f"   📝 Subtitle entries: {len(subtitle_entries)}")
    print(f"   📄 Files generated: {len(subtitle_files)}")
    if create_mkv and "srt" in subtitle_files:
        print(f"   🎬 MKV with subtitles: ✅")

    print(f"\n📁 Output files:")
    for format_type, path in subtitle_files.items():
        print(f"   📝 {format_type.upper()}: {path}")

    if create_mkv and "srt" in subtitle_files:
        mkv_path = output_dir / f"{base_name}_with_subtitles.mkv"
        if mkv_path.exists():
            print(f"   🎬 MKV: {mkv_path}")

    return True

def main():
    """Main execution function"""

    # Configuration
    VIDEO_PATH = Path("Datasets/.princesslexiexo/hooters-girl-revenge.wmv")
    SEGMENTS_PATH = Path("outputs/optimized_transcripts/hooters-girl-revenge_segments.json")
    OUTPUT_DIR = Path("outputs/subtitled_videos")

    # Subtitle options
    SUBTITLE_FORMATS = ["srt", "vtt"]  # Formats to generate
    CREATE_MKV = True  # Whether to create MKV with embedded subtitles

    print("🎬 SUBTITLE SYNCHRONIZATION AND MKV MUXING SYSTEM")
    print("=" * 70)

    # Check prerequisites
    print("🔍 Checking Prerequisites:")

    # Check if segments file exists (should be created by optimized transcript generator)
    if not SEGMENTS_PATH.exists():
        print(f"❌ Segments file not found: {SEGMENTS_PATH}")
        print("💡 Please run Gen-CleanTranscript-Optimized.py first to generate segments")
        return

    print(f"✅ Video file: {VIDEO_PATH.name}")
    print(f"✅ Segments file: {SEGMENTS_PATH.name}")

    # Run the complete workflow
    success = sync_and_mux_subtitles(
        video_path=VIDEO_PATH,
        segments_path=SEGMENTS_PATH,
        output_dir=OUTPUT_DIR,
        subtitle_formats=SUBTITLE_FORMATS,
        create_mkv=CREATE_MKV
    )

    if success:
        print("\n🎉 All operations completed successfully!")
        print("🎬 Your video now has synchronized subtitles!")
    else:
        print("\n❌ Some operations failed. Check the output above for details.")

if __name__ == "__main__":
    main()
