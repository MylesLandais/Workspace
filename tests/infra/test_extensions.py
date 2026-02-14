"""Tests for infra.psql.extensions module."""

import os
from unittest.mock import patch, MagicMock
import pytest

from infra.psql.extensions import ensure_extensions, health_check


class TestEnsureExtensions:
    """Test extension initialization."""

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.extensions.get_connection")
    def test_creates_age_extension(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        ensure_extensions()

        executed = [c.args[0] for c in mock_cursor.execute.call_args_list]
        assert any("age" in q.lower() for q in executed)

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.extensions.get_connection")
    def test_creates_pgvector_extension(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        ensure_extensions()

        executed = [c.args[0] for c in mock_cursor.execute.call_args_list]
        assert any("vector" in q.lower() for q in executed)

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.extensions.get_connection")
    def test_commits_and_closes(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        ensure_extensions()

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


class TestHealthCheck:
    """Test database health check."""

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.extensions.get_connection")
    def test_healthy(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        result = health_check()

        assert result["status"] == "healthy"
        assert "extensions" in result

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.extensions.get_connection")
    def test_unhealthy_on_connection_error(self, mock_get_conn):
        mock_get_conn.return_value.get_raw_connection.side_effect = Exception("refused")

        result = health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.extensions.get_connection")
    def test_lists_installed_extensions(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.fetchall.return_value = [("age",), ("vector",)]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        result = health_check()

        assert "age" in result["extensions"]
        assert "vector" in result["extensions"]
