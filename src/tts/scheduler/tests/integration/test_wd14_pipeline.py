"""
Integration tests for WD14 tagging pipeline.
Tests cache, service, and CLI operations.
"""

import pytest
import json
from pathlib import Path
from PIL import Image
from io import BytesIO

from src.feed.services.wd14_cache import WD14Cache
from src.feed.services.wd14_service import WD14Service
from src.image_captioning.models import WD14Result, WD14Tag, WD14TagCategory


@pytest.fixture
def cache():
    """Provide WD14Cache instance."""
    return WD14Cache()


@pytest.fixture
def test_image():
    """Create a simple test image."""
    img = Image.new("RGB", (448, 448), color="red")
    return img


class TestWD14Cache:
    """Test Valkey cache operations."""

    def test_cache_tags(self, cache):
        """Test caching WD14 tags."""
        sha256 = "test_image_123"
        tags_json = json.dumps({
            "image_sha256": sha256,
            "character_tags": [],
            "general_tags": [{"name": "1girl", "category": "general", "confidence": 0.99}],
            "rating": "safe",
            "processed_at": "2025-01-01T00:00:00",
            "model_version": "wd14-vit",
            "score_metadata": {},
        })

        cache.cache_tags(sha256, tags_json)
        retrieved = cache.get_cached_tags(sha256)

        assert retrieved is not None
        assert json.loads(retrieved)["image_sha256"] == sha256

    def test_mark_and_get_failed(self, cache):
        """Test tracking failed jobs."""
        sha256 = "failed_image_456"
        bucket = "test-bucket"
        uri = "s3://test-bucket/image.jpg"
        error = "Download timeout"

        cache.mark_failed(sha256, bucket, uri, error)
        failed_jobs = cache.get_failed_jobs(older_than_hours=0)

        assert any(job["image_sha256"] == sha256 for job in failed_jobs)

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        sha256_1 = "image_1"
        sha256_2 = "image_2"
        tags_json = '{"image_sha256": "test", "tags": []}'

        cache.cache_tags(sha256_1, tags_json)
        cache.cache_tags(sha256_2, tags_json)

        stats = cache.get_cache_stats()
        assert stats["cached_tags"] >= 2


class TestWD14Models:
    """Test WD14 data models."""

    def test_wd14_result_creation(self):
        """Test WD14Result creation and serialization."""
        tag1 = WD14Tag(name="1girl", category=WD14TagCategory.GENERAL, confidence=0.99)
        tag2 = WD14Tag(name="outdoor", category=WD14TagCategory.GENERAL, confidence=0.85)

        result = WD14Result(
            image_sha256="abc123",
            general_tags=[tag1, tag2],
            rating="safe",
        )

        # Test high confidence filtering
        high_conf = result.get_high_confidence_tags(threshold=0.90)
        assert len(high_conf) == 1
        assert high_conf[0].name == "1girl"

    def test_wd14_result_serialization(self):
        """Test WD14Result to/from dict."""
        tag = WD14Tag(name="1girl", category=WD14TagCategory.GENERAL, confidence=0.99)
        result = WD14Result(
            image_sha256="test_sha",
            general_tags=[tag],
            rating="safe",
        )

        data = result.to_dict()
        assert data["image_sha256"] == "test_sha"
        assert len(data["general_tags"]) == 1

        # Reconstruct from dict
        reconstructed = WD14Result.from_dict(data)
        assert reconstructed.image_sha256 == "test_sha"
        assert len(reconstructed.general_tags) == 1


class TestWD14Tagger:
    """Test WD14 ONNX tagger."""

    @pytest.mark.skip(reason="Requires ONNX model download and GPU")
    def test_tag_image(self, test_image):
        """Test tagging a simple image."""
        from src.image_captioning.wd14_tagger import WD14Tagger

        tagger = WD14Tagger()
        result = tagger.tag_image(test_image)

        assert isinstance(result, WD14Result)
        assert result.image_sha256  # Should compute SHA256
        assert result.rating in ["safe", "questionable", "explicit"]

    @pytest.mark.skip(reason="Requires ONNX model download")
    def test_tag_image_with_sha256(self, test_image):
        """Test tagging with provided SHA256."""
        from src.image_captioning.wd14_tagger import WD14Tagger

        tagger = WD14Tagger()
        sha256 = "custom_sha256"
        result = tagger.tag_image(test_image, sha256)

        assert result.image_sha256 == sha256


class TestWD14Service:
    """Test WD14 service operations."""

    @pytest.mark.skip(reason="Requires S3/MinIO connection")
    def test_scan_bucket(self):
        """Test bucket scanning."""
        service = WD14Service()
        images, new_count = service.scan_bucket("test-bucket")

        assert isinstance(images, list)
        assert isinstance(new_count, int)

    def test_get_stats(self):
        """Test getting service statistics."""
        service = WD14Service()
        stats = service.get_stats()

        assert "cached_tags" in stats
        assert "failed_jobs" in stats
        assert isinstance(stats["cached_tags"], int)
        assert isinstance(stats["failed_jobs"], int)
