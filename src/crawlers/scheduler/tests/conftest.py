"""Pytest fixtures for YouTube channel subscription tests."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j connection."""
    neo4j = Mock()
    neo4j.execute_read = Mock(return_value=[])
    neo4j.execute_write = Mock(return_value=[])
    return neo4j


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    redis = Mock()
    redis.get = Mock(return_value=None)
    redis.setex = Mock(return_value=True)
    redis.delete = Mock(return_value=1)
    redis.ping = Mock(return_value=True)
    redis.ttl = Mock(return_value=3600)
    redis.dbsize = Mock(return_value=0)
    redis.info = Mock(return_value={
        'redis_version': '7.2.0',
        'connected_clients': 5,
        'used_memory_human': '15.2M'
    })
    return redis


@pytest.fixture
def mock_valkey_connection(mock_redis):
    """Mock Valkey connection."""
    valkey = Mock()
    valkey.client = mock_redis
    return valkey


@pytest.fixture
def fasffy_creator_data():
    """Fasffy creator test data."""
    return {
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Fasffy",
        "slug": "fasffy",
        "bio": "Content creator and streamer - Testing memes and challenges",
        "avatar_url": "https://example.com/fasffy-avatar.jpg"
    }


@pytest.fixture
def misskatie_creator_data():
    """Miss Katie creator test data."""
    return {
        "uuid": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Miss Katie",
        "slug": "misskatie",
        "bio": "YouTube content creator - Lifestyle and vlogs",
        "avatar_url": "https://example.com/misskatie-avatar.jpg"
    }


@pytest.fixture
def youtube_platform_data():
    """YouTube platform test data."""
    return {
        "name": "YouTube",
        "slug": "youtube",
        "api_base_url": "https://www.googleapis.com/youtube/v3",
        "icon_url": "https://www.youtube.com/favicon.ico"
    }


@pytest.fixture
def fasffy_handle_data():
    """Fasffy YouTube handle test data."""
    return {
        "uuid": "660e8400-e29b-41d4-a716-446655440001",
        "username": "@Fasffy",
        "display_name": "Fasffy",
        "profile_url": "https://www.youtube.com/@Fasffy",
        "follower_count": 150000,
        "verified_by_platform": True
    }


@pytest.fixture
def misskatie_handle_data():
    """Miss Katie YouTube handle test data."""
    return {
        "uuid": "660e8400-e29b-41d4-a716-446655440002",
        "username": "@MissKatie",
        "display_name": "Miss Katie",
        "profile_url": "https://www.youtube.com/@MissKatie",
        "follower_count": 85000,
        "verified_by_platform": True
    }


@pytest.fixture
def sample_fasffy_video():
    """Sample Fasffy video test data."""
    return {
        "uuid": "770e8400-e29b-41d4-a716-446655440001",
        "title": "These Memes Challenge Me...",
        "source_url": "https://www.youtube.com/watch?v=2vh31BrqhJQ",
        "media_type": "Video",
        "publish_date": datetime.utcnow(),
        "thumbnail_url": "https://i.ytimg.com/vi/2vh31BrqhJQ/maxresdefault.jpg",
        "duration": 624,
        "view_count": 125000,
        "aspect_ratio": "16:9",
        "resolution": "1080p"
    }


@pytest.fixture
def sample_misskatie_video():
    """Sample Miss Katie video test data."""
    return {
        "uuid": "770e8400-e29b-41d4-a716-446655440002",
        "title": "A Day in My Life",
        "source_url": "https://www.youtube.com/watch?v=dummy123",
        "media_type": "Video",
        "publish_date": datetime.utcnow(),
        "thumbnail_url": "https://i.ytimg.com/vi/dummy123/maxresdefault.jpg",
        "duration": 845,
        "view_count": 45000,
        "aspect_ratio": "9:16",
        "resolution": "1080p"
    }
