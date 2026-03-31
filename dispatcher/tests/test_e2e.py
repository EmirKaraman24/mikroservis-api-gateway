import pytest
import json
from unittest.mock import patch, MagicMock
from src.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_check_e2e(client):
    """
    Test the /health endpoint directly.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == {"status": "UP", "service": "dispatcher"}

@patch('src.app.auth.authenticate')
@patch('src.dispatcher.requests.request')
def test_proxy_e2e_success(mock_request, mock_auth, client):
    """
    Test a full proxy request lifecycle for a protected route (/users).
    """
    # Mock Authentication to succeed
    mock_auth.return_value = "user_123"
    
    # Mock Upstream Microservice response
    mock_upstream_resp = MagicMock()
    mock_upstream_resp.status_code = 200
    mock_upstream_resp.content = b'{"msg": "success"}'
    mock_upstream_resp.headers = {"Content-Type": "application/json"}
    mock_request.return_value = mock_upstream_resp
    
    # Send request with simulated proxy path
    response = client.get("/users/1", headers={"Authorization": "Bearer token"})
    
    # Assertions
    assert response.status_code == 200
    assert response.data == b'{"msg": "success"}'
    mock_auth.assert_called_once()
    mock_request.assert_called_once()

@patch('src.app.auth.authenticate')
def test_proxy_e2e_auth_failure(mock_auth, client):
    """
    Test E2E when Authentication Middleware fails.
    """
    from src.auth_middleware import AuthError
    mock_auth.side_effect = AuthError("Invalid Token", status_code=401)
    
    response = client.get("/users", headers={"Authorization": "Bearer invalid"})
    
    assert response.status_code == 401
    assert "Invalid Token" in response.data.decode()
