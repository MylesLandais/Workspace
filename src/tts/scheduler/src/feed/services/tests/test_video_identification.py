"""Test suite for video identification and reverse lookup."""

import pytest
from pathlib import Path
from typing import List, Dict
import numpy as np

from ..video_watermark_detection import (
    VideoWatermarkDetector,
    VideoIdentificationService,
    WatermarkDetection,
    FaceMatch,
    SceneMatch,
)
from ..adult_content_crawlers import (
    MultiSourceCrawler,
    Data18Crawler,
    IAFDCrawler,
    IndexxxCrawler,
)
from ..stash_integration import StashClient, StashIntegration
from ...storage.neo4j_connection import get_connection


class TestVideoWatermarkDetection:
    """Test watermark detection functionality."""
    
    def test_extract_frames(self, sample_video_path: str):
        """Test frame extraction from video."""
        detector = VideoWatermarkDetector()
        frames = detector.extract_frames(sample_video_path, sample_rate=30, max_frames=10)
        
        assert len(frames) > 0
        assert all(isinstance(f[0], np.ndarray) for f in frames)
        assert all(isinstance(f[1], int) for f in frames)  # frame_number
        assert all(isinstance(f[2], float) for f in frames)  # timestamp
    
    def test_detect_watermark_fantasyhd(self, sample_video_path: str):
        """Test detection of fantasyhd.com watermark."""
        detector = VideoWatermarkDetector()
        watermarks = detector.detect_watermarks_in_video(
            sample_video_path,
            watermark_patterns=["fantasyhd.com", "fantasyhd"],
            sample_rate=30
        )
        
        # Should detect at least one watermark
        assert len(watermarks) > 0
        
        # Check watermark text contains expected pattern
        watermark_texts = [w.text.lower() for w in watermarks]
        has_fantasyhd = any(
            "fantasyhd" in text or "fantasy" in text
            for text in watermark_texts
        )
        assert has_fantasyhd, f"No fantasyhd watermark detected. Found: {watermark_texts}"
    
    def test_watermark_confidence(self, sample_video_path: str):
        """Test watermark detection confidence scores."""
        detector = VideoWatermarkDetector()
        watermarks = detector.detect_watermarks_in_video(
            sample_video_path,
            watermark_patterns=["fantasyhd.com"]
        )
        
        if watermarks:
            # Confidence should be reasonable
            avg_confidence = sum(w.confidence for w in watermarks) / len(watermarks)
            assert avg_confidence > 0.3, f"Low average confidence: {avg_confidence}"
    
    def test_deduplicate_watermarks(self):
        """Test watermark deduplication."""
        detector = VideoWatermarkDetector()
        
        # Create duplicate detections
        detections = [
            WatermarkDetection(
                text="fantasyhd.com",
                confidence=0.9,
                bbox=(10, 10, 100, 20),
                frame_number=0,
                timestamp=0.0
            ),
            WatermarkDetection(
                text="FANTASYHD.COM",
                confidence=0.85,
                bbox=(12, 12, 100, 20),
                frame_number=30,
                timestamp=1.0
            ),
        ]
        
        unique = detector._deduplicate_watermarks(detections)
        assert len(unique) == 1, "Should deduplicate similar watermarks"


class TestData18Crawler:
    """Test data18.com crawling functionality."""
    
    def test_get_studio_performers(self):
        """Test fetching performers for fantasyhd studio."""
        crawler = Data18Crawler()
        performers = crawler.get_studio_performers("fantasyhd")
        
        # Should return list of performers
        assert isinstance(performers, list)
        
        if performers:
            # Check performer structure
            performer = performers[0]
            assert hasattr(performer, 'name')
            assert hasattr(performer, 'performer_id')
            assert hasattr(performer, 'profile_url')
            assert hasattr(performer, 'source')
            assert performer.source == 'data18'
    
    def test_get_performer_fantasyhd_scenes(self):
        """Test fetching FantasyHD scenes for a performer."""
        crawler = Data18Crawler()
        
        # First get a performer
        performers = crawler.get_studio_performers("fantasyhd")
        if performers:
            performer_id = performers[0].performer_id
            scenes = crawler.get_performer_fantasyhd_scenes(performer_id, "fantasyhd")
            
            assert isinstance(scenes, list)
            if scenes:
                scene = scenes[0]
                assert hasattr(scene, 'scene_id')
                assert hasattr(scene, 'title')
                assert hasattr(scene, 'studio')
                assert scene.studio == 'fantasyhd'
    
    def test_search_scenes_by_studio(self):
        """Test searching scenes for a studio."""
        crawler = Data18Crawler()
        scenes = crawler.search_scenes_by_studio("fantasyhd", keywords=None)
        
        assert isinstance(scenes, list)
        if scenes:
            assert all(hasattr(s, 'scene_id') for s in scenes)
            assert all(hasattr(s, 'title') for s in scenes)


class TestIAFDCrawler:
    """Test IAFD.com crawling functionality."""
    
    def test_get_distributor_titles(self):
        """Test fetching titles for fantasyhd.com distributor."""
        crawler = IAFDCrawler()
        scenes = crawler.get_distributor_titles("fantasyhd.com")
        
        assert isinstance(scenes, list)
        if scenes:
            scene = scenes[0]
            assert hasattr(scene, 'scene_id')
            assert hasattr(scene, 'title')
            assert hasattr(scene, 'studio')
            assert scene.source == 'iafd'
    
    def test_get_performer_fantasyhd_titles(self):
        """Test fetching FantasyHD titles for a performer."""
        crawler = IAFDCrawler()
        # Use a known performer name for testing
        scenes = crawler.get_performer_fantasyhd_titles("Test Performer")
        
        assert isinstance(scenes, list)


class TestIndexxxCrawler:
    """Test Indexxx.com crawling functionality."""
    
    def test_get_model_fantasyhd_scenes(self):
        """Test fetching FantasyHD scenes for a model."""
        crawler = IndexxxCrawler()
        # Use a known model name for testing
        scenes = crawler.get_model_fantasyhd_scenes("Test Model")
        
        assert isinstance(scenes, list)
        if scenes:
            scene = scenes[0]
            assert hasattr(scene, 'scene_id')
            assert hasattr(scene, 'title')
            assert hasattr(scene, 'performers')
            assert scene.source == 'indexxx'


class TestMultiSourceCrawler:
    """Test multi-source crawling functionality."""
    
    def test_get_all_fantasyhd_performers(self):
        """Test getting performers from all sources."""
        crawler = MultiSourceCrawler()
        performers = crawler.get_all_fantasyhd_performers()
        
        assert isinstance(performers, list)
        if performers:
            # Should be deduplicated
            names = [p.name.lower() for p in performers]
            assert len(names) == len(set(names)), "Performers should be deduplicated"
    
    def test_search_scenes_multi_source(self):
        """Test searching scenes across all sources."""
        crawler = MultiSourceCrawler()
        scenes = crawler.search_scenes_multi_source(studio="fantasyhd")
        
        assert isinstance(scenes, list)
        if scenes:
            # Should have scenes from multiple sources
            sources = set(s.source for s in scenes)
            assert len(sources) > 0


class TestStashIntegration:
    """Test Stash integration functionality."""
    
    @pytest.fixture
    def stash_url(self):
        """Provide Stash URL for testing."""
        # Update with your Stash instance URL
        return "http://192.168.0.222:9999"
    
    def test_stash_connection(self, stash_url):
        """Test connection to Stash instance."""
        client = StashClient(stash_url)
        scenes = client.get_fantasyhd_scenes(limit=10)
        
        # Should return list (may be empty if no scenes indexed)
        assert isinstance(scenes, list)
    
    def test_stash_search_scenes(self, stash_url):
        """Test searching scenes in Stash."""
        client = StashClient(stash_url)
        scenes = client.search_scenes(studio="FantasyHD", limit=10)
        
        assert isinstance(scenes, list)
        if scenes:
            scene = scenes[0]
            assert hasattr(scene, 'id')
            assert hasattr(scene, 'title')
            assert hasattr(scene, 'studio')
    
    def test_stash_get_scene_by_id(self, stash_url):
        """Test getting scene by ID from Stash."""
        client = StashClient(stash_url)
        
        # First get a scene ID
        scenes = client.get_fantasyhd_scenes(limit=1)
        if scenes:
            scene_id = scenes[0].id
            scene = client.get_scene_by_id(scene_id)
            
            assert scene is not None
            assert scene.id == scene_id
    
    def test_stash_search_performers(self, stash_url):
        """Test searching performers in Stash."""
        client = StashClient(stash_url)
        performers = client.search_performers(query="Natalie", limit=10)
        
        assert isinstance(performers, list)
        if performers:
            performer = performers[0]
            assert hasattr(performer, 'id')
            assert hasattr(performer, 'name')
    
    def test_video_identification_with_stash(self, sample_video_path: str, stash_url):
        """Test video identification using Stash."""
        neo4j = get_connection()
        service = VideoIdentificationService(
            neo4j=neo4j,
            enable_face_matching=False,
            stash_url=stash_url
        )
        
        result = service.identify_video(
            sample_video_path,
            watermark_patterns=["fantasyhd.com"]
        )
        
        # Should attempt Stash lookup
        assert hasattr(result, 'scene_matches')
        
        # Check for Stash matches
        stash_matches = [s for s in result.scene_matches if s.match_type == 'stash']
        # May or may not have matches depending on Stash content
        assert isinstance(stash_matches, list)


class TestVideoIdentification:
    """Test complete video identification workflow."""
    
    def test_identify_video_with_watermark(self, sample_video_path: str):
        """Test end-to-end video identification."""
        neo4j = get_connection()
        service = VideoIdentificationService(neo4j, enable_face_matching=False)
        
        result = service.identify_video(
            sample_video_path,
            watermark_patterns=["fantasyhd.com"]
        )
        
        # Should detect watermarks
        assert len(result.watermarks) > 0
        
        # Should identify studio
        assert result.studio is not None
        assert "fantasyhd" in result.studio.lower()
    
    def test_scene_matching(self, sample_video_path: str):
        """Test scene matching after studio identification."""
        neo4j = get_connection()
        service = VideoIdentificationService(neo4j, enable_face_matching=False)
        
        result = service.identify_video(
            sample_video_path,
            watermark_patterns=["fantasyhd.com"]
        )
        
        # If studio identified, should attempt scene matching
        if result.studio:
            # May or may not have matches depending on database
            assert isinstance(result.scene_matches, list)
    
    def test_identification_result_structure(self, sample_video_path: str):
        """Test that identification result has correct structure."""
        neo4j = get_connection()
        service = VideoIdentificationService(neo4j, enable_face_matching=False)
        
        result = service.identify_video(sample_video_path)
        
        assert hasattr(result, 'video_path')
        assert hasattr(result, 'watermarks')
        assert hasattr(result, 'face_matches')
        assert hasattr(result, 'scene_matches')
        assert hasattr(result, 'studio')
        assert hasattr(result, 'identified')


class TestEvaluationMetrics:
    """Test evaluation metrics and progress tracking."""
    
    def test_watermark_detection_rate(self, test_videos: List[Dict]):
        """Calculate watermark detection rate."""
        detector = VideoWatermarkDetector()
        detected = 0
        total = len(test_videos)
        
        for video_info in test_videos:
            video_path = video_info["path"]
            expected_watermark = video_info.get("expected_watermark")
            
            if expected_watermark:
                watermarks = detector.detect_watermarks_in_video(
                    video_path,
                    watermark_patterns=[expected_watermark]
                )
                if watermarks:
                    detected += 1
        
        detection_rate = detected / total if total > 0 else 0
        print(f"Watermark detection rate: {detection_rate:.2%}")
        
        assert detection_rate > 0.5, f"Low detection rate: {detection_rate:.2%}"
    
    def test_processing_time(self, sample_video_path: str):
        """Measure video processing time."""
        import time
        
        neo4j = get_connection()
        service = VideoIdentificationService(neo4j, enable_face_matching=False)
        
        start = time.time()
        result = service.identify_video(sample_video_path)
        elapsed = time.time() - start
        
        print(f"Processing time: {elapsed:.2f} seconds")
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert elapsed < 300, f"Processing too slow: {elapsed:.2f}s"
    
    def test_identification_success_rate(self, test_videos: List[Dict]):
        """Calculate overall identification success rate."""
        neo4j = get_connection()
        service = VideoIdentificationService(neo4j, enable_face_matching=False)
        
        successful = 0
        total = len(test_videos)
        
        for video_info in test_videos:
            video_path = video_info["path"]
            result = service.identify_video(video_path)
            
            if result.identified:
                successful += 1
        
        success_rate = successful / total if total > 0 else 0
        print(f"Identification success rate: {success_rate:.2%}")
        
        return success_rate


# Fixtures

@pytest.fixture
def sample_video_path() -> str:
    """Provide path to sample video for testing."""
    # Update with actual test video path
    return "~/Downloads/1766554370099356.webm"


@pytest.fixture
def test_videos() -> List[Dict]:
    """Provide list of test videos with metadata."""
    return [
        {
            "path": "~/Downloads/1766554370099356.webm",
            "expected_watermark": "fantasyhd.com",
            "expected_studio": "fantasyhd"
        },
        # Add more test videos
    ]


# Run tests with: pytest src/feed/services/tests/test_video_identification.py -v

