# dispatcher/src/app.py
# ─────────────────────
# TDD Green Fazi (Commit 08 - Nuh): Flask HTTP Server Entrypoint.
# Dispatcher microservice'i icin disariya acilan HTTP API.
# Gelen tum HTTP isteklerini yakalar ve Dispatcher sinifina yonledirir.

import logging
from flask import Flask, request, Response
from pymongo import MongoClient

from src.router import Router
from src.dispatcher import Dispatcher, RouteNotFoundError, UpstreamError
from src.auth_middleware import AuthMiddleware, AuthError

# ── LOGLAMA AYARLARI ────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dispatcher-flask")


# ── FLASK APP & BAGIMLILIKLARIN BASLATILMASI ──────────────────────────────

from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)

# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# TODO: Production icin os.environ'dan okunacak
mongo_client = MongoClient("mongodb://mongo:27017/", serverSelectionTimeoutMS=2000)

auth = AuthMiddleware(mongo_client=mongo_client, db_name="dispatcher")

# Basit demo rotalari - Servisler hazir oldugunda gercek adreslerle degistirilecek
routes_map = {
    "/auth":     "http://auth-service:5001",
    "/users":    "http://user-service:5002",
    "/messages": "http://message-service:5003",
}

router = Router(routes_map)
dispatcher = Dispatcher(router=router, timeout=10.0)

logger.info("Dispatcher servisi baslatiliyor...")
logger.info(f"Kayitli Rotalar: {list(routes_map.keys())}")


# ── FLASK ENDPOINT (CATCH-ALL) ─────────────────────────────────────────────

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy(path: str) -> Response:
    """
    Gelen tum HTTP isteklerini karsilar, Authentication kontrolunden gecirir,
    ardindan Dispatcher uzerinden hedef microservice'e yonlendirir.
    """
    full_path = f"/{path}"
    
    logger.info(f"[{request.method}] Istek alindi: {full_path}")
    
    # 1) Auth Middleware Kontrolu (Sadece /auth harici rotalar icin)
    if not full_path.startswith("/auth"):
        try:
            user_id = auth.authenticate(dict(request.headers))
            logger.info(f"Authentication basarili. User: {user_id}")
            
            # Guvenlik/Trace amaciyla user_id bilgisini upstream'e iletebilmek
            # icin headers'a eklenebilir, simdilik standart devam ediyoruz.
            
        except AuthError as e:
            logger.warning(f"Auth Hatasi ({e.status_code}): {str(e)}")
            return Response(response=str(e), status=e.status_code)

    # 2) Dispatcher üzerinden hedef servise yonlendirme
    try:
        # Flask request nesnesinin body'sini byte olarak okuyoruz
        req_body = request.get_data()
        
        upstream_resp = dispatcher.forward(
            method=request.method,
            path=full_path,
            headers=dict(request.headers),
            params=dict(request.args),
            body=req_body
        )
        
        # 3) Upstream yanitini istemciye dondurme
        # Chunked transfer ve content-encoding durumlarina dikkat etmemiz gerekir,
        # simdilik basit Response donuyoruz.
        return Response(
            response=upstream_resp.content,
            status=upstream_resp.status_code,
            headers=dict(upstream_resp.headers)
        )

    except RouteNotFoundError as e:
        logger.warning(f"Rota bulunamadi: {full_path}")
        return Response(response=str(e), status=404)
        
    except ValueError as e:
        logger.warning(f"Gecersiz istek: {str(e)}")
        return Response(response=str(e), status=400)
        
    except UpstreamError as e:
        logger.error(f"Upstream Hatasi ({e.status_code}): {str(e)}")
        return Response(response=str(e), status=e.status_code)
        
    except Exception as e:
        logger.exception("Dispatcher ic hatasi:")
        return Response(response="Internal Server Error", status=500)


if __name__ == "__main__":
    # Sadece gelistirme asamasinda calistirilir
    app.run(host="0.0.0.0", port=5000, debug=True)
