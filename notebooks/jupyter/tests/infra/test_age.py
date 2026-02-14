"""Tests for infra.psql.age module."""

import os
from unittest.mock import patch, MagicMock, call
import pytest

from infra.psql.age import AGEAdapter, get_age


class TestAGEAdapter:
    """Test AGEAdapter initialization and query execution."""

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_init_default_graph(self, mock_get_conn):
        adapter = AGEAdapter()
        assert adapter.graph_name == "archive_graph"
        assert adapter._initialized is False

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_init_custom_graph(self, mock_get_conn):
        adapter = AGEAdapter(graph_name="my_graph")
        assert adapter.graph_name == "my_graph"

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_initialize_graph_runs_setup_queries(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        adapter = AGEAdapter()
        adapter._initialize_graph()

        assert adapter._initialized is True
        assert mock_cursor.execute.call_count >= 3
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_initialize_graph_only_once(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        adapter = AGEAdapter()
        adapter._initialize_graph()
        adapter._initialize_graph()

        assert mock_get_conn.return_value.get_raw_connection.call_count == 1

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_execute_query(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"v": '{"id": 1}'}]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        adapter = AGEAdapter()
        adapter._initialized = True
        results = adapter.execute_query("MATCH (n) RETURN n")

        assert len(results) == 1
        mock_conn.close.assert_called()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_execute_query_error_raises(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [None, Exception("AGE error")]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.get_raw_connection.return_value = mock_conn

        adapter = AGEAdapter()
        adapter._initialized = True

        with pytest.raises(Exception, match="AGE error"):
            adapter.execute_query("INVALID CYPHER")

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_execute_write_delegates(self, mock_get_conn):
        adapter = AGEAdapter()
        adapter._initialized = True
        adapter.execute_query = MagicMock(return_value=[])

        result = adapter.execute_write("CREATE (n:Node {name: 'test'})")
        adapter.execute_query.assert_called_once_with(
            "CREATE (n:Node {name: 'test'})", None
        )

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_execute_read_delegates(self, mock_get_conn):
        adapter = AGEAdapter()
        adapter._initialized = True
        adapter.execute_query = MagicMock(return_value=[{"v": "data"}])

        result = adapter.execute_read("MATCH (n) RETURN n")
        adapter.execute_query.assert_called_once_with("MATCH (n) RETURN n", None)

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_context_manager(self, mock_get_conn):
        with AGEAdapter() as adapter:
            assert isinstance(adapter, AGEAdapter)


class TestGetAge:
    """Test singleton factory."""

    def setup_method(self):
        import infra.psql.age as mod
        mod._age_adapter = None

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.age.get_connection")
    def test_returns_singleton(self, mock_get_conn):
        a1 = get_age()
        a2 = get_age()
        assert a1 is a2
