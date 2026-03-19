# dispatcher/src/dispatcher.py
# ─────────────────────────────
# Dispatcher sinifi, projenin merkezi bilesenidir.
# Sorumlulukları:
#   1. Gelen istegi Router araciligiyla dogru servise yonlendirmek
#   2. requests kutuphanesi ile upstream'e HTTP istegi iletmek
#   3. Upstream yanitini oldugu gibi istemciye dondermek
#
# İleride auth_middleware, logger ve rate_limiter bu sinifa eklenecektir.

from __future__ import annotations

import requests
from requests import Response

from .router import Router


class DispatcherError(Exception):
    """Dispatcher'a ozgu hatalarin base sinifi."""


class RouteNotFoundError(DispatcherError):
    """Hicbir rotayla eslesmeyen path icin firlatilir."""


class UpstreamError(DispatcherError):
    """Upstream servisten hatali yanit geldiginde firlatilir."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class Dispatcher:
    """
    API Gateway gorevini ustlenen merkezi yonlendirici.

    Kullanim::

        dispatcher = Dispatcher()
        response   = dispatcher.forward(method="GET", path="/users/42", headers={}, body=None)
    """

    # Desteklenen HTTP metodlari
    ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})

    def __init__(
        self,
        router: Router | None = None,
        timeout: float = 10.0,
    ) -> None:
        # Bagimlilik enjeksiyonu: test ortaminda sahte router gecirilebilir
        self._router: Router = router or Router()
        self._timeout: float = timeout

    # ── Public API ─────────────────────────────────────────────────────────

    def forward(
        self,
        method: str,
        path: str,
        headers: dict | None = None,
        body: bytes | None = None,
        params: dict | None = None,
    ) -> Response:
        """
        Gelen istegi uygun upstream servise iletir ve yaniti doner.

        :param method:  HTTP metodu ("GET", "POST", ...)
        :param path:    Istek path'i (or. "/users/42")
        :param headers: Orijinal istek baslikları
        :param body:    Ham istek govdesi (bytes)
        :param params:  Query string parametreleri
        :return:        Upstream'den gelen requests.Response nesnesi

        :raises RouteNotFoundError: Hicbir rota eslesmedigi nde
        :raises UpstreamError:      Upstream 5xx dondurdugunde
        :raises ValueError:         Gecersiz HTTP metodu icin
        """
        method = method.upper()
        self._validate_method(method)

        upstream_base = self._router.resolve(path)
        if upstream_base is None:
            raise RouteNotFoundError(
                f"'{path}' icin eslesen rota bulunamadi."
            )

        url = self._build_url(upstream_base, path)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                data=body,
                params=params or {},
                timeout=self._timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise UpstreamError(503, f"Upstream baglanti hatasi: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise UpstreamError(504, f"Upstream zaman asimi: {exc}") from exc

        if response.status_code >= 500:
            raise UpstreamError(
                response.status_code,
                f"Upstream hata dondurdu: HTTP {response.status_code}",
            )

        return response

    # ── Private helpers ────────────────────────────────────────────────────

    def _validate_method(self, method: str) -> None:
        if method not in self.ALLOWED_METHODS:
            raise ValueError(
                f"Desteklenmeyen HTTP metodu: '{method}'. "
                f"Izin verilenler: {sorted(self.ALLOWED_METHODS)}"
            )

    @staticmethod
    def _build_url(base: str, path: str) -> str:
        """Base URL ve path'i birlestir, cift slash'i temizle."""
        return base.rstrip("/") + "/" + path.lstrip("/")
