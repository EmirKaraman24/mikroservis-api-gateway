import pytest
import requests
from unittest.mock import patch, MagicMock
from src.dispatcher import Dispatcher, RouteNotFoundError, UpstreamError
from src.router import Router

@pytest.fixture
def test_router():
    router = Router()
    router.add_route("/users", "http://user-service:5001")
    return router

@pytest.fixture
def dispatcher(test_router):
    return Dispatcher(router=test_router)

@patch('src.dispatcher.requests.request')
def test_dispatcher_routes_correctly(mock_request, dispatcher):
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"msg": "success"}
    mock_request.return_value = mock_resp

    # Act
    resp = dispatcher.forward("GET", "/users/1")

    # Assert
    assert resp.status_code == 200
    mock_request.assert_called_once_with(
        method="GET",
        url="http://user-service:5001/users/1",
        headers={},
        data=None,
        params={},
        timeout=10.0
    )

def test_dispatcher_route_not_found(dispatcher):
    with pytest.raises(RouteNotFoundError):
        dispatcher.forward("GET", "/unknown/path")
