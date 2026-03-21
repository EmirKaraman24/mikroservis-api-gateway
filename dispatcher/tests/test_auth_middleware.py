# dispatcher/tests/test_auth_middleware.py
# ─────────────────────────────────────────
# TDD Refactor Fazi (Commit 07 - Emir): AuthMiddleware icin birim testler.
#
# MongoDB baglantisi gerektirmeden calisabilmesi icin MongoClient,
# MagicMock ile simule edilmistir (Dependency Injection sayesinde).
#
# Test Gruplari:
#   1. Basarili Kimlik Dogrulama (Happy Path)
#   2. Eksik / Yanlis Format Authorization Basligi
#   3. MongoDB'de Bulunmayan Token
#   4. Suresi Dolmus Token (expires_at kontrolu)
#   5. Kayit Icinde user_id Eksik
#   6. Buyuk/Kucuk Harf Duyarsizligi (header key)
#
# Calistirmak icin:
#   pytest dispatcher/tests/test_auth_middleware.py -v

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.auth_middleware import AuthMiddleware, AuthError


# ── Yardimci fabrika fonksiyonu ────────────────────────────────────────────

def _make_middleware(find_one_return=None):
    """
    Gercek bir MongoDB baglantisi olmadan AuthMiddleware olusturur.
    find_one_return: collection.find_one() cagrisinin dondurecegi deger.
    """
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = find_one_return
    # mongo_client[db_name][collection_name] zincirini simule et
    mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
    return AuthMiddleware(mongo_client=mock_client), mock_collection


# ── Grup 1: Basarili Kimlik Dogrulama ─────────────────────────────────────

class TestAuthenticateSuccess:
    """Gecerli token ile kimlik dogrulama basarili olmali."""

    def test_valid_token_returns_user_id(self):
        """Gecerli token icin dogru user_id dondurulmeli."""
        session_doc = {"token": "valid-token-abc", "user_id": "user-42"}
        auth, _ = _make_middleware(find_one_return=session_doc)

        result = auth.authenticate({"Authorization": "Bearer valid-token-abc"})
        assert result == "user-42"

    def test_valid_token_with_future_expiry_returns_user_id(self):
        """Suresi dolmamis token kabul edilmeli."""
        future = datetime.now(tz=timezone.utc) + timedelta(hours=24)
        session_doc = {
            "token": "token-with-expiry",
            "user_id": "user-99",
            "expires_at": future,
        }
        auth, _ = _make_middleware(find_one_return=session_doc)

        result = auth.authenticate({"Authorization": "Bearer token-with-expiry"})
        assert result == "user-99"

    def test_token_without_expiry_field_is_accepted(self):
        """expires_at alani olmayan token da gecerli sayilmali."""
        session_doc = {"token": "no-expiry-token", "user_id": "user-7"}
        auth, _ = _make_middleware(find_one_return=session_doc)

        result = auth.authenticate({"Authorization": "Bearer no-expiry-token"})
        assert result == "user-7"

    def test_collection_queried_with_correct_token(self):
        """MongoDB sorgusu dogru token degeriyle yapilmali."""
        session_doc = {"token": "query-token", "user_id": "user-1"}
        auth, mock_col = _make_middleware(find_one_return=session_doc)

        auth.authenticate({"Authorization": "Bearer query-token"})
        mock_col.find_one.assert_called_once_with({"token": "query-token"})


# ── Grup 2: Eksik / Yanlis Format Authorization Basligi ───────────────────

class TestMissingOrMalformedHeader:
    """Eksik veya yanlisformat Authorization basligi 401 firlatmali."""

    def test_missing_authorization_header_raises_401(self):
        """Authorization basligi hic yoksa 401 AuthError firlatilmali."""
        auth, _ = _make_middleware()

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({})
        assert exc_info.value.status_code == 401

    def test_empty_authorization_value_raises_401(self):
        """Authorization basligi bos string ise 401 firlatilmali."""
        auth, _ = _make_middleware()

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": ""})
        assert exc_info.value.status_code == 401

    def test_non_bearer_scheme_raises_401(self):
        """'Basic ...' gibi Bearer olmayan sema 401 firlatmali."""
        auth, _ = _make_middleware()

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Basic dXNlcjpwYXNz"})
        assert exc_info.value.status_code == 401

    def test_bearer_without_token_raises_401(self):
        """'Bearer ' sonrasinda token yoksa 401 firlatilmali."""
        auth, _ = _make_middleware()

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer "})
        assert exc_info.value.status_code == 401

    def test_bearer_only_keyword_raises_401(self):
        """Sadece 'Bearer' kelimesi varsa 401 firlatilmali."""
        auth, _ = _make_middleware()

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer"})
        assert exc_info.value.status_code == 401


# ── Grup 3: MongoDB'de Bulunmayan Token ────────────────────────────────────

class TestTokenNotFound:
    """MongoDB'de kaydedilmemis token icin 403 firlatilmali."""

    def test_unknown_token_raises_403(self):
        """find_one None donunce 403 AuthError beklenmeli."""
        auth, _ = _make_middleware(find_one_return=None)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer unknown-token"})
        assert exc_info.value.status_code == 403

    def test_mongodb_is_queried_even_for_unknown_token(self):
        """Bilinmeyen token icin de MongoDB sorgusu yapilmali."""
        auth, mock_col = _make_middleware(find_one_return=None)

        with pytest.raises(AuthError):
            auth.authenticate({"Authorization": "Bearer ghost-token"})
        mock_col.find_one.assert_called_once_with({"token": "ghost-token"})


# ── Grup 4: Suresi Dolmus Token ────────────────────────────────────────────

class TestExpiredToken:
    """Suresi dolmus token icin 403 firlatilmali."""

    def test_past_expiry_raises_403(self):
        """expires_at gecmiste olan token 403 AuthError firlatmali."""
        past = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        session_doc = {
            "token": "expired-token",
            "user_id": "user-dead",
            "expires_at": past,
        }
        auth, _ = _make_middleware(find_one_return=session_doc)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer expired-token"})
        assert exc_info.value.status_code == 403

    def test_naive_datetime_treated_as_utc(self):
        """timezone-naive expires_at UTC olarak yorumlanmali; gecmisteyse 403 vermeli."""
        # timezone bilgisi olmayan, gecmiste kalan tarih
        past_naive = datetime.now() - timedelta(hours=1)
        session_doc = {
            "token": "naive-expired",
            "user_id": "user-x",
            "expires_at": past_naive,
        }
        auth, _ = _make_middleware(find_one_return=session_doc)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer naive-expired"})
        assert exc_info.value.status_code == 403

    def test_future_naive_datetime_accepted(self):
        """timezone-naive, gelecekteki expires_at UTC olarak yorumlanmali; kabul edilmeli."""
        future_naive = datetime.now() + timedelta(hours=24)
        session_doc = {
            "token": "naive-valid",
            "user_id": "user-y",
            "expires_at": future_naive,
        }
        auth, _ = _make_middleware(find_one_return=session_doc)

        result = auth.authenticate({"Authorization": "Bearer naive-valid"})
        assert result == "user-y"


# ── Grup 5: Kayit Icinde user_id Eksik ────────────────────────────────────

class TestMissingUserId:
    """MongoDB kaydinda user_id alani eksik veya bos ise 403 firlatilmali."""

    def test_missing_user_id_field_raises_403(self):
        """Kayit user_id icermiyorsa 403 AuthError firlatilmali."""
        session_doc = {"token": "orphan-token"}  # user_id yok
        auth, _ = _make_middleware(find_one_return=session_doc)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer orphan-token"})
        assert exc_info.value.status_code == 403

    def test_empty_user_id_raises_403(self):
        """user_id bos string ise 403 AuthError firlatilmali."""
        session_doc = {"token": "empty-uid-token", "user_id": ""}
        auth, _ = _make_middleware(find_one_return=session_doc)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer empty-uid-token"})
        assert exc_info.value.status_code == 403

    def test_none_user_id_raises_403(self):
        """user_id None ise 403 AuthError firlatilmali."""
        session_doc = {"token": "none-uid-token", "user_id": None}
        auth, _ = _make_middleware(find_one_return=session_doc)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate({"Authorization": "Bearer none-uid-token"})
        assert exc_info.value.status_code == 403


# ── Grup 6: Header Buyuk/Kucuk Harf Duyarsizligi ─────────────────────────

class TestHeaderCaseInsensitivity:
    """Authorization basligi hem buyuk hem kucuk harfli gelmeli."""

    def test_lowercase_authorization_header_accepted(self):
        """'authorization' (kucuk harf) basligi da tanimlanmali."""
        session_doc = {"token": "case-token", "user_id": "user-lower"}
        auth, _ = _make_middleware(find_one_return=session_doc)

        result = auth.authenticate({"authorization": "Bearer case-token"})
        assert result == "user-lower"

    def test_uppercase_header_takes_precedence(self):
        """'Authorization' (buyuk harf) basligi tercih edilmeli."""
        session_doc = {"token": "upper-token", "user_id": "user-upper"}
        auth, _ = _make_middleware(find_one_return=session_doc)

        result = auth.authenticate({
            "Authorization": "Bearer upper-token",
            "authorization": "Bearer other-token",
        })
        assert result == "user-upper"
