"""
Tests for the Hacky News API
"""
import pytest
import os
import json
from app import create_app

@pytest.fixture
def app():
    """Create and configure the Flask app for testing."""
    # Use a test configuration to avoid affecting the real database
    app = create_app({
        'TESTING': True,
    })
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_index_route(client):
    """Test the index route returns HTTP 200."""
    response = client.get('/')
    assert response.status_code == 200

def test_news_endpoint(client):
    """Test the /news endpoint returns a JSON list."""
    response = client.get('/news')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_categories_endpoint(client):
    """Test the /categories endpoint returns a JSON list."""
    response = client.get('/categories')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_stats_endpoint(client):
    """Test the /stats endpoint returns JSON with expected fields."""
    response = client.get('/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_stories' in data
    assert 'categories' in data
    assert isinstance(data['categories'], list)

def test_search_endpoint_requires_query(client):
    """Test the /search endpoint requires a query parameter."""
    response = client.get('/search')
    assert response.status_code == 400

def test_search_endpoint_with_query(client):
    """Test the /search endpoint with a query parameter."""
    response = client.get('/search?q=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_top_recent_endpoint(client):
    """Test the /stats/top-recent endpoint."""
    response = client.get('/stats/top-recent')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_top_alltime_endpoint(client):
    """Test the /stats/top-alltime endpoint."""
    response = client.get('/stats/top-alltime')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)