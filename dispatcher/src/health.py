# dispatcher/src/health.py
# ─────────────────────────────────────────────────────────────
# feat(dispatcher): implement health check endpoint GET /health
#
# GET /health → tüm bağımlı servislerin durumunu döner.
# Yanıt:
#   200 { "status": "ok", "services": { "<name>": "ok"|"down" } }
#   503 { "status": "degraded", ... }  (en az bir servis çökmüşse)
#
# Bağımlılık enjeksiyonu ile test edilebilir tasarım:
#   - service_urls: kontrol edilecek servis adresleri dict'i
#   - http_get_fn:  gerçek HTTP yerine test stub'ı geçirilebilir

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Upstream servislerin /health (veya /) endpoint'lerini ping'ler
    ve özetlenmiş bir durum raporu döner.

    Kullanım::

        checker = HealthChecker(service_urls={
            "auth-service":    "http://auth-service:5002",
            "user-service":    "http://user-service:5001",
            "message-service": "http://message-service:5003",
        })
        result = checker.check()
        # {"status": "ok", "services": {"auth-service": "ok", ...}}
    """

    def __init__(
        self,
        service_urls: dict[str, str],
        timeout: float = 2.0,
        http_get_fn: Optional[Callable] = None,
    ) -> None:
        """
        :param service_urls: {"servis-adı": "http://host:port"} eşlemesi
        :param timeout:      Her ping için maksimum bekleme süresi (sn)
        :param http_get_fn:  Test sırasında gerçek requests.get yerine
                             geçirilecek callable (opsiyonel)
        """
        self._urls: dict[str, str] = service_urls
        self._timeout: float = timeout
        self._get = http_get_fn or self._default_get

    # ── Public API ──────────────────────────────────────────────────────────

    def check(self) -> dict:
        """
        Tüm servisleri ping'ler ve özet döner.

        :return: {
            "status":   "ok" | "degraded",
            "services": { "<name>": "ok" | "down" }
        }
        """
        services: dict[str, str] = {}
        all_ok = True

        for name, base_url in self._urls.items():
            ok = self._ping(name, base_url)
            services[name] = "ok" if ok else "down"
            if not ok:
                all_ok = False

        return {
            "status": "ok" if all_ok else "degraded",
            "services": services,
        }

    # ── Private helpers ─────────────────────────────────────────────────────

    def _ping(self, name: str, base_url: str) -> bool:
        """
        Servise tek bir GET isteği atar; herhangi bir yanıt 'ok' sayılır.
        Bağlantı hatası veya timeout → 'down' sayılır.
        """
        url = base_url.rstrip("/") + "/health"
        try:
            resp = self._get(url, timeout=self._timeout)
            # 2xx veya 4xx dönse bile servis ayaktadır
            ok = resp.status_code < 500
            logger.info(f"[health] {name} → HTTP {resp.status_code} → {'ok' if ok else 'down'}")
            return ok
        except Exception as exc:
            logger.warning(f"[health] {name} ping başarısız: {exc}")
            return False

    @staticmethod
    def _default_get(url: str, timeout: float):
        """Gerçek HTTP GET — sadece production kullanımında çağrılır."""
        import requests
        return requests.get(url, timeout=timeout)
