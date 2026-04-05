# dispatcher/tests/test_router.py
# ─────────────────────────────────
# Router sinifinin prefix cozumleme davranisini
# test eden birim testleri.
#
# Calistirmak icin:
#   pytest dispatcher/tests/test_router.py -v

import pytest
from src.router import Router


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture()
def router() -> Router:
    """Sabit rota tablosuyla olusturulmus Router ornegi."""
    return Router(routes={
        "/auth":     "http://auth-service:5001",
        "/users":    "http://user-service:5002",
        "/messages": "http://message-service:5003",
    })


# ── Grup 1: Temel Rota Cozumleme ──────────────────────────────────────────

class TestResolve:
    """Router.resolve() metodunun dogru upstream dondurmesi."""

    def test_exact_prefix_resolves(self, router: Router) -> None:
        """/users path'i user-service'e cozumlenmeli."""
        assert router.resolve("/users") == "http://user-service:5002"

    def test_nested_path_resolves(self, router: Router) -> None:
        """/users/42 alt yolu da user-service'e cozumlenmeli."""
        assert router.resolve("/users/42") == "http://user-service:5002"

    def test_deeply_nested_path_resolves(self, router: Router) -> None:
        """/messages/room/1/history derinlemesine de cozumlenmeli."""
        assert router.resolve("/messages/room/1/history") == "http://message-service:5003"

    def test_auth_prefix_resolves(self, router: Router) -> None:
        """/auth/login path'i auth-service'e cozumlenmeli."""
        assert router.resolve("/auth/login") == "http://auth-service:5001"

    def test_unknown_path_returns_none(self, router: Router) -> None:
        """Bilinmeyen path icin None donmeli."""
        assert router.resolve("/unknown") is None

    def test_root_path_returns_none(self, router: Router) -> None:
        """Kok yol '/' hicbir rotayla eslesmemeli."""
        assert router.resolve("/") is None

    def test_partial_prefix_does_not_match(self, router: Router) -> None:
        """/user (tekil) /users rotasiyla eslesmemeli."""
        assert router.resolve("/user") is None


# ── Grup 2: Rota Ekleme ve Kaldirma ──────────────────────────────────────

class TestRouteManagement:
    """Router'e dinamik rota ekleme ve kaldirma."""

    def test_add_route_resolves_new_path(self, router: Router) -> None:
        """Yeni eklenen rota cozumlenmeli."""
        router.add_route("/reports", "http://report-service:5004")
        assert router.resolve("/reports") == "http://report-service:5004"

    def test_add_route_without_leading_slash_raises(self, router: Router) -> None:
        """Slash olmadan ekleme ValueError firlatmali."""
        with pytest.raises(ValueError):
            router.add_route("noslash", "http://bad-service:9999")

    def test_remove_route_makes_path_unresolvable(self, router: Router) -> None:
        """Kaldirilan rota artik cozumlenmemeli."""
        router.remove_route("/users")
        assert router.resolve("/users") is None

    def test_remove_nonexistent_route_does_not_raise(self, router: Router) -> None:
        """Var olmayan rota kaldirma hata firlatmamali."""
        router.remove_route("/nonexistent")  # Hata vermemeli

    def test_routes_property_returns_copy(self, router: Router) -> None:
        """routes property'si degistirilemez kopya donmeli."""
        routes_copy = router.routes
        routes_copy["/hack"] = "http://evil.com"
        # Orijinal router etkilenmemeli
        assert router.resolve("/hack") is None
