import pytest
import pandas as pd
from pathlib import Path
import os
import sys
from unittest.mock import patch, MagicMock

# Add the current directory to sys.path so we can import app
sys.path.append(os.path.dirname(__file__))

from app import app, archive

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test that the index route returns 200."""
    with patch.object(archive, 'load_data') as mock_load:
        mock_load.return_value = pd.DataFrame([{
            'thread_id': '123', 'post_no': '123', 'board': 'b', 
            'subject': 'test', 'comment': 'test', 'local_path': '', 
            'timestamp': pd.Timestamp.now(), 'timestamp_str': 'now', 'filename': '',
            'thread_subject': 'test'
        }])
        rv = client.get('/')
        assert rv.status_code == 200
        assert b'Archive Search' in rv.data

def test_load_data_missing_columns():
    """Test that load_data handles missing columns gracefully."""
    # Create a mock parquet file with missing columns
    df_incomplete = pd.DataFrame([{
        'thread_id': '1', 'post_no': '1', 'board': 'b', 'timestamp': 1234567890
    }])
    
    with patch('pandas.read_parquet') as mock_read:
        mock_read.return_value = df_incomplete
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch.object(archive, '_get_soft_deleted_ids') as mock_curation:
                mock_curation.return_value = (set(), set())
                
                df_loaded = archive.load_data(force=True)
                
                # Check that missing columns were added as empty strings
                assert 'subject' in df_loaded.columns
                assert 'comment' in df_loaded.columns
                assert 'filename' in df_loaded.columns
                assert df_loaded.iloc[0]['subject'] == ''
                assert 'timestamp_str' in df_loaded.columns

def test_curate_api(client):
    """Test the curation API."""
    with patch('psycopg2.connect') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        payload = {
            'board': 'b',
            'item_id': '12345',
            'item_type': 'post',
            'action': 'soft_delete'
        }
        rv = client.post('/api/curate', json=payload)
        assert rv.status_code == 200
        assert rv.get_json()['status'] == 'success'
        assert mock_cursor.execute.called

def test_gallery_view(client):
    """Test the gallery view route."""
    rv = client.get('/?view=gallery')
    assert rv.status_code == 200
    # Check if threads container is present (unified layout uses #threads)
    assert b'id="threads"' in rv.data

def test_catalog_view(client):
    """Test the catalog view route."""
    rv = client.get('/?view=catalog')
    assert rv.status_code == 200
    assert b'Catalog' in rv.data

def test_search_filtering(client):
    """Test that searching returns a filtered result (or at least doesn't crash)."""
    rv = client.get('/?q=testquery')
    assert rv.status_code == 200
    assert b'Archive Search' in rv.data

def test_invalid_view(client):
    """Test that an invalid view defaults to list view."""
    rv = client.get('/?view=invalid')
    assert rv.status_code == 200
    # Should show the default list view (Search)
    assert b'Search' in rv.data

def test_thread_view_missing_id(client):
    """Test thread view without an ID."""
    rv = client.get('/?view=thread')
    assert rv.status_code == 200
    assert b'No posts found in this thread.' in rv.data

def test_health_endpoint(client):
    """Test the health check endpoint."""
    rv = client.get('/health')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'ok'

def test_load_data_integrity():
    """Test that load_data returns a DataFrame (even if empty)."""
    df = archive.load_data()
    assert isinstance(df, pd.DataFrame)
