# Dispatcher Service
# ─────────────────
# Bu klasörde Dispatcher (API Gateway) servisi yer almaktadır.

dispatcher/
├── src/
│   ├── __init__.py
│   ├── app.py             ← Flask HTTP giriş noktası
│   ├── dispatcher.py      ← Ana yönlendirme sınıfı
│   ├── router.py          ← URL → servis eşleme
│   ├── auth_middleware.py ← Token doğrulama
│   ├── logger.py          ← Trafik loglama
│   ├── metrics.py         ← Prometheus metrikleri
│   ├── rate_limiter.py    ← Rate limiting
│   └── health.py          ← /health endpoint
├── tests/
│   ├── __init__.py
│   ├── test_dispatcher.py
│   ├── test_auth_middleware.py
│   └── test_error_handling.py
├── Dockerfile
└── requirements.txt
