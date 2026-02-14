"""Tests for lib.sources.base module."""

import pytest

from lib.sources.base import PlatformAdapter


class TestPlatformAdapterABC:
    """Test that PlatformAdapter defines the expected interface."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            PlatformAdapter()

    def test_has_platform_name_property(self):
        assert hasattr(PlatformAdapter, "platform_name")

    def test_has_fetch_posts(self):
        assert hasattr(PlatformAdapter, "fetch_posts")

    def test_has_fetch_media(self):
        assert hasattr(PlatformAdapter, "fetch_media")

    def test_has_get_rate_limits(self):
        assert hasattr(PlatformAdapter, "get_rate_limits")

    def test_has_validate_credentials(self):
        assert hasattr(PlatformAdapter, "validate_credentials")

    def test_has_get_post_url(self):
        assert hasattr(PlatformAdapter, "get_post_url")
