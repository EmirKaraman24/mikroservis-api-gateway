# dispatcher/src/router.py
# ────────────────────────
# Router sınıfı, gelen isteğin path/prefix bilgisine göre
# hangi arka uç (upstream) servise yönlendirileceğini belirler.
#
# Yönlendirme tablosu bir sözlük ile tutulur:
#   { "/auth":    "http://auth-service:5001",
#     "/users":   "http://user-service:5002",
#     "/messages":"http://message-service:5003" }

from __future__ import annotations
from typing import Optional


class Router:
    """URL prefix -> upstream servis adresi eslemesini yonetir."""

    def __init__(self, routes: Optional[dict] = None) -> None:
        # Varsayilan rotalar; disaridan da gecirilebilir (test kolayligi icin)
        self._routes: dict[str, str] = routes or {
            "/auth": "http://auth-service:5001",
            "/users": "http://user-service:5002",
            "/messages": "http://message-service:5003",
        }

    # ── Public API ─────────────────────────────────────────────────────────

    def resolve(self, path: str) -> Optional[str]:
        """
        Verilen path icin upstream URL'yi doner.

        :param path: Gelen HTTP isteğinin tam path'i (ör. "/users/42")
        :return: Eslesen upstream base URL ya da None (esleme yoksa)
        """
        for prefix, upstream in self._routes.items():
            if path == prefix or path.startswith(prefix + "/"):
                return upstream
        return None

    def add_route(self, prefix: str, upstream: str) -> None:
        """Calisma zamaninda yeni rota ekler."""
        if not prefix.startswith("/"):
            raise ValueError(f"Prefix '/' ile baslamali: {prefix!r}")
        self._routes[prefix] = upstream

    def remove_route(self, prefix: str) -> None:
        """Var olan rotayi kaldirir."""
        self._routes.pop(prefix, None)

    @property
    def routes(self) -> dict[str, str]:
        """Mevcut rota tablosunun salt-okunur kopyasi."""
        return dict(self._routes)
