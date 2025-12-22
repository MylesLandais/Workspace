"""Unit tests for graph query builders."""

import pytest
from uuid import UUID
from unittest.mock import Mock

from rpg_graph_vtt.graph.queries import CharacterQueries, PartyQueries


class TestCharacterQueries:
    """Tests for CharacterQueries."""

    def test_create_character_query(self, mock_neo4j_connection, sample_character_data):
        """Test character creation query."""
        # Mock the execute_write to capture the query
        mock_neo4j_connection.execute_write = Mock(return_value=None)
        
        uuid = CharacterQueries.create_character(
            sample_character_data,
            mock_neo4j_connection
        )
        
        assert isinstance(uuid, UUID)
        assert mock_neo4j_connection.execute_write.called

    def test_get_character_query(self, mock_neo4j_connection):
        """Test getting a character by UUID."""
        # Mock execute_read to return a character
        mock_record = Mock()
        mock_record.__getitem__ = Mock(return_value={"uuid": "123e4567-e89b-12d3-a456-426614174000", "name": "Test"})
        mock_neo4j_connection.execute_read = Mock(return_value=[mock_record])
        
        uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
        result = CharacterQueries.get_character(uuid, mock_neo4j_connection)
        
        assert mock_neo4j_connection.execute_read.called
        # Result may be None if character not found, or dict if found
        assert result is None or isinstance(result, dict)


class TestPartyQueries:
    """Tests for PartyQueries."""

    def test_create_party_query(self, mock_neo4j_connection, sample_party_data):
        """Test party creation query."""
        mock_neo4j_connection.execute_write = Mock(return_value=None)
        
        party_name = PartyQueries.create_party(
            sample_party_data,
            mock_neo4j_connection
        )
        
        assert party_name == sample_party_data["name"]
        assert mock_neo4j_connection.execute_write.called

    def test_get_all_parties_query(self, mock_neo4j_connection):
        """Test getting all parties."""
        mock_neo4j_connection.execute_read = Mock(return_value=[])
        
        result = PartyQueries.get_all_parties(mock_neo4j_connection)
        
        assert isinstance(result, list)
        assert mock_neo4j_connection.execute_read.called

