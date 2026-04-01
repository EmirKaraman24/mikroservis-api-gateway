# dispatcher/src/__init__.py
# ─────────────────────────────
# Dispatcher servisinin kaynak paketi.
# Bu dosya, src/ klasörünü Python paketi olarak tanımlar.
# Commit 39 (Emir) — 5 Nisan 2026: tüm testler gözden geçirildi, eksik
# export'lar tamamlandı.

from .router import Router
from .dispatcher import Dispatcher, DispatcherError, RouteNotFoundError, UpstreamError
from .auth_middleware import AuthMiddleware, AuthError
from .rate_limiter import RateLimiter, RateLimitExceeded
from .health import HealthChecker

__all__ = [
    # Routing
    "Router",
    # Dispatcher core
    "Dispatcher",
    "DispatcherError",
    "RouteNotFoundError",
    "UpstreamError",
    # Auth
    "AuthMiddleware",
    "AuthError",
    # Rate limiting
    "RateLimiter",
    "RateLimitExceeded",
    # Health check
    "HealthChecker",
]
