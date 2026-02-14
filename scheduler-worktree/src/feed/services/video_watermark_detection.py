"""Video watermark detection and OSINT identification service.

This service handles:
- Video frame extraction
- OCR for watermark detection
- Face recognition and matching
- Multi-source database lookups (data18, etc.)
- Ontology building for adult content
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import pytesseract
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

from ..storage.neo4j_connection import Neo4jConnection
from .adult_content_crawlers import (
    MultiSourceCrawler,
    Data18Crawler,
    IAFDCrawler,
    IndexxxCrawler,
    AdultReverseImageSearch,
)
from .stash_integration import StashIntegration, StashClient


@dataclass
class WatermarkDetection:
    """Detected watermark information."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    frame_number: int
    timestamp: float  # seconds into video


@dataclass
class FaceMatch:
    """Face recognition match result."""
    actor_id: str
    actor_name: str
    confidence: float
    frame_number: int
    bbox: Tuple[int, int, int, int]


@dataclass
class SceneMatch:
    """Scene match from database."""
    scene_id: str
    scene_title: str
    studio: str
    actors: List[str]
    url: str
    confidence: float
    match_type: str  # 'watermark', 'face', 'metadata'


@dataclass
class VideoIdentificationResult:
    """Complete video identification result."""
    video_path: str
    watermarks: List[WatermarkDetection]
    face_matches: List[FaceMatch]
    scene_matches: List[SceneMatch]
    studio: Optional[str] = None
    identified: bool = False
    metadata: Optional[Dict[str, Any]] = None


class VideoWatermarkDetector:
    """Detect watermarks in video files using OCR."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize watermark detector.
        
        Args:
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_frames(
        self,
        video_path: str,
        sample_rate: int = 30,  # Extract every Nth frame
        max_frames: int = 100
    ) -> List[Tuple[np.ndarray, int, float]]:
        """
        Extract frames from video for analysis.
        
        Args:
            video_path: Path to video file
            sample_rate: Extract every Nth frame
            max_frames: Maximum frames to extract
            
        Returns:
            List of (frame_image, frame_number, timestamp) tuples
        """
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0
        extracted = 0
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        while cap.isOpened() and extracted < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % sample_rate == 0:
                timestamp = frame_count / fps if fps > 0 else 0
                frames.append((frame, frame_count, timestamp))
                extracted += 1
            
            frame_count += 1
        
        cap.release()
        return frames
    
    def detect_watermark(
        self,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float,
        watermark_patterns: Optional[List[str]] = None
    ) -> List[WatermarkDetection]:
        """
        Detect watermarks in a frame using OCR.
        
        Args:
            frame: Video frame (numpy array)
            frame_number: Frame number
            timestamp: Timestamp in seconds
            watermark_patterns: Optional list of expected watermark patterns
            
        Returns:
            List of detected watermarks
        """
        detections = []
        
        # Convert to PIL Image for OCR
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Try OCR on full frame
        try:
            ocr_data = pytesseract.image_to_data(
                pil_image,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and bounding boxes
            n_boxes = len(ocr_data['text'])
            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                conf = float(ocr_data['conf'][i]) if ocr_data['conf'][i] != -1 else 0.0
                
                if text and conf > 30:  # Minimum confidence threshold
                    # Check if it matches watermark patterns
                    is_watermark = False
                    if watermark_patterns:
                        for pattern in watermark_patterns:
                            if pattern.lower() in text.lower():
                                is_watermark = True
                                break
                    else:
                        # Heuristic: short text in corners/edges might be watermark
                        x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], \
                                   ocr_data['width'][i], ocr_data['height'][i]
                        frame_h, frame_w = frame.shape[:2]
                        
                        # Check if text is in corner/edge regions
                        margin = 0.1
                        in_corner = (
                            (x < frame_w * margin or x > frame_w * (1 - margin)) or
                            (y < frame_h * margin or y > frame_h * (1 - margin))
                        )
                        
                        if in_corner and len(text) < 50:
                            is_watermark = True
                    
                    if is_watermark:
                        detections.append(WatermarkDetection(
                            text=text,
                            confidence=conf / 100.0,
                            bbox=(
                                ocr_data['left'][i],
                                ocr_data['top'][i],
                                ocr_data['width'][i],
                                ocr_data['height'][i]
                            ),
                            frame_number=frame_number,
                            timestamp=timestamp
                        ))
        except Exception as e:
            print(f"OCR error on frame {frame_number}: {e}")
        
        return detections
    
    def detect_watermarks_in_video(
        self,
        video_path: str,
        watermark_patterns: Optional[List[str]] = None,
        sample_rate: int = 30
    ) -> List[WatermarkDetection]:
        """
        Detect watermarks throughout a video.
        
        Args:
            video_path: Path to video file
            watermark_patterns: Expected watermark patterns (e.g., ['fantasyhd.com'])
            sample_rate: Extract every Nth frame
            
        Returns:
            List of all detected watermarks
        """
        frames = self.extract_frames(video_path, sample_rate=sample_rate)
        all_detections = []
        
        for frame, frame_number, timestamp in frames:
            detections = self.detect_watermark(
                frame, frame_number, timestamp, watermark_patterns
            )
            all_detections.extend(detections)
        
        # Deduplicate similar watermarks
        unique_detections = self._deduplicate_watermarks(all_detections)
        
        return unique_detections
    
    def _deduplicate_watermarks(
        self,
        detections: List[WatermarkDetection]
    ) -> List[WatermarkDetection]:
        """Remove duplicate watermark detections."""
        if not detections:
            return []
        
        # Group by text similarity
        unique = []
        seen_texts = set()
        
        for det in detections:
            text_lower = det.text.lower().strip()
            # Check if we've seen similar text
            is_duplicate = False
            for seen in seen_texts:
                if text_lower in seen or seen in text_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(det)
                seen_texts.add(text_lower)
        
        return unique


# Data18Crawler moved to adult_content_crawlers.py
# Import here for backward compatibility


class FaceMatcher:
    """Face recognition and matching service."""
    
    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize face matcher.
        
        Args:
            neo4j: Neo4j connection for actor database
        """
        self.neo4j = neo4j
        # TODO: Initialize face recognition model (e.g., face_recognition library)
    
    def extract_faces_from_frame(
        self,
        frame: np.ndarray
    ) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Extract faces from a video frame.
        
        Args:
            frame: Video frame (numpy array)
            
        Returns:
            List of (face_image, bbox) tuples
        """
        # TODO: Implement face detection using OpenCV or face_recognition
        # Placeholder
        return []
    
    def match_face_to_actors(
        self,
        face_image: np.ndarray,
        actor_ids: List[str]
    ) -> List[FaceMatch]:
        """
        Match a face to known actors.
        
        Args:
            face_image: Face image (numpy array)
            actor_ids: List of actor IDs to match against
            
        Returns:
            List of face matches with confidence scores
        """
        # TODO: Implement face recognition matching
        # 1. Load actor face encodings from Neo4j
        # 2. Compute encoding for input face
        # 3. Compare and return matches
        return []


class VideoIdentificationService:
    """Complete video identification service."""
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        enable_face_matching: bool = True,
        use_multi_source: bool = True,
        stash_url: Optional[str] = None,
        stash_api_key: Optional[str] = None
    ):
        """
        Initialize video identification service.
        
        Args:
            neo4j: Neo4j connection
            enable_face_matching: Enable face recognition matching
            use_multi_source: Use multiple database sources (Data18, IAFD, Indexxx)
            stash_url: Optional Stash instance URL (e.g., "http://192.168.0.222:9999")
            stash_api_key: Optional Stash API key
        """
        self.neo4j = neo4j
        self.watermark_detector = VideoWatermarkDetector()
        
        if use_multi_source:
            self.crawler = MultiSourceCrawler()
        else:
            self.crawler = Data18Crawler()
        
        self.face_matcher = FaceMatcher(neo4j) if enable_face_matching else None
        self.reverse_search = AdultReverseImageSearch()
        
        # Stash integration (primary source if available)
        self.stash = None
        if stash_url:
            try:
                self.stash = StashIntegration(stash_url, stash_api_key)
                print(f"Stash integration enabled: {stash_url}")
            except Exception as e:
                print(f"Warning: Could not connect to Stash: {e}")
    
    def identify_video(
        self,
        video_path: str,
        watermark_patterns: Optional[List[str]] = None
    ) -> VideoIdentificationResult:
        """
        Identify a video using multiple methods.
        
        Args:
            video_path: Path to video file
            watermark_patterns: Expected watermark patterns
            
        Returns:
            Complete identification result
        """
        # Step 1: Detect watermarks
        watermarks = self.watermark_detector.detect_watermarks_in_video(
            video_path,
            watermark_patterns=watermark_patterns
        )
        
        # Step 2: Extract studio from watermarks
        studio = None
        if watermarks:
            # Extract domain from watermark (e.g., "fantasyhd.com" -> "fantasyhd")
            watermark_text = watermarks[0].text.lower()
            if '.com' in watermark_text:
                studio = watermark_text.split('.com')[0]
        
        # Step 3: If studio found, search Stash first (if available), then multi-source databases
        scene_matches = []
        if studio:
            # Priority 1: Stash (if available) - most comprehensive and accurate
            if self.stash:
                stash_scenes = self.stash.client.get_fantasyhd_scenes(limit=100)
                for scene in stash_scenes:
                    scene_matches.append(SceneMatch(
                        scene_id=scene.id,
                        scene_title=scene.title,
                        studio=studio,
                        actors=[p.name for p in (scene.performers or [])],
                        url=scene.url or f"{self.stash.client.base_url}/scenes/{scene.id}",
                        confidence=0.9,  # High confidence from Stash
                        match_type='stash'
                    ))
            
            # Priority 2: Multi-source crawler (Data18, IAFD, Indexxx)
            if not scene_matches:  # Only if Stash didn't find matches
                scenes = self.crawler.search_scenes_multi_source(
                    studio=studio,
                    keywords=None
                )
                
                for scene in scenes:
                    scene_matches.append(SceneMatch(
                        scene_id=scene.scene_id,
                        scene_title=scene.title,
                        studio=studio,
                        actors=scene.performers,
                        url=scene.url,
                        confidence=0.7,  # Initial confidence
                        match_type=scene.source  # 'data18', 'iafd', 'indexxx'
                    ))
        
        # Step 4: Face matching and reverse image search (if enabled)
        face_matches = []
        if self.face_matcher or True:  # Also use reverse image search
            frames = self.watermark_detector.extract_frames(video_path, sample_rate=60)
            
            # Extract clear face frames (avoid motion blur, overlays)
            clear_frames = []
            for frame, frame_number, timestamp in frames[:10]:
                # Heuristic: prefer frames with faces detected
                # TODO: Implement actual face detection filtering
                clear_frames.append((frame, frame_number, timestamp))
            
            # Try adult reverse image search on clear frames
            for frame, frame_number, _ in clear_frames[:3]:  # Limit to 3 frames
                # Save frame temporarily for reverse search
                import tempfile
                import cv2
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    cv2.imwrite(tmp.name, frame)
                    reverse_results = self.reverse_search.search_by_image(tmp.name)
                    
                    # Process reverse search results
                    for result in reverse_results:
                        # Would extract performer names from results
                        pass
            
            # Traditional face matching (if enabled)
            if self.face_matcher:
                for frame, frame_number, _ in clear_frames:
                    faces = self.face_matcher.extract_faces_from_frame(frame)
                    for face_image, bbox in faces:
                        # Get actor IDs from studio using multi-source
                        if studio:
                            performers = self.crawler.get_all_fantasyhd_performers()
                            performer_ids = [p.performer_id for p in performers]
                            matches = self.face_matcher.match_face_to_actors(
                                face_image, performer_ids
                            )
                            face_matches.extend(matches)
        
        return VideoIdentificationResult(
            video_path=video_path,
            watermarks=watermarks,
            face_matches=face_matches,
            scene_matches=scene_matches,
            studio=studio,
            identified=len(scene_matches) > 0 or len(face_matches) > 0
        )

