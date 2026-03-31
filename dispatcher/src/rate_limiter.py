# dispatcher/src/rate_limiter.py
# ─────────────────────────────────────────────────────────────
# Commit 32 (Nuh) — 2 Nisan 2026
# feat(dispatcher): implement rate limiting middleware
#
# Sliding window algoritmasıyla IP tabanlı rate limiting.
# Belirli bir zaman penceresi içinde izin verilen maksimum
# istek sayısını aşan IP'ler 429 Too Many Requests alır.
#
# Kullanım:
#   limiter = RateLimiter(limit=100, period=60.0)
#   if not limiter.is_allowed(client_ip):
#       raise RateLimitExceeded(retry_after=limiter.retry_after(client_ip))

from __future__ import annotations

import time
import threading
from collections import deque
from typing import Deque


# ── Exceptions ──────────────────────────────────────────────────────────────

class RateLimitExceeded(Exception):
    """
    İstek limitini aşan istemciler için fırlatılır.

    Attributes:
        status_code:  Her zaman 429 (Too Many Requests)
        retry_after:  İstemcinin kaç saniye beklemesi gerektiği
    """

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            f"Rate limit aşıldı. {retry_after} saniye sonra tekrar deneyin."
        )
        self.status_code: int = 429
        self.retry_after: int = retry_after


# ── RateLimiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding Window algoritmasıyla IP bazlı rate limiter.

    Her IP için son `period` saniye içinde yapılan istekler
    bir deque'de tutulur. İstek sayısı `limit`'i aşarsa
    RateLimitExceeded fırlatılır.

    Kullanım::

        limiter = RateLimiter(limit=100, period=60.0)
        client_ip = request.remote_addr

        if not limiter.is_allowed(client_ip):
            raise RateLimitExceeded(retry_after=limiter.retry_after(client_ip))

        # İzin verilen istek — kayıt et
        limiter.record(client_ip)
    """

    def __init__(
        self,
        limit: int = 100,
        period: float = 60.0,
    ) -> None:
        """
        :param limit:  Zaman penceresi içinde izin verilen maksimum istek sayısı
        :param period: Zaman penceresi (saniye cinsinden)
        """
        if limit <= 0:
            raise ValueError(f"limit pozitif bir tamsayı olmalı, alınan: {limit}")
        if period <= 0:
            raise ValueError(f"period pozitif bir sayı olmalı, alınan: {period}")

        self._limit:  int   = limit
        self._period: float = period

        # {ip: deque of timestamps}
        self._window: dict[str, Deque[float]] = {}

        # Thread güvenliği için kilit
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────

    def is_allowed(self, ip: str) -> bool:
        """
        IP'nin mevcut pencerede istek yapmasına izin var mı?

        Bu metod yalnızca kontrol eder, kayıt yapmaz.
        İzin verilirse `record()` ile kayıt yapılmalıdır.

        :param ip: İstemci IP adresi
        :return:   True → izin var, False → limit aşıldı
        """
        with self._lock:
            self._cleanup(ip)
            return len(self._window.get(ip, deque())) < self._limit

    def record(self, ip: str) -> None:
        """
        IP için yeni bir istek zaman damgası kayıt eder.

        :param ip: İstemci IP adresi
        """
        now = time.monotonic()
        with self._lock:
            if ip not in self._window:
                self._window[ip] = deque()
            self._window[ip].append(now)

    def check_and_record(self, ip: str) -> None:
        """
        Atomic kontrol + kayıt. İzin yoksa RateLimitExceeded fırlatır.

        :param ip: İstemci IP adresi
        :raises RateLimitExceeded: Limit aşıldığında
        """
        with self._lock:
            self._cleanup(ip)
            bucket = self._window.setdefault(ip, deque())

            if len(bucket) >= self._limit:
                # retry_after: en eski isteğin süresi dolana kadar kalan süre
                oldest  = bucket[0]
                wait    = math.ceil(self._period - (time.monotonic() - oldest))
                raise RateLimitExceeded(retry_after=max(1, wait))

            bucket.append(time.monotonic())

    def retry_after(self, ip: str) -> int:
        """
        Verilen IP'nin kaç saniye beklemesi gerektiğini döner.

        :param ip: İstemci IP adresi
        :return:   Bekleme süresi (saniye, tamsayı)
        """
        with self._lock:
            bucket = self._window.get(ip)
            if not bucket:
                return 0
            oldest = bucket[0]
            wait   = self._period - (time.monotonic() - oldest)
            return max(0, math.ceil(wait))

    def remaining(self, ip: str) -> int:
        """
        Verilen IP'nin kalan istek hakkını döner.

        :param ip: İstemci IP adresi
        :return:   Kalan istek sayısı (0'dan küçük olamaz)
        """
        with self._lock:
            self._cleanup(ip)
            used = len(self._window.get(ip, deque()))
            return max(0, self._limit - used)

    def reset(self, ip: str) -> None:
        """
        Verilen IP'nin pencere kaydını temizler (test/admin amaçlı).

        :param ip: İstemci IP adresi
        """
        with self._lock:
            self._window.pop(ip, None)

    def reset_all(self) -> None:
        """Tüm IP'lerin kayıtlarını temizler."""
        with self._lock:
            self._window.clear()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def limit(self) -> int:
        """Yapılandırılmış istek limiti."""
        return self._limit

    @property
    def period(self) -> float:
        """Yapılandırılmış zaman penceresi (saniye)."""
        return self._period

    # ── Private Helpers ───────────────────────────────────────────────────

    def _cleanup(self, ip: str) -> None:
        """
        IP'nin pencere kaydından süresi dolmuş zaman damgalarını kaldırır.
        Bu metod her zaman _lock altında çağrılmalıdır.
        """
        bucket = self._window.get(ip)
        if not bucket:
            return

        cutoff = time.monotonic() - self._period
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        # Boş deque'yi temizle (bellek tasarrufu)
        if not bucket:
            del self._window[ip]


# ── math import (check_and_record için) ────────────────────────────────────
import math
