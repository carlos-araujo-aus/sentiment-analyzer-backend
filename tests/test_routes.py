# tests/test_routes.py
import pytest
from api import create_app
from api.models import db, Analysis

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Use a testing configuration
    app = create_app('api.config.DevelopmentConfig')
    app.config.update({
        "TESTING": True,
        # Use an in-memory SQLite database for tests to keep them fast and isolated
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_analyze_success(client, mocker):
    """
    Test a successful analysis, mocking external dependencies.
    """
    # 1. Mock the Watson API call to avoid making a real, slow, and costly API call
    mock_watson_result = {
        "data": {"sentiment": {"label": "positive"}, "emotions": {}, "keywords": []},
        "status": 200
    }
    mocker.patch('api.routes.analyze_text', return_value=mock_watson_result)

    # 2. Mock the database session to verify that we are trying to save
    # This is more of a unit test approach. An integration test would let it write to the in-memory db.
    mock_db_session = mocker.patch('api.routes.db.session')

    # 3. Perform the test request
    response = client.post('/api/analyze', json={'text': 'This is a great test!'})
    
    # 4. Assert the results
    # Check if the response from the endpoint is correct
    assert response.status_code == 200
    assert response.json['sentiment']['label'] == 'positive'
    
    # Check if we attempted to interact with the database correctly
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

    # 5. Verify that a record was created (Integration Test part)
    # This part is commented out because we mocked the session.
    # If we removed the mock_db_session patch, this would work with the in-memory db.
    # assert Analysis.query.count() == 1
    # assert Analysis.query.first().sentiment_label == 'positive'
