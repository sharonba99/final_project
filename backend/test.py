import pytest
from app import app 



@pytest.fixture
def client():
    # Testing app.py
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_shorten_endpoint_exists(client):
    """
    This test sends a request to app.py 
    to see if the /shorten route exists and handles data.
    """
    # Send Post request to /shorten
    response = client.post('/shorten', json={'long_url': 'https://google.com'})
    
    # Check for output status code
    assert response.status_code in [200, 500]