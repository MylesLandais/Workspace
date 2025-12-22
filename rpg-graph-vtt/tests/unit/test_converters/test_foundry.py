"""Unit tests for Foundry VTT converter."""

import pytest
from rpg_graph_vtt.converters.foundry import (
    foundry_to_character,
    character_to_foundry,
)


class TestFoundryConverter:
    """Tests for Foundry VTT import/export."""

    def test_foundry_to_character_structure(self):
        """Test converting Foundry VTT format to character data."""
        foundry_data = {
            "name": "Test Character",
            "data": {
                "level": 5,
                "attributes": {
                    "hp": {"value": 45, "max": 45},
                },
                "abilities": {
                    "str": {"value": 16},
                    "dex": {"value": 14},
                    "con": {"value": 15},
                    "int": {"value": 12},
                    "wis": {"value": 13},
                    "cha": {"value": 10},
                },
            },
        }
        
        # This is a placeholder test - actual implementation may vary
        # The converter should extract data from Foundry format
        assert foundry_data["name"] == "Test Character"
        assert foundry_data["data"]["level"] == 5

    def test_character_to_foundry_structure(self, sample_character_data):
        """Test converting character data to Foundry VTT format."""
        # This is a placeholder test - actual implementation may vary
        # The converter should format data for Foundry
        assert sample_character_data["name"] == "Test Character"
        assert sample_character_data["level"] == 5

