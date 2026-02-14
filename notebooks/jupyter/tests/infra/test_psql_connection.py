"""Tests for infra.psql.connection module."""

import os
from unittest.mock import patch, MagicMock
import pytest

from infra.psql.connection import PostgresConnection, get_connection


class TestPostgresConnection:
    """Test PostgresConnection initialization and methods."""

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
        "POSTGRES_DB": "testdb",
    }, clear=False)
    def test_init_from_env(self):
        conn = PostgresConnection()
        assert conn.host == "localhost"
        assert conn.port == "5432"
        assert conn.user == "testuser"
        assert conn.password == "testpass"
        assert conn.dbname == "testdb"

    @patch.dict(os.environ, {}, clear=True)
    def test_init_defaults(self):
        conn = PostgresConnection()
        assert conn.host == "localhost"
        assert conn.port == "5432"
        assert conn.user == "postgres"
        assert conn.password == ""
        assert conn.dbname == "postgres"

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "db.example.com",
        "POSTGRES_PORT": "5433",
        "POSTGRES_USER": "admin",
        "POSTGRES_PASSWORD": "s3cret",
        "POSTGRES_DB": "mydb",
    }, clear=False)
    def test_conn_str(self):
        conn = PostgresConnection()
        assert conn.conn_str == "postgresql://admin:s3cret@db.example.com:5433/mydb"

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.connection.psycopg2.connect")
    def test_get_raw_connection(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        conn = PostgresConnection()
        raw = conn.get_raw_connection()

        mock_connect.assert_called_once_with(
            host="localhost",
            port="5432",
            user="u",
            password="p",
            dbname="d",
        )
        assert raw is mock_conn

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.connection.create_engine")
    def test_get_engine_cached(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        conn = PostgresConnection()
        e1 = conn.get_engine()
        e2 = conn.get_engine()

        assert e1 is e2
        mock_create_engine.assert_called_once()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.connection.create_engine")
    @patch("infra.psql.connection.sessionmaker")
    def test_get_session(self, mock_sessionmaker, mock_create_engine):
        mock_session_cls = MagicMock()
        mock_session_instance = MagicMock()
        mock_session_cls.return_value = mock_session_instance
        mock_sessionmaker.return_value = mock_session_cls

        conn = PostgresConnection()
        session = conn.get_session()

        assert session is mock_session_instance
        mock_sessionmaker.assert_called_once()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.connection.psycopg2.connect")
    def test_execute_query_returns_results(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.description = [("col",)]
        mock_cursor.fetchall.return_value = [{"col": "val"}]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        conn = PostgresConnection()
        results = conn.execute_query("SELECT 1")

        assert results == [{"col": "val"}]
        mock_conn.close.assert_called_once()

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    @patch("infra.psql.connection.psycopg2.connect")
    def test_execute_query_write_commits(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.description = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        conn = PostgresConnection()
        results = conn.execute_query("INSERT INTO t VALUES (1)")

        assert results == []
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_no_hardcoded_paths(self):
        """Ensure no hardcoded home directory paths exist in the module."""
        import inspect
        import infra.psql.connection as mod
        source = inspect.getsource(mod)
        assert "/home/warby" not in source
        assert "/home/" not in source


class TestGetConnection:
    """Test the singleton factory."""

    def setup_method(self):
        import infra.psql.connection as mod
        mod._connection = None

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    def test_returns_singleton(self):
        c1 = get_connection()
        c2 = get_connection()
        assert c1 is c2

    @patch.dict(os.environ, {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
    }, clear=False)
    def test_returns_postgres_connection_instance(self):
        c = get_connection()
        assert isinstance(c, PostgresConnection)
