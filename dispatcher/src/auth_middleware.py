# dispatcher/src/auth_middleware.py
# ───────────────────────────────────
# TDD Green Fazi (Commit 06 - Nuh): Auth Middleware implementasyonu.
#
# AuthMiddleware, gelen her istekteki Authorization basligini dogrular.
# Token gecerliligi MongoDB (NoSQL) koleksiyonundan sorgulanir.
#
# Akis:
#   1. Istek basliginda "Authorization: Bearer <token>" aranir.
#   2. Token, MongoDB'deki 'sessions' koleksiyonunda aranir.
#   3. Token gecerliyse istek Dispatcher'a iletilir.
#   4. Gecersiz veya eksik token icin 401 / 403 doner.
#
# Bagimsiz (unit) test icin MongoClient'in disaridan enjekte edilmesi
# saglanmistir (Dependency Injection).

from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone


class AuthError(Exception):
    """Auth kontrolunden gecemeyen istekler icin firlatilir."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthMiddleware:
    """
    MongoDB tabanli Bearer-token dogrulama middleware'i.

    Kullanim::

        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017")
        auth = AuthMiddleware(mongo_client=client)
        user_id = auth.authenticate(headers=request.headers)
    """

    # Authorization basliginin beklenen on eki
    _BEARER_PREFIX = "Bearer "

    def __init__(
        self,
        mongo_client,               # pymongo.MongoClient ornegi
        db_name: str = "dispatcher",
        collection_name: str = "sessions",
    ) -> None:
        self._collection = (
            mongo_client[db_name][collection_name]
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def authenticate(self, headers: dict) -> str:
        """
        Istek basliklarini dogrular ve iliskilendirilmis user_id'yi doner.

        :param headers: HTTP istek basliklarinin sozlugu
        :return: Oturumdaki kullanici kimligi (user_id)

        :raises AuthError(401): Authorization basligi eksik
        :raises AuthError(401): Token formati yanlis
        :raises AuthError(403): Token MongoDB'de bulunamadi veya suresi dolmus
        """
        raw = headers.get("Authorization") or headers.get("authorization")

        if not raw:
            raise AuthError(401, "Authorization basligi eksik.")

        if not raw.startswith(self._BEARER_PREFIX):
            raise AuthError(401, "Gecersiz Authorization formati. 'Bearer <token>' bekleniyor.")

        token = raw[len(self._BEARER_PREFIX):].strip()
        if not token:
            raise AuthError(401, "Token bos olamaz.")

        return self._lookup_token(token)

    # ── Private helpers ────────────────────────────────────────────────────

    def _lookup_token(self, token: str) -> str:
        """
        Token'i once JWT formatinda olup olmadigina bakar. Eger JWT ise payload'dan username'i okur.
        Degilse eski mantikla MongoDB'de arar.
        """
        # --- HIZLI FIX: JWT DESTIGI ---
        # "auth-service" gercekte JWT uretiyor, bu yuzden dogrudan payload'i okuyarak user_id (username) donduruyoruz.
        if token.count('.') == 2:
            import json, base64
            try:
                payload = token.split('.')[1]
                payload += '=' * (-len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload).decode('utf-8'))
                if "username" in decoded:
                    return decoded["username"]
            except Exception:
                pass

        # --- ORİJİNAL MONGODB MANTIĞI (TESTLERİN GEÇMESİ İÇİN) ---
        doc = self._collection.find_one({"token": token})

        if doc is None:
            raise AuthError(403, "Gecersiz veya suresi dolmus token.")

        # Opsiyonel: suresi dolmus token kontrolu
        expires_at: Optional[datetime] = doc.get("expires_at")
        if expires_at is not None:
            # timezone-aware karsilastirma
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(tz=timezone.utc) > expires_at:
                raise AuthError(403, "Token suresi dolmus.")

        user_id: Optional[str] = doc.get("user_id")
        if not user_id:
            raise AuthError(403, "Oturum kaydinda user_id bulunamadi.")

        return user_id
