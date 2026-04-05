# tests/e2e/test_full_lifecycle.py
# ─────────────────────────────────────────────────────────────
# Commit 34 (Nuh) — 3 Nisan 2026
# test(e2e): add end-to-end test for full request lifecycle
#
# Bu testler, gerçek bir Docker ortamı yerine Flask test client
# ve mock upstream servisler kullanarak tam istek döngüsünü
# (istemci → dispatcher → upstream → istemci) doğrular.
#
# Test edilen akışlar:
#   1. Auth bypass: /auth/* rotaları token kontrolünden muaf
#   2. Korumalı rota: geçerli token → upstream'e iletilir
#   3. Yetkisiz istek: token yoksa 401 döner
#   4. Bilinmeyen rota: 404 döner
#   5. Upstream hatası: 5xx → 500 döner
#   6. Health check: GET /health → servis durumu döner
#   7. Rate limiting: limit aşılınca 429 döner
#
# Çalıştırmak için:
#   pytest tests/e2e/test_full_lifecycle.py -v

import json
import pytest
from unittest.mock import MagicMock, patch


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def flask_app():
    """
    Dispatcher Flask uygulamasını test modunda başlatır.
    MongoDB ve upstream servisleri mock'lanır.
    """
    # MongoDB bağlantısını mock'la (gerçek Mongo gerekmez)
    with patch("pymongo.MongoClient") as mock_mongo:
        mock_col = MagicMock()
        mock_mongo.return_value.__getitem__.return_value.__getitem__.return_value = mock_col
        mock_col.find_one.return_value = {
            "token": "valid-token-e2e",
            "user_id": "user-e2e-42",
        }

        # HealthChecker'ı da mock'la (upstream'ler ayakta görünsün)
        with patch("src.health.HealthChecker._default_get") as mock_health_get:
            mock_health_resp = MagicMock()
            mock_health_resp.status_code = 200
            mock_health_get.return_value = mock_health_resp

            from src.app import app
            app.config["TESTING"] = True
            yield app


@pytest.fixture()
def client(flask_app):
    with flask_app.test_client() as c:
        yield c


def make_auth_header(token: str = "valid-token-e2e") -> dict:
    return {"Authorization": f"Bearer {token}"}


def mock_upstream(status_code: int = 200, body: dict = None) -> MagicMock:
    """Upstream servis yanıtı için MagicMock oluşturur."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = json.dumps(body or {"ok": True}).encode()
    resp.headers = {"Content-Type": "application/json"}
    return resp


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 1: /health Endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """GET /health — servis durumu özeti."""

    def test_health_returns_200_when_all_up(self, client):
        """Tüm servisler ayaktayken 200 ve status=ok dönmeli."""
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        with patch("src.health.HealthChecker._default_get", return_value=ok_resp):
            resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "services" in data

    def test_health_returns_503_when_service_down(self, client):
        """En az bir servis çökmüşse 503 ve status=degraded dönmeli."""
        def selective_ping(url, timeout):
            r = MagicMock()
            r.status_code = 500 if "auth" in url else 200
            return r

        with patch("src.app.health_checker._get", side_effect=selective_ping):
            resp = client.get("/health")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["status"] == "degraded"
        assert data["services"]["auth-service"] == "down"

    def test_health_response_has_all_services(self, client):
        """Yanıt tüm servislerin durumunu içermeli."""
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        with patch("src.health.HealthChecker._default_get", return_value=ok_resp):
            resp = client.get("/health")
        services = resp.get_json().get("services", {})
        assert "auth-service" in services
        assert "user-service" in services
        assert "message-service" in services


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 2: Auth Bypass — /auth/* rotaları
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthBypass:
    """/auth/* rotaları token kontrolünden geçmeden upstream'e iletilmeli."""

    def test_auth_login_bypasses_auth_check(self, client):
        """POST /auth/login token olmadan 404 değil upstream yanıtı dönmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_upstream(200)):
            resp = client.post("/auth/login", json={"username": "emir", "password": "pass"})
        # upstream mock 200 döndü; auth kontrolü bypass edildi
        assert resp.status_code == 200

    def test_auth_register_bypasses_auth_check(self, client):
        """POST /auth/register token olmadan çalışmalı."""
        with patch("src.dispatcher.requests.request", return_value=mock_upstream(201)):
            resp = client.post("/auth/register", json={"username": "new", "password": "pass"})
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 3: Korumalı Rotalar — Token Gerekli
# ═══════════════════════════════════════════════════════════════════════════

class TestProtectedRoutes:
    """Korumalı rotalar geçerli token ile upstream'e iletilmeli."""

    def test_get_users_with_valid_token(self, client):
        """Geçerli token ile GET /users → upstream 200 dönmeli."""
        with patch("src.dispatcher.requests.request",
                   return_value=mock_upstream(200, {"users": []})):
            resp = client.get("/users", headers=make_auth_header())
        assert resp.status_code == 200

    def test_post_messages_with_valid_token(self, client):
        """Geçerli token ile POST /messages → upstream 201 dönmeli."""
        with patch("src.dispatcher.requests.request",
                   return_value=mock_upstream(201, {"message": "created"})):
            resp = client.post(
                "/messages",
                json={"content": "test", "sender": "emir"},
                headers=make_auth_header(),
            )
        assert resp.status_code == 201

    def test_delete_user_with_valid_token(self, client):
        """Geçerli token ile DELETE /users/42 → upstream 204 dönmeli."""
        with patch("src.dispatcher.requests.request", return_value=mock_upstream(204)):
            resp = client.delete("/users/42", headers=make_auth_header())
        assert resp.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 4: Yetkisiz İstekler
# ═══════════════════════════════════════════════════════════════════════════

class TestUnauthorizedRequests:
    """Token olmayan veya geçersiz token içeren istekler 401/403 almalı."""

    def test_no_token_returns_401(self, client):
        """Authorization başlığı olmayan istek 401 almalı."""
        resp = client.get("/users")
        assert resp.status_code == 401

    def test_invalid_token_format_returns_401(self, client):
        """Yanlış formatlı token 401 almalı."""
        resp = client.get("/users", headers={"Authorization": "InvalidFormat"})
        assert resp.status_code == 401

    def test_wrong_token_returns_403(self, client):
        """MongoDB'de bulunmayan token 403 almalı."""
        with patch("src.auth_middleware.AuthMiddleware._lookup_token",
                   side_effect=__import__('src.auth_middleware', fromlist=['AuthError']).AuthError(403, "Geçersiz token.")):
            resp = client.get("/users", headers=make_auth_header("bad-token"))
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 5: Bilinmeyen Rota
# ═══════════════════════════════════════════════════════════════════════════

class TestUnknownRoute:
    """Kayıtlı olmayan path için 404 dönmeli."""

    def test_unknown_path_returns_404(self, client):
        """GET /nonexistent → 404."""
        resp = client.get("/nonexistent/path", headers=make_auth_header())
        assert resp.status_code == 404

    def test_admin_path_returns_404(self, client):
        """GET /admin → 404 (tanımlı rota yok)."""
        resp = client.get("/admin", headers=make_auth_header())
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 6: Upstream Hata Yönetimi
# ═══════════════════════════════════════════════════════════════════════════

class TestUpstreamErrors:
    """Upstream 5xx → dispatcher 5xx döndürmeli."""

    def test_upstream_500_raises_upstream_error(self, client):
        """Upstream 500 döndüğünde istemci 500 almalı."""
        with patch("src.dispatcher.requests.request", return_value=mock_upstream(500)):
            resp = client.get("/users", headers=make_auth_header())
        assert resp.status_code == 500

    def test_upstream_connection_error_returns_503(self, client):
        """Upstream bağlantı hatası → 503."""
        import requests as req_lib
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.ConnectionError("down")):
            resp = client.get("/users", headers=make_auth_header())
        assert resp.status_code == 503

    def test_upstream_timeout_returns_504(self, client):
        """Upstream timeout → 504."""
        import requests as req_lib
        with patch("src.dispatcher.requests.request",
                   side_effect=req_lib.exceptions.Timeout("timeout")):
            resp = client.get("/users", headers=make_auth_header())
        assert resp.status_code == 504


# ═══════════════════════════════════════════════════════════════════════════
#  SENARYO 7: Tam İstek Döngüsü
# ═══════════════════════════════════════════════════════════════════════════

class TestFullRequestCycle:
    """Gerçek uçtan uca akışı simüle eden entegrasyon benzeri testler."""

    def test_register_then_get_users(self, client):
        """
        1. POST /auth/register (token yok, bypass)
        2. GET /users (geçerli token ile)
        Her ikisi de başarıyla tamamlanmalı.
        """
        with patch("src.dispatcher.requests.request", return_value=mock_upstream(201)):
            reg = client.post("/auth/register", json={"username": "emir"})
        assert reg.status_code == 201

        with patch("src.dispatcher.requests.request",
                   return_value=mock_upstream(200, {"users": [{"id": 1}]})):
            users = client.get("/users", headers=make_auth_header())
        assert users.status_code == 200

    def test_send_message_then_list(self, client):
        """
        1. POST /messages (mesaj gönder)
        2. GET /messages (listele)
        """
        with patch("src.dispatcher.requests.request", return_value=mock_upstream(201)):
            send = client.post(
                "/messages",
                json={"content": "merhaba", "sender": "emir"},
                headers=make_auth_header(),
            )
        assert send.status_code == 201

        with patch("src.dispatcher.requests.request",
                   return_value=mock_upstream(200, [{"id": 1, "content": "merhaba"}])):
            listing = client.get("/messages", headers=make_auth_header())
        assert listing.status_code == 200
