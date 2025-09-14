#!/usr/bin/env python3
"""
Subtitle Format Management

This module provides functionality for converting between different subtitle formats
and managing video container operations for subtitle embedding.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import timedelta
import xml.etree.ElementTree as ET

from src.subtitle_processor import TimedSegment, SubtitleSegment


@dataclass
class SubtitleFormat:
    """Represents a subtitle format specification."""
    name: str
    extension: str
    supports_styling: bool
    supports_positioning: bool
    supports_effects: bool
    mime_type: str


class SubtitleFormatter:
    """Handles conversion between different subtitle formats."""
    
    # Supported subtitle formats
    FORMATS = {
        'ass': SubtitleFormat(
            name='Advanced SubStation Alpha',
            extension='.ass',
            supports_styling=True,
            supports_positioning=True,
            supports_effects=True,
            mime_type='text/x-ass'
        ),
        'srt': SubtitleFormat(
            name='SubRip',
            extension='.srt',
            supports_styling=False,
            supports_positioning=False,
            supports_effects=False,
            mime_type='text/srt'
        ),
        'vtt': SubtitleFormat(
            name='WebVTT',
            extension='.vtt',
            supports_styling=True,
            supports_positioning=True,
            supports_effects=False,
            mime_type='text/vtt'
        ),
        'ttml': SubtitleFormat(
            name='Timed Text Markup Language',
            extension='.ttml',
            supports_styling=True,
            supports_positioning=True,
            supports_effects=True,
            mime_type='application/ttml+xml'
        ),
        'sbv': SubtitleFormat(
            name='YouTube SubViewer',
            extension='.sbv',
            supports_styling=False,
            supports_positioning=False,
            supports_effects=False,
            mime_type='text/sbv'
        )
    }
    
    def __init__(self):
        """Initialize the subtitle formatter."""
        pass
    
    def parse_srt(self, srt_content: str) -> List[SubtitleSegment]:
        """
        Parse SRT format subtitle content.
        
        Args:
            srt_content: SRT format subtitle content
            
        Returns:
            List of SubtitleSegment objects
        """
        segments = []
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # Parse subtitle number (first line)
                subtitle_num = int(lines[0])
                
                # Parse timing (second line)
                timing_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', lines[1])
                if not timing_match:
                    continue
                
                # Convert to seconds
                start_h, start_m, start_s, start_ms = map(int, timing_match.groups()[:4])
                end_h, end_m, end_s, end_ms = map(int, timing_match.groups()[4:])
                
                start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
                
                # Parse text (remaining lines)
                text = '\n'.join(lines[2:])
                
                segment = SubtitleSegment(
                    start_time=start_time,
                    end_time=end_time,
                    text=text
                )
                segments.append(segment)
                
            except (ValueError, IndexError):
                continue
        
        return segments
    
    def parse_ass(self, ass_content: str) -> List[SubtitleSegment]:
        """
        Parse ASS format subtitle content.
        
        Args:
            ass_content: ASS format subtitle content
            
        Returns:
            List of SubtitleSegment objects
        """
        segments = []
        
        # Find the Events section
        lines = ass_content.split('\n')
        in_events = False
        format_line = None
        
        for line in lines:
            line = line.strip()
            
            if line == '[Events]':
                in_events = True
                continue
            elif line.startswith('[') and in_events:
                break
            elif not in_events:
                continue
            
            if line.startswith('Format:'):
                format_line = line[7:].strip()
                continue
            
            if line.startswith('Dialogue:') and format_line:
                try:
                    # Parse dialogue line
                    dialogue_data = line[9:].strip()
                    fields = [f.strip() for f in dialogue_data.split(',')]
                    
                    # Map fields based on format
                    format_fields = [f.strip() for f in format_line.split(',')]
                    field_map = {field: i for i, field in enumerate(format_fields)}
                    
                    if 'Start' in field_map and 'End' in field_map and 'Text' in field_map:
                        start_time = self._parse_ass_time(fields[field_map['Start']])
                        end_time = self._parse_ass_time(fields[field_map['End']])
                        text = ','.join(fields[field_map['Text']:])  # Text might contain commas
                        
                        # Convert ASS line breaks to regular line breaks
                        text = text.replace('\\N', '\n')
                        
                        segment = SubtitleSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=text,
                            style=fields[field_map.get('Style', 0)] if 'Style' in field_map else None
                        )
                        segments.append(segment)
                
                except (ValueError, IndexError):
                    continue
        
        return segments
    
    def _parse_ass_time(self, time_str: str) -> float:
        """Parse ASS time format (H:MM:SS.CC) to seconds."""
        match = re.match(r'(\d+):(\d{2}):(\d{2})\.(\d{2})', time_str)
        if not match:
            return 0.0
        
        hours, minutes, seconds, centiseconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds + centiseconds / 100
    
    def parse_vtt(self, vtt_content: str) -> List[SubtitleSegment]:
        """
        Parse WebVTT format subtitle content.
        
        Args:
            vtt_content: WebVTT format subtitle content
            
        Returns:
            List of SubtitleSegment objects
        """
        segments = []
        
        lines = vtt_content.split('\n')
        i = 0
        
        # Skip header
        while i < len(lines) and not lines[i].strip().startswith('WEBVTT'):
            i += 1
        i += 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and notes
            if not line or line.startswith('NOTE'):
                i += 1
                continue
            
            # Check if this is a timing line
            timing_match = re.match(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3}) --> (\d{2}):(\d{2}):(\d{2})\.(\d{3})', line)
            if timing_match:
                try:
                    # Parse timing
                    start_h, start_m, start_s, start_ms = map(int, timing_match.groups()[:4])
                    end_h, end_m, end_s, end_ms = map(int, timing_match.groups()[4:])
                    
                    start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                    end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
                    
                    # Collect text lines
                    i += 1
                    text_lines = []
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    text = '\n'.join(text_lines)
                    
                    segment = SubtitleSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    )
                    segments.append(segment)
                
                except (ValueError, IndexError):
                    pass
            
            i += 1
        
        return segments
    
    def convert_format(self, input_content: str, input_format: str, 
                      output_format: str) -> str:
        """
        Convert subtitle content from one format to another.
        
        Args:
            input_content: Input subtitle content
            input_format: Input format ('srt', 'ass', 'vtt', etc.)
            output_format: Output format ('srt', 'ass', 'vtt', etc.)
            
        Returns:
            Converted subtitle content
        """
        if input_format not in self.FORMATS:
            raise ValueError(f"Unsupported input format: {input_format}")
        
        if output_format not in self.FORMATS:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        if input_format == output_format:
            return input_content
        
        # Parse input format
        if input_format == 'srt':
            segments = self.parse_srt(input_content)
        elif input_format == 'ass':
            segments = self.parse_ass(input_content)
        elif input_format == 'vtt':
            segments = self.parse_vtt(input_content)
        else:
            raise ValueError(f"Parsing not implemented for format: {input_format}")
        
        # Convert to output format
        from src.subtitle_processor import SubtitleProcessor
        processor = SubtitleProcessor()
        
        if output_format == 'srt':
            return processor.generate_srt_subtitle(segments)
        elif output_format == 'ass':
            return processor.generate_ass_subtitle(segments)
        elif output_format == 'vtt':
            return processor.generate_vtt_subtitle(segments)
        else:
            raise ValueError(f"Generation not implemented for format: {output_format}")
    
    def detect_format(self, content: str) -> Optional[str]:
        """
        Detect subtitle format from content.
        
        Args:
            content: Subtitle file content
            
        Returns:
            Detected format name or None
        """
        content = content.strip()
        
        # Check for WebVTT
        if content.startswith('WEBVTT'):
            return 'vtt'
        
        # Check for ASS
        if '[Script Info]' in content and '[V4+ Styles]' in content:
            return 'ass'
        
        # Check for SRT (simple heuristic)
        lines = content.split('\n')
        if len(lines) >= 3:
            # First line should be a number
            try:
                int(lines[0].strip())
                # Second line should be timing
                if '-->' in lines[1]:
                    return 'srt'
            except ValueError:
                pass
        
        return None
    
    def validate_format(self, content: str, format_name: str) -> bool:
        """
        Validate that content matches the specified format.
        
        Args:
            content: Subtitle content
            format_name: Expected format name
            
        Returns:
            True if content matches format
        """
        detected = self.detect_format(content)
        return detected == format_name
    
    def get_format_info(self, format_name: str) -> Optional[SubtitleFormat]:
        """
        Get information about a subtitle format.
        
        Args:
            format_name: Format name
            
        Returns:
            SubtitleFormat object or None
        """
        return self.FORMATS.get(format_name)
    
    def list_supported_formats(self) -> List[str]:
        """
        Get list of supported subtitle formats.
        
        Returns:
            List of format names
        """
        return list(self.FORMATS.keys())


class ContainerManager:
    """Manages video container operations for subtitle embedding."""
    
    def __init__(self):
        """Initialize the container manager."""
        self.supported_containers = {
            'mkv': {
                'name': 'Matroska',
                'subtitle_formats': ['ass', 'srt', 'vtt'],
                'multiple_subtitles': True,
                'external_subtitles': True
            },
            'mp4': {
                'name': 'MP4',
                'subtitle_formats': ['srt', 'vtt'],
                'multiple_subtitles': True,
                'external_subtitles': False
            },
            'avi': {
                'name': 'AVI',
                'subtitle_formats': ['srt'],
                'multiple_subtitles': False,
                'external_subtitles': True
            }
        }
    
    def get_container_info(self, container_format: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a container format.
        
        Args:
            container_format: Container format name
            
        Returns:
            Container information dictionary
        """
        return self.supported_containers.get(container_format)
    
    def get_supported_subtitle_formats(self, container_format: str) -> List[str]:
        """
        Get subtitle formats supported by a container.
        
        Args:
            container_format: Container format name
            
        Returns:
            List of supported subtitle formats
        """
        info = self.get_container_info(container_format)
        return info['subtitle_formats'] if info else []
    
    def can_embed_subtitles(self, container_format: str, subtitle_format: str) -> bool:
        """
        Check if a container can embed a specific subtitle format.
        
        Args:
            container_format: Container format name
            subtitle_format: Subtitle format name
            
        Returns:
            True if embedding is supported
        """
        supported_formats = self.get_supported_subtitle_formats(container_format)
        return subtitle_format in supported_formats
    
    def recommend_subtitle_format(self, container_format: str, 
                                 prefer_styling: bool = True) -> Optional[str]:
        """
        Recommend the best subtitle format for a container.
        
        Args:
            container_format: Container format name
            prefer_styling: Whether to prefer formats with styling support
            
        Returns:
            Recommended subtitle format name
        """
        supported_formats = self.get_supported_subtitle_formats(container_format)
        
        if not supported_formats:
            return None
        
        formatter = SubtitleFormatter()
        
        if prefer_styling:
            # Prefer formats with styling support
            for fmt in ['ass', 'vtt', 'srt']:
                if fmt in supported_formats:
                    format_info = formatter.get_format_info(fmt)
                    if format_info and format_info.supports_styling:
                        return fmt
        
        # Fall back to first supported format
        return supported_formats[0]


def main():
    """Example usage of subtitle formatting."""
    formatter = SubtitleFormatter()
    container_manager = ContainerManager()
    
    # Example SRT content
    srt_content = """1
00:00:01,000 --> 00:00:05,000
Hello, this is a test subtitle.

2
00:00:06,000 --> 00:00:10,000
This is the second subtitle line.
"""
    
    print("=== Subtitle Format Conversion Example ===")
    
    # Detect format
    detected = formatter.detect_format(srt_content)
    print(f"Detected format: {detected}")
    
    # Convert SRT to ASS
    try:
        ass_content = formatter.convert_format(srt_content, 'srt', 'ass')
        print(f"\nConverted to ASS format:")
        print(ass_content[:300] + "..." if len(ass_content) > 300 else ass_content)
    except Exception as e:
        print(f"Conversion failed: {e}")
    
    # Convert SRT to VTT
    try:
        vtt_content = formatter.convert_format(srt_content, 'srt', 'vtt')
        print(f"\nConverted to VTT format:")
        print(vtt_content)
    except Exception as e:
        print(f"Conversion failed: {e}")
    
    print("\n=== Container Format Information ===")
    
    # Show container capabilities
    for container in ['mkv', 'mp4', 'avi']:
        info = container_manager.get_container_info(container)
        if info:
            print(f"\n{container.upper()} ({info['name']}):")
            print(f"  Supported subtitle formats: {info['subtitle_formats']}")
            print(f"  Multiple subtitles: {info['multiple_subtitles']}")
            print(f"  External subtitles: {info['external_subtitles']}")
            
            recommended = container_manager.recommend_subtitle_format(container)
            print(f"  Recommended format: {recommended}")
    
    print(f"\nSupported subtitle formats: {formatter.list_supported_formats()}")


if __name__ == "__main__":
    main()