# dispatcher/tests/test_dispatcher.py
# ─────────────────────────────────────
# Dispatcher sinifinin routing (yonlendirme) davranisini
# test eden birim testleri. 
# Calistirmak icin:
#   pytest dispatcher/tests/test_dispatcher.py -v

import pytest
from unittest.mock import MagicMock, patch

from src.dispatcher import Dispatcher, RouteNotFoundError, UpstreamError
from src.router import Router


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture()
def custom_router() -> Router:
    """Test icin sabit rota tablosuyla olusturulmus Router nesnesi."""
    return Router(routes={
        "/users":    "http://user-service:5002",
        "/messages": "http://message-service:5003",
        "/auth":     "http://auth-service:5001",
    })


@pytest.fixture()
def dispatcher(custom_router: Router) -> Dispatcher:
    """Test rotalarini kullanan Dispatcher ornegi."""
    return Dispatcher(router=custom_router, timeout=5.0)


# ── Grup 1: Rota Cozumleme Testleri ───────────────────────────────────────

class TestRouting:
    """Dispatcher'in dogru upstream'e yonlendirip yonlendirmedigi."""

    def test_get_users_routes_to_user_service(self, dispatcher: Dispatcher) -> None:
        """GET /users istegi kullanici servisine gitmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="GET", path="/users")
            call_kwargs = mock_req.call_args
            assert "http://user-service:5002" in call_kwargs.kwargs["url"]

    def test_post_messages_routes_to_message_service(self, dispatcher: Dispatcher) -> None:
        """POST /messages istegi mesaj servisine gitmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 201

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="POST", path="/messages", body=b'{"text":"hi"}')
            call_kwargs = mock_req.call_args
            assert "http://message-service:5003" in call_kwargs.kwargs["url"]

    def test_auth_path_routes_to_auth_service(self, dispatcher: Dispatcher) -> None:
        """POST /auth/login istegi auth servisine gitmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="POST", path="/auth/login")
            call_kwargs = mock_req.call_args
            assert "http://auth-service:5001" in call_kwargs.kwargs["url"]

    def test_nested_path_resolves_correctly(self, dispatcher: Dispatcher) -> None:
        """GET /users/42 alt yolu da dogru servise gitmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="GET", path="/users/42")
            call_kwargs = mock_req.call_args
            assert "/users/42" in call_kwargs.kwargs["url"]


# ── Grup 2: Route Not Found Testleri ──────────────────────────────────────

class TestRouteNotFound:
    """Bilinmeyen path icin dogru hata firlatilmali."""

    def test_unknown_path_raises_route_not_found(self, dispatcher: Dispatcher) -> None:
        """Tanimlanmamis path RouteNotFoundError firlatmali."""
        with pytest.raises(RouteNotFoundError):
            dispatcher.forward(method="GET", path="/unknown/path")

    def test_empty_path_raises_route_not_found(self, dispatcher: Dispatcher) -> None:
        """Bos path RouteNotFoundError firlatmali."""
        with pytest.raises(RouteNotFoundError):
            dispatcher.forward(method="GET", path="/")

    def test_partial_prefix_does_not_match(self, dispatcher: Dispatcher) -> None:
        """/user (tekil) /users rotasiyla eslesmemeli."""
        with pytest.raises(RouteNotFoundError):
            dispatcher.forward(method="GET", path="/user")


# ── Grup 3: HTTP Metod Validasyonu ────────────────────────────────────────

class TestMethodValidation:
    """Gecersiz HTTP metodlari reddedilmeli."""

    def test_unsupported_method_raises_value_error(self, dispatcher: Dispatcher) -> None:
        """CONNECT metodu ValueError firlatmali."""
        with pytest.raises(ValueError, match="Desteklenmeyen HTTP metodu"):
            dispatcher.forward(method="CONNECT", path="/users")

    def test_lowercase_method_is_accepted(self, dispatcher: Dispatcher) -> None:
        """Kucuk harfli 'get' metodu gecerli olmali (buyuk harfe donusturulur)."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.dispatcher.requests.request", return_value=mock_response):
            response = dispatcher.forward(method="get", path="/users")
            assert response.status_code == 200

    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
    def test_all_allowed_methods_accepted(self, dispatcher: Dispatcher, method: str) -> None:
        """Tum izin verilen HTTP metodlari kabul edilmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.dispatcher.requests.request", return_value=mock_response):
            response = dispatcher.forward(method=method, path="/users")
            assert response.status_code == 200


# ── Grup 4: Upstream Hata Yonetimi ────────────────────────────────────────

class TestUpstreamErrors:
    """Upstream hatalarinda dogru exception firlatilmali."""

    def test_upstream_500_raises_upstream_error(self, dispatcher: Dispatcher) -> None:
        """Upstream HTTP 500 dondustugunde UpstreamError firlatilmali."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("src.dispatcher.requests.request", return_value=mock_response):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert exc_info.value.status_code == 500

    def test_upstream_503_raises_upstream_error(self, dispatcher: Dispatcher) -> None:
        """Upstream 503 dondustugunde UpstreamError firlatilmali."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch("src.dispatcher.requests.request", return_value=mock_response):
            with pytest.raises(UpstreamError):
                dispatcher.forward(method="GET", path="/users")

    def test_connection_error_raises_upstream_error(self, dispatcher: Dispatcher) -> None:
        """Upstream'e ulasalamayinca UpstreamError (503) firlatilmali."""
        import requests as req_lib
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.ConnectionError("refused")):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert exc_info.value.status_code == 503

    def test_timeout_raises_upstream_error_504(self, dispatcher: Dispatcher) -> None:
        """Zaman asiminda UpstreamError (504) firlatilmali."""
        import requests as req_lib
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.Timeout("timed out")):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert exc_info.value.status_code == 504


# ── Grup 5: URL Birlestirme Testleri ──────────────────────────────────────

class TestUrlBuilding:
    """Upstream URL'nin dogru sekilde olusturuldugu dogrulanmali."""

    def test_url_has_no_double_slash(self, dispatcher: Dispatcher) -> None:
        """Base URL ve path arasinda cift slash olmamali."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="GET", path="/users/99")
            url = mock_req.call_args.kwargs["url"]
            assert "//" not in url.replace("http://", "")

    def test_forward_passes_headers(self, dispatcher: Dispatcher) -> None:
        """Istek basliklar upstream'e iletilmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        headers = {"Authorization": "Bearer test-token"}

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="GET", path="/users", headers=headers)
            sent_headers = mock_req.call_args.kwargs["headers"]
            assert sent_headers.get("Authorization") == "Bearer test-token"

    def test_forward_passes_query_params(self, dispatcher: Dispatcher) -> None:
        """Query parametreleri upstream'e iletilmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        params = {"page": "1", "limit": "10"}

        with patch("src.dispatcher.requests.request", return_value=mock_response) as mock_req:
            dispatcher.forward(method="GET", path="/users", params=params)
            sent_params = mock_req.call_args.kwargs["params"]
            assert sent_params == params
