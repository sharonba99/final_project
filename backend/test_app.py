import pytest
from app import app
from unittest.mock import patch, MagicMock
import psycopg2

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Health Check
def test_health_basic(client):
    """Test /health"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'up'

def test_health_live(client):
    """Test /health/live"""
    response = client.get('/health/live')
    assert response.status_code == 200
    assert response.json['status'] == 'live'

# Readiness Tests
@patch('psycopg2.connect')
def test_health_ready_success(mock_connect, client):
    """Test /health/ready when database is connected"""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    response = client.get('/health/ready')
    
    assert response.status_code == 200
    assert response.json['status'] == 'ready'
    assert response.json['database'] == 'connected'
    mock_cur.execute.assert_called_with("SELECT 1")

@patch('psycopg2.connect')
def test_health_ready_fail(mock_connect, client):
    """Test /health/ready when database connection fails"""
    mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
    
    response = client.get('/health/ready')
    
    assert response.status_code == 503
    assert response.json['status'] == 'not ready'
    assert "Connection refused" in response.json['reason']

# Test URL Validation Logic
def test_shorten_invalid_url(client):
    response = client.post('/shorten', json={'long_url': 'not-a-url'})
    assert response.status_code == 400
    assert b"Invalid URL format" in response.data

# Test Metrics Endpoint
def test_metrics_endpoint(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b"http_requests_total" in response.data

# Shorten URL test
@patch('app.get_conn')
def test_shorten_url_success(mock_get_conn, client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    response = client.post('/shorten', json={'long_url': 'https://google.com'})
    
    assert response.status_code == 201
    assert 'short_code' in response.json
    mock_cur.execute.assert_called() 

# Redirect URL test
@patch('app.get_conn')
def test_redirect_not_found(mock_get_conn, client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    # Simulate "No record found" in DB
    mock_cur.fetchone.return_value = None
    
    response = client.get('/r/fakeCode')
    assert response.status_code == 404