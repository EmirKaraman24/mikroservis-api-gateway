# dispatcher/tests/test_edge_cases.py
# ─────────────────────────────────────────────────────────────
# TDD Refactor Fazi (Commit 28 - Nuh): Dispatcher edge case ve
# hata yönetimi testleri.
#
# Bu dosya mevcut testlere ek olarak:
#   - Sınır koşullarını (boundary conditions)
#   - Beklenmeyen/hatalı giriş senaryolarını
#   - Güvenlik ile ilgili edge case'leri test eder.
#
# Çalıştırmak için:
#   pytest dispatcher/tests/test_edge_cases.py -v

import pytest
import requests as req_lib
from unittest.mock import MagicMock, patch, call
from src.dispatcher import Dispatcher, RouteNotFoundError, UpstreamError
from src.router import Router


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def router() -> Router:
    return Router(routes={
        "/users":    "http://user-service:5002",
        "/messages": "http://message-service:5003",
        "/auth":     "http://auth-service:5001",
    })


@pytest.fixture()
def dispatcher(router: Router) -> Dispatcher:
    return Dispatcher(router=router, timeout=5.0)


@pytest.fixture()
def mock_ok_response() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.content = b'{"status": "ok"}'
    resp.headers = {"Content-Type": "application/json"}
    return resp


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 1: PATH EDGE CASE'LERİ
# ═══════════════════════════════════════════════════════════════════════════

class TestPathEdgeCases:
    """Path ile ilgili sınır durumları."""

    def test_path_with_trailing_slash(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """/users/ (sondaki slash) da doğru servise gitmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/users/")
            url = mock_req.call_args.kwargs["url"]
            assert "user-service" in url

    def test_deeply_nested_path(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """/users/42/profile/avatar gibi derin path'ler desteklenmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/users/42/profile/avatar")
            url = mock_req.call_args.kwargs["url"]
            assert "/users/42/profile/avatar" in url

    def test_path_with_query_string_chars(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """Path içinde özel karakterler sorun çıkarmamalı."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(
                method="GET",
                path="/users",
                params={"name": "Emir", "page": "1"}
            )
            sent_params = mock_req.call_args.kwargs["params"]
            assert sent_params["name"] == "Emir"

    def test_nonexistent_top_level_path(self, dispatcher: Dispatcher) -> None:
        """/admin tanımlı değilse RouteNotFoundError atılmalı."""
        with pytest.raises(RouteNotFoundError):
            dispatcher.forward(method="GET", path="/admin/panel")

    def test_case_sensitive_path(self, dispatcher: Dispatcher) -> None:
        """/Users (büyük U) /users rotasıyla eşleşmemeli."""
        with pytest.raises(RouteNotFoundError):
            dispatcher.forward(method="GET", path="/Users")

    def test_numeric_path_segment(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """/messages/999999 gibi büyük ID'ler çalışmalı."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/messages/999999")
            url = mock_req.call_args.kwargs["url"]
            assert "999999" in url

    def test_path_with_unicode(self, dispatcher: Dispatcher) -> None:
        """/users/türkçe gibi unicode path'ler tanımlı rotayla eşleşmeli."""
        resp = MagicMock()
        resp.status_code = 200
        with patch("src.dispatcher.requests.request", return_value=resp) as mock_req:
            dispatcher.forward(method="GET", path="/users/türkçe")
            url = mock_req.call_args.kwargs["url"]
            assert "user-service" in url


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 2: HTTP METOD EDGE CASE'LERİ
# ═══════════════════════════════════════════════════════════════════════════

class TestMethodEdgeCases:
    """HTTP metod doğrulama edge case'leri."""

    @pytest.mark.parametrize("method", [
        "TRACE", "CONNECT", "OPTIONS", "HEAD", "PROPFIND"
    ])
    def test_unsupported_methods_rejected(self, dispatcher: Dispatcher, method: str) -> None:
        """Tanımsız HTTP metodları reddedilmeli."""
        with pytest.raises(ValueError, match="Desteklenmeyen HTTP metodu"):
            dispatcher.forward(method=method, path="/users")

    def test_method_with_extra_spaces(self, dispatcher: Dispatcher) -> None:
        """'GET ' gibi boşluk içeren metodlar reddedilmeli."""
        with pytest.raises(ValueError):
            dispatcher.forward(method="GET ", path="/users")

    def test_empty_method_string(self, dispatcher: Dispatcher) -> None:
        """Boş metod string'i reddedilmeli."""
        with pytest.raises(ValueError):
            dispatcher.forward(method="", path="/users")

    @pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
    def test_lowercase_methods_normalized(self, dispatcher: Dispatcher, method: str, mock_ok_response) -> None:
        """Küçük harfli metodlar büyük harfe dönüştürülerek kabul edilmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method=method, path="/users")
            called_method = mock_req.call_args.kwargs["method"]
            assert called_method == method.upper()


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 3: UPSTREAM HATA YÖNETIMI EDGE CASE'LERİ
# ═══════════════════════════════════════════════════════════════════════════

class TestUpstreamEdgeCases:
    """Upstream servis hata senaryoları."""

    @pytest.mark.parametrize("status_code", [500, 501, 502, 503, 504, 599])
    def test_all_5xx_raise_upstream_error(self, dispatcher: Dispatcher, status_code: int) -> None:
        """Tüm 5xx yanıtlarında UpstreamError fırlatılmalı."""
        resp = MagicMock()
        resp.status_code = status_code
        with patch("src.dispatcher.requests.request", return_value=resp):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert exc_info.value.status_code == status_code

    @pytest.mark.parametrize("status_code", [200, 201, 204, 301, 302, 400, 401, 404])
    def test_non_5xx_do_not_raise(self, dispatcher: Dispatcher, status_code: int) -> None:
        """5xx olmayan yanıtlar exception fırlatmamalı."""
        resp = MagicMock()
        resp.status_code = status_code
        with patch("src.dispatcher.requests.request", return_value=resp):
            result = dispatcher.forward(method="GET", path="/users")
            assert result.status_code == status_code

    def test_upstream_connection_refused(self, dispatcher: Dispatcher) -> None:
        """Connection refused → UpstreamError(503) olmalı."""
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.ConnectionError("Connection refused")):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="POST", path="/messages")
            assert exc_info.value.status_code == 503

    def test_upstream_dns_failure(self, dispatcher: Dispatcher) -> None:
        """DNS çözümleme hatası → UpstreamError(503) olmalı."""
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.ConnectionError("Failed to resolve hostname")):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/auth/login")
            assert exc_info.value.status_code == 503
            assert "503" in str(exc_info.value.status_code) or exc_info.value.status_code == 503

    def test_upstream_read_timeout(self, dispatcher: Dispatcher) -> None:
        """Read timeout → UpstreamError(504) olmalı."""
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.ReadTimeout("Read timed out")):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert exc_info.value.status_code == 504

    def test_upstream_connect_timeout(self, dispatcher: Dispatcher) -> None:
        """Connect timeout da UpstreamError(503) olmalı (Connection error)."""
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.ConnectTimeout("Connect timed out")):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert exc_info.value.status_code == 503

    def test_upstream_error_message_contains_status(self, dispatcher: Dispatcher) -> None:
        """UpstreamError mesajı HTTP durum kodunu içermeli."""
        resp = MagicMock()
        resp.status_code = 503
        with patch("src.dispatcher.requests.request", return_value=resp):
            with pytest.raises(UpstreamError) as exc_info:
                dispatcher.forward(method="GET", path="/users")
            assert "503" in str(exc_info.value)


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 4: BODY & HEADER EDGE CASE'LERİ
# ═══════════════════════════════════════════════════════════════════════════

class TestRequestDataEdgeCases:
    """İstek verisi (body, header) edge case'leri."""

    def test_empty_body_forwarded_as_none(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """Body verilmezse None olarak iletilmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="POST", path="/messages")
            assert mock_req.call_args.kwargs["data"] is None

    def test_large_body_forwarded(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """Büyük body'ler (1MB+) sorunsuz iletilmeli."""
        big_body = b"x" * (1024 * 1024)  # 1 MB
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="POST", path="/messages", body=big_body)
            assert mock_req.call_args.kwargs["data"] == big_body

    def test_headers_not_mutated(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """Orijinal header dict'i değiştirilmemeli."""
        original_headers = {"Authorization": "Bearer abc", "Content-Type": "application/json"}
        headers_copy = dict(original_headers)
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response):
            dispatcher.forward(method="GET", path="/users", headers=original_headers)
        assert original_headers == headers_copy

    def test_none_headers_defaults_to_empty_dict(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """headers=None verildiğinde {} olarak iletilmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/users", headers=None)
            assert mock_req.call_args.kwargs["headers"] == {}

    def test_none_params_defaults_to_empty_dict(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """params=None verildiğinde {} olarak iletilmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/users", params=None)
            assert mock_req.call_args.kwargs["params"] == {}

    def test_multiple_query_params(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """Çok sayıda query parametresi doğru iletilmeli."""
        params = {"page": "1", "limit": "10", "sort": "name", "order": "asc", "filter": "active"}
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/users", params=params)
            assert mock_req.call_args.kwargs["params"] == params


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 5: TIMEOUT KONFİGÜRASYONU
# ═══════════════════════════════════════════════════════════════════════════

class TestTimeoutConfig:
    """Timeout konfigürasyon edge case'leri."""

    def test_custom_timeout_passed_to_requests(self, router: Router, mock_ok_response) -> None:
        """Dispatcher'a verilen timeout, requests'e iletilmeli."""
        d = Dispatcher(router=router, timeout=3.5)
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            d.forward(method="GET", path="/users")
            assert mock_req.call_args.kwargs["timeout"] == 3.5

    def test_zero_timeout_still_passes(self, router: Router, mock_ok_response) -> None:
        """timeout=0 (hemen timeout) da iletilmeli."""
        d = Dispatcher(router=router, timeout=0)
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            d.forward(method="GET", path="/users")
            assert mock_req.call_args.kwargs["timeout"] == 0

    def test_default_timeout_is_10(self, router: Router, mock_ok_response) -> None:
        """Varsayılan timeout 10 saniye olmalı."""
        d = Dispatcher(router=router)
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            d.forward(method="GET", path="/users")
            assert mock_req.call_args.kwargs["timeout"] == 10.0


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 6: URL OLUŞTURMA EDGE CASE'LERİ
# ═══════════════════════════════════════════════════════════════════════════

class TestUrlBuildingEdgeCases:
    """URL birleştirme edge case'leri."""

    def test_no_double_slash_with_trailing_base(self, router: Router, mock_ok_response) -> None:
        """Base URL sona / ile bitse bile çift slash oluşmamalı."""
        r = Router(routes={"/users": "http://user-service:5002/"})
        d = Dispatcher(router=r)
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            d.forward(method="GET", path="/users/42")
            url = mock_req.call_args.kwargs["url"]
            assert "//" not in url.replace("http://", "")

    def test_url_preserves_full_path(self, dispatcher: Dispatcher, mock_ok_response) -> None:
        """/users/42/orders/7 tam olarak URL'de yer almalı."""
        with patch("src.dispatcher.requests.request", return_value=mock_ok_response) as mock_req:
            dispatcher.forward(method="GET", path="/users/42/orders/7")
            url = mock_req.call_args.kwargs["url"]
            assert url.endswith("/users/42/orders/7")
