#!/usr/bin/env python3
"""
Subtitle Processing Module

This module provides functionality for generating timed subtitle files from transcription data.
Supports multiple subtitle formats including .ass, .srt, and .vtt.
"""

import re
import math
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import timedelta


@dataclass
class TimedSegment:
    """Represents a timed segment of audio/video with transcription."""
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    text: str          # Transcribed text
    confidence: Optional[float] = None  # Confidence score (0.0-1.0)
    speaker: Optional[str] = None       # Speaker identification
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


@dataclass
class SubtitleSegment:
    """Represents a subtitle segment with formatting information."""
    start_time: float
    end_time: float
    text: str
    style: Optional[str] = None  # Style name for .ass format
    position: Optional[Dict[str, Any]] = None  # Position/alignment info
    effects: Optional[List[str]] = None  # Visual effects


class SubtitleProcessor:
    """Processes transcription data into timed subtitle files."""
    
    def __init__(self, max_chars_per_line: int = 50, max_lines_per_subtitle: int = 2,
                 min_duration: float = 1.0, max_duration: float = 6.0):
        """
        Initialize subtitle processor.
        
        Args:
            max_chars_per_line: Maximum characters per subtitle line
            max_lines_per_subtitle: Maximum lines per subtitle
            min_duration: Minimum subtitle duration in seconds
            max_duration: Maximum subtitle duration in seconds
        """
        self.max_chars_per_line = max_chars_per_line
        self.max_lines_per_subtitle = max_lines_per_subtitle
        self.min_duration = min_duration
        self.max_duration = max_duration
        
        # Default ASS styles
        self.ass_styles = {
            'Default': {
                'fontname': 'Arial',
                'fontsize': 20,
                'primarycolor': '&H00FFFFFF',  # White
                'secondarycolor': '&H000000FF',  # Red
                'outlinecolor': '&H00000000',   # Black
                'backcolor': '&H80000000',      # Semi-transparent black
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'strikeout': 0,
                'scalex': 100,
                'scaley': 100,
                'spacing': 0,
                'angle': 0,
                'borderstyle': 1,
                'outline': 2,
                'shadow': 2,
                'alignment': 2,  # Bottom center
                'marginl': 10,
                'marginr': 10,
                'marginv': 10,
                'encoding': 1
            }
        }
    
    def create_timed_segments_from_transcript(self, transcript: str, 
                                            audio_duration: float) -> List[TimedSegment]:
        """
        Create timed segments from a plain transcript by estimating timing.
        
        Args:
            transcript: Plain text transcript
            audio_duration: Total audio duration in seconds
            
        Returns:
            List of timed segments with estimated timing
        """
        # Split transcript into sentences
        sentences = self._split_into_sentences(transcript)
        
        if not sentences:
            return []
        
        # Estimate timing based on character count and speaking rate
        # Average speaking rate: ~150 words per minute or ~2.5 words per second
        # Average word length: ~5 characters
        # So roughly 12.5 characters per second
        
        segments = []
        current_time = 0.0
        total_chars = sum(len(sentence) for sentence in sentences)
        
        for sentence in sentences:
            # Calculate duration based on character count
            char_ratio = len(sentence) / total_chars if total_chars > 0 else 0
            estimated_duration = audio_duration * char_ratio
            
            # Apply min/max duration constraints
            duration = max(self.min_duration, min(self.max_duration, estimated_duration))
            
            # Ensure we don't exceed total duration
            if current_time + duration > audio_duration:
                duration = audio_duration - current_time
            
            if duration > 0:
                segment = TimedSegment(
                    start_time=current_time,
                    end_time=current_time + duration,
                    text=sentence.strip(),
                    confidence=0.5,  # Estimated timing has lower confidence
                    metadata={'estimated_timing': True}
                )
                segments.append(segment)
                current_time += duration
            
            if current_time >= audio_duration:
                break
        
        return segments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for subtitle timing."""
        # Clean up the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        
        # Filter out empty sentences and clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If no sentence boundaries found, split by length
        if len(sentences) <= 1 and text:
            # Split long text into chunks
            words = text.split()
            sentences = []
            current_sentence = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 > self.max_chars_per_line * self.max_lines_per_subtitle:
                    if current_sentence:
                        sentences.append(' '.join(current_sentence))
                        current_sentence = [word]
                        current_length = len(word)
                    else:
                        # Single word is too long, add it anyway
                        sentences.append(word)
                        current_length = 0
                else:
                    current_sentence.append(word)
                    current_length += len(word) + 1
            
            if current_sentence:
                sentences.append(' '.join(current_sentence))
        
        return sentences
    
    def create_subtitle_segments(self, timed_segments: List[TimedSegment]) -> List[SubtitleSegment]:
        """
        Convert timed segments into subtitle segments with proper formatting.
        
        Args:
            timed_segments: List of timed segments from ASR
            
        Returns:
            List of formatted subtitle segments
        """
        subtitle_segments = []
        
        for segment in timed_segments:
            # Split long text into multiple lines
            lines = self._wrap_text(segment.text)
            
            # Create subtitle segment
            subtitle_segment = SubtitleSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text='\\N'.join(lines),  # ASS format line break
                style='Default'
            )
            
            subtitle_segments.append(subtitle_segment)
        
        return subtitle_segments
    
    def _wrap_text(self, text: str) -> List[str]:
        """Wrap text to fit subtitle constraints."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > self.max_chars_per_line:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)
                    current_length = 0
            else:
                current_line.append(word)
                current_length += len(word) + 1
            
            # Check if we've reached max lines
            if len(lines) >= self.max_lines_per_subtitle:
                break
        
        if current_line and len(lines) < self.max_lines_per_subtitle:
            lines.append(' '.join(current_line))
        
        return lines
    
    def format_time_ass(self, seconds: float) -> str:
        """Format time for ASS subtitle format (H:MM:SS.CC)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        centiseconds = int((secs % 1) * 100)
        secs = int(secs)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def format_time_srt(self, seconds: float) -> str:
        """Format time for SRT subtitle format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        milliseconds = int((secs % 1) * 1000)
        secs = int(secs)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def generate_ass_subtitle(self, subtitle_segments: List[SubtitleSegment], 
                            title: str = "Generated Subtitles") -> str:
        """
        Generate ASS format subtitle content.
        
        Args:
            subtitle_segments: List of subtitle segments
            title: Title for the subtitle file
            
        Returns:
            ASS format subtitle content as string
        """
        lines = []
        
        # ASS Header
        lines.append("[Script Info]")
        lines.append(f"Title: {title}")
        lines.append("ScriptType: v4.00+")
        lines.append("WrapStyle: 0")
        lines.append("ScaledBorderAndShadow: yes")
        lines.append("YCbCr Matrix: TV.601")
        lines.append("")
        
        # Styles section
        lines.append("[V4+ Styles]")
        lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
        
        for style_name, style in self.ass_styles.items():
            style_line = f"Style: {style_name},{style['fontname']},{style['fontsize']},{style['primarycolor']},{style['secondarycolor']},{style['outlinecolor']},{style['backcolor']},{style['bold']},{style['italic']},{style['underline']},{style['strikeout']},{style['scalex']},{style['scaley']},{style['spacing']},{style['angle']},{style['borderstyle']},{style['outline']},{style['shadow']},{style['alignment']},{style['marginl']},{style['marginr']},{style['marginv']},{style['encoding']}"
            lines.append(style_line)
        
        lines.append("")
        
        # Events section
        lines.append("[Events]")
        lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
        
        for i, segment in enumerate(subtitle_segments):
            start_time = self.format_time_ass(segment.start_time)
            end_time = self.format_time_ass(segment.end_time)
            style = segment.style or 'Default'
            text = segment.text.replace('\n', '\\N')
            
            event_line = f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{text}"
            lines.append(event_line)
        
        return '\n'.join(lines)
    
    def generate_srt_subtitle(self, subtitle_segments: List[SubtitleSegment]) -> str:
        """
        Generate SRT format subtitle content.
        
        Args:
            subtitle_segments: List of subtitle segments
            
        Returns:
            SRT format subtitle content as string
        """
        lines = []
        
        for i, segment in enumerate(subtitle_segments, 1):
            start_time = self.format_time_srt(segment.start_time)
            end_time = self.format_time_srt(segment.end_time)
            text = segment.text.replace('\\N', '\n')  # Convert ASS line breaks to SRT
            
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(text)
            lines.append("")  # Empty line between subtitles
        
        return '\n'.join(lines)
    
    def generate_vtt_subtitle(self, subtitle_segments: List[SubtitleSegment]) -> str:
        """
        Generate WebVTT format subtitle content.
        
        Args:
            subtitle_segments: List of subtitle segments
            
        Returns:
            WebVTT format subtitle content as string
        """
        lines = ["WEBVTT", ""]
        
        for i, segment in enumerate(subtitle_segments, 1):
            start_time = self.format_time_srt(segment.start_time).replace(',', '.')
            end_time = self.format_time_srt(segment.end_time).replace(',', '.')
            text = segment.text.replace('\\N', '\n')
            
            lines.append(f"{start_time} --> {end_time}")
            lines.append(text)
            lines.append("")
        
        return '\n'.join(lines)
    
    def process_transcript_to_subtitles(self, transcript: str, audio_duration: float,
                                      output_formats: List[str] = None) -> Dict[str, str]:
        """
        Process a plain transcript into subtitle formats.
        
        Args:
            transcript: Plain text transcript
            audio_duration: Total audio duration in seconds
            output_formats: List of formats to generate ('ass', 'srt', 'vtt')
            
        Returns:
            Dictionary mapping format names to subtitle content
        """
        if output_formats is None:
            output_formats = ['ass', 'srt']
        
        # Create timed segments from transcript
        timed_segments = self.create_timed_segments_from_transcript(transcript, audio_duration)
        
        # Convert to subtitle segments
        subtitle_segments = self.create_subtitle_segments(timed_segments)
        
        # Generate requested formats
        results = {}
        
        if 'ass' in output_formats:
            results['ass'] = self.generate_ass_subtitle(subtitle_segments)
        
        if 'srt' in output_formats:
            results['srt'] = self.generate_srt_subtitle(subtitle_segments)
        
        if 'vtt' in output_formats:
            results['vtt'] = self.generate_vtt_subtitle(subtitle_segments)
        
        return results
    
    def save_subtitles(self, subtitle_content: Dict[str, str], base_path: Union[str, Path],
                      filename_base: str) -> Dict[str, Path]:
        """
        Save subtitle content to files.
        
        Args:
            subtitle_content: Dictionary mapping format to content
            base_path: Base directory path
            filename_base: Base filename (without extension)
            
        Returns:
            Dictionary mapping format to saved file paths
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        for format_name, content in subtitle_content.items():
            file_path = base_path / f"{filename_base}.{format_name}"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[format_name] = file_path
        
        return saved_files


def main():
    """Example usage of SubtitleProcessor."""
    # Example transcript
    transcript = """
    Hey guys, did you know that in terms of male human and female Pokémon breeding, 
    Vaporeon is the most compatible Pokémon for humans? Not only are they in the field egg group, 
    which is mostly comprised of mammals, Vaporeon are an average of 3'03" tall and 63.9 pounds.
    """
    
    # Initialize processor
    processor = SubtitleProcessor()
    
    # Process transcript (assuming 60 second audio)
    subtitles = processor.process_transcript_to_subtitles(
        transcript=transcript.strip(),
        audio_duration=60.0,
        output_formats=['ass', 'srt', 'vtt']
    )
    
    # Print results
    for format_name, content in subtitles.items():
        print(f"\n=== {format_name.upper()} Format ===")
        print(content[:500] + "..." if len(content) > 500 else content)
    
    # Save to files
    saved_files = processor.save_subtitles(
        subtitles, 
        Path("output/subtitles"), 
        "example"
    )
    
    print(f"\nSaved subtitle files:")
    for format_name, file_path in saved_files.items():
        print(f"  {format_name}: {file_path}")


if __name__ == "__main__":
    main()