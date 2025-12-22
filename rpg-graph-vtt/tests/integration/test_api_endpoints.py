"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

# Integration tests require the FastAPI server to be running
# or use TestClient for in-memory testing


class TestAPIEndpoints:
    """Integration tests for FastAPI endpoints."""

    @pytest.mark.integration
    def test_list_characters_endpoint(self):
        """Test GET /api/characters endpoint."""
        # This test requires the server or TestClient
        pytest.skip("Requires FastAPI server or TestClient setup")

    @pytest.mark.integration
    def test_get_character_endpoint(self):
        """Test GET /api/characters/{uuid} endpoint."""
        pytest.skip("Requires FastAPI server or TestClient setup")

    @pytest.mark.integration
    def test_list_parties_endpoint(self):
        """Test GET /api/parties endpoint."""
        pytest.skip("Requires FastAPI server or TestClient setup")

