import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app

@pytest.fixture
def client():
    """Sets up a test client for the Flask app."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@patch('app.get_conn')
def test_shorten_url_mocked(mock_get_conn, client):
    """Tests the /shorten path without a real database."""
    
    # Creating mock cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ["http://google.com"]
    
    # Creating mock connection 
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    # Make request to the /shorten path
    response = client.post('/shorten', json={'long_url': 'https://google.com'})

 
    assert 200 <= response.status_code < 300

    mock_get_conn.assert_called_once()