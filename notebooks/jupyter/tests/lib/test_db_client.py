"""Tests for lib.db.client module."""

import os
from unittest.mock import patch, MagicMock
import pytest

from lib.db.client import get_db, get_graph


class TestGetDb:
    """Test the get_db convenience function."""

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("lib.db.client.get_connection")
    def test_returns_connection(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        db = get_db()

        assert db is mock_conn
        mock_get_conn.assert_called_once()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("lib.db.client.get_connection")
    def test_returns_same_instance(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        db1 = get_db()
        db2 = get_db()

        assert db1 is db2


class TestGetGraph:
    """Test the get_graph convenience function."""

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("lib.db.client.get_age")
    def test_returns_age_adapter(self, mock_get_age):
        mock_adapter = MagicMock()
        mock_get_age.return_value = mock_adapter

        graph = get_graph()

        assert graph is mock_adapter
        mock_get_age.assert_called_once()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("lib.db.client.get_age")
    def test_passes_graph_name(self, mock_get_age):
        mock_adapter = MagicMock()
        mock_get_age.return_value = mock_adapter

        graph = get_graph(graph_name="custom_graph")

        mock_get_age.assert_called_once_with(graph_name="custom_graph")


class TestModels:
    """Test SQLAlchemy base model."""

    def test_base_model_exists(self):
        from lib.db.models import Base
        assert hasattr(Base, "metadata")

    def test_timestamp_mixin(self):
        from lib.db.models import TimestampMixin
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")

    def test_soft_delete_mixin(self):
        from lib.db.models import SoftDeleteMixin
        assert hasattr(SoftDeleteMixin, "deleted_at")
