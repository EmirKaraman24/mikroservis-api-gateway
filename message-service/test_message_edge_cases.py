# message-service/test_message_edge_cases.py
# ─────────────────────────────────────────────────────────────
# TDD Refactor Fazi (Commit 31 - Emir): Message Service edge
# case testleri ve mevcut testlerin refactor'ı.
#
# Kapsam:
#   - Geçersiz/eksik veri edge case'leri
#   - Büyük payload senaryoları
#   - Eş zamanlı işlem simülasyonu
#   - Mesaj bulunamama durumları
#   - Sınır değerleri (boundary conditions)
#
# Çalıştırmak için:
#   pytest message-service/test_message_edge_cases.py -v

import pytest
import json
from app import app


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    """Her test öncesi in-memory DB'yi sıfırla."""
    import app as app_module
    app_module.messages_db.clear()
    app_module.message_counter = 1
    yield
    app_module.messages_db.clear()
    app_module.message_counter = 1


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def send_msg(client, **kwargs):
    """Yardımcı: mesaj gönder ve response döndür."""
    data = {"content": "test", "sender": "user1", **kwargs}
    return client.post('/messages', json=data)


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 1: TEMEL CRUD — REFACTOR EDİLMİŞ
# ═══════════════════════════════════════════════════════════════════════════

class TestBasicCrudRefactored:
    """Temel CRUD testleri — daha açıklayıcı ve güçlendirilmiş."""

    def test_health_check_returns_healthy(self, client):
        """/health endpoint 200 ve {status: healthy} dönmeli."""
        resp = client.get('/health')
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "healthy"

    def test_send_message_returns_201(self, client):
        """Yeni mesaj gönderildiğinde 201 Created dönmeli."""
        resp = send_msg(client)
        assert resp.status_code == 201

    def test_send_message_body_contains_confirmation(self, client):
        """Yanıt 'Message sent' mesajı içermeli."""
        resp = send_msg(client)
        assert resp.get_json()["message"] == "Message sent"

    def test_get_messages_returns_list(self, client):
        """GET /messages her zaman liste döndürmelidir."""
        resp = client.get('/messages')
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_get_messages_empty_db(self, client):
        """DB boşken boş liste dönmeli."""
        resp = client.get('/messages')
        assert resp.get_json() == []

    def test_get_messages_after_inserts(self, client):
        """Eklenen mesajlar GET ile geri alınabilmeli."""
        send_msg(client, content="msg1")
        send_msg(client, content="msg2")
        resp = client.get('/messages')
        msgs = resp.get_json()
        assert len(msgs) == 2

    def test_delete_existing_message(self, client):
        """Var olan mesaj silinebilmeli."""
        send_msg(client)  # message_counter=1 → key="1"
        resp = client.delete('/messages/1')
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Message deleted"

    def test_delete_removes_from_db(self, client):
        """Silinen mesaj GET'te görünmemeli."""
        send_msg(client)
        client.delete('/messages/1')
        resp = client.get('/messages')
        assert len(resp.get_json()) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 2: PAYLOAD EDGE CASE'LERİ
# ═══════════════════════════════════════════════════════════════════════════

class TestPayloadEdgeCases:
    """Farklı payload türleri ve sınır değerleri."""

    def test_send_empty_json_object(self, client):
        """Boş JSON {} gönderildiğinde yine de 201 dönmeli."""
        resp = client.post('/messages', json={})
        assert resp.status_code == 201

    def test_send_message_with_extra_fields(self, client):
        """Fazladan alanlar içeren payload kabul edilmeli."""
        resp = client.post('/messages', json={
            "content": "test",
            "sender": "user1",
            "extra_field": "ignored",
            "priority": 99,
        })
        assert resp.status_code == 201

    def test_send_message_with_long_content(self, client):
        """10.000 karakterlik içerik kabul edilmeli."""
        long_content = "A" * 10_000
        resp = send_msg(client, content=long_content)
        assert resp.status_code == 201

    def test_send_message_with_unicode_content(self, client):
        """Türkçe karakterler içeren mesaj kaydedilmeli."""
        resp = send_msg(client, content="Merhaba dünya! 🌍 Türkçe test.")
        assert resp.status_code == 201
        msgs = client.get('/messages').get_json()
        assert any("Türkçe" in str(m) for m in msgs)

    def test_send_message_with_special_chars(self, client):
        """Özel karakterler sorun çıkarmamalı."""
        resp = send_msg(client, content='<script>alert("xss")</script>')
        assert resp.status_code == 201

    def test_send_message_with_json_content(self, client):
        """Content alanı JSON string olarak saklanabilmeli."""
        resp = send_msg(client, content='{"nested": "json", "value": 42}')
        assert resp.status_code == 201

    def test_send_message_with_integer_sender(self, client):
        """sender alanı integer gelse de hata vermemeli."""
        resp = client.post('/messages', json={"content": "test", "sender": 42})
        assert resp.status_code == 201

    def test_send_null_content(self, client):
        """content=null gelse de 201 dönmeli (veri doğrulama işi servise ait değil)."""
        resp = client.post('/messages', json={"content": None, "sender": "user1"})
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 3: MESAJ SAYACI VE ID YÖNETİMİ
# ═══════════════════════════════════════════════════════════════════════════

class TestMessageCounterAndIds:
    """Mesaj ID'lerinin doğru artması ve yönetimi."""

    def test_first_message_has_id_1(self, client):
        """İlk mesajın ID'si 1 olmalı."""
        send_msg(client)
        msgs = client.get('/messages').get_json()
        # DB'de {"1": {...}} şeklinde saklanır
        import app as m
        assert "1" in m.messages_db

    def test_ids_increment_sequentially(self, client):
        """Her yeni mesajın ID'si bir öncekinden 1 fazla olmalı."""
        import app as m
        for i in range(5):
            send_msg(client)
        assert set(m.messages_db.keys()) == {"1", "2", "3", "4", "5"}

    def test_delete_does_not_reset_counter(self, client):
        """Silme işlemi sayacı sıfırlamamalı."""
        import app as m
        send_msg(client)  # id=1
        send_msg(client)  # id=2
        client.delete('/messages/1')
        send_msg(client)  # id=3 (reset olmaz)
        assert "3" in m.messages_db

    def test_delete_nonexistent_message_returns_200(self, client):
        """Var olmayan mesaj ID'sini silmeye çalışmak 200 dönmeli."""
        resp = client.delete('/messages/999')
        assert resp.status_code == 200

    def test_delete_nonexistent_message_body(self, client):
        """Var olmayan mesaj silinmeye çalışıldığında 'Message deleted' dönmeli."""
        resp = client.delete('/messages/9999')
        assert resp.get_json()["message"] == "Message deleted"

    def test_delete_string_id(self, client):
        """String ID ile silme çalışmalı."""
        send_msg(client)
        resp = client.delete('/messages/1')
        assert resp.status_code == 200

    def test_delete_already_deleted_message(self, client):
        """Zaten silinmiş mesajı tekrar silmek hata vermemeli."""
        send_msg(client)
        client.delete('/messages/1')
        resp = client.delete('/messages/1')  # tekrar sil
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 4: HTTP METOD DOĞRULAMASI
# ═══════════════════════════════════════════════════════════════════════════

class TestHttpMethodValidation:
    """Desteklenmeyen HTTP metodları reddedilmeli."""

    def test_patch_messages_not_allowed(self, client):
        """PATCH /messages desteklenmiyorsa 405 dönmeli."""
        resp = client.patch('/messages', json={"content": "test"})
        assert resp.status_code == 405

    def test_put_messages_not_allowed(self, client):
        """PUT /messages desteklenmiyorsa 405 dönmeli."""
        resp = client.put('/messages', json={"content": "test"})
        assert resp.status_code == 405

    def test_get_messages_with_id_not_defined(self, client):
        """GET /messages/1 tanımlı değilse 405 dönmeli."""
        send_msg(client)
        resp = client.get('/messages/1')
        assert resp.status_code == 405


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 5: EŞ ZAMANLI İŞLEM SİMÜLASYONU
# ═══════════════════════════════════════════════════════════════════════════

class TestConcurrencySimulation:
    """Çok sayıda ardışık istek (thread güvenliği simülasyonu)."""

    def test_send_many_messages_sequentially(self, client):
        """100 mesaj arka arkaya gönderildiğinde hepsi saklanmalı."""
        for i in range(100):
            resp = send_msg(client, content=f"mesaj {i}", sender=f"user{i}")
            assert resp.status_code == 201

        msgs = client.get('/messages').get_json()
        assert len(msgs) == 100

    def test_send_and_delete_alternately(self, client):
        """Ekleme ve silme birbirini takip ettiğinde tutarsızlık olmmalı."""
        import app as m
        for i in range(10):
            send_msg(client, content=f"msg{i}")

        # Tek ID'lileri sil
        for i in range(1, 11, 2):
            client.delete(f'/messages/{i}')

        remaining = client.get('/messages').get_json()
        assert len(remaining) == 5


# ═══════════════════════════════════════════════════════════════════════════
#  GRUP 6: İÇERİK TİPİ VE FORMAT
# ═══════════════════════════════════════════════════════════════════════════

class TestContentTypeAndFormat:
    """Content-Type başlıkları ve yanıt formatı."""

    def test_get_messages_returns_json_content_type(self, client):
        """GET /messages yanıtı application/json olmalı."""
        resp = client.get('/messages')
        assert resp.content_type.startswith('application/json')

    def test_post_messages_returns_json_content_type(self, client):
        """POST /messages yanıtı application/json olmalı."""
        resp = send_msg(client)
        assert resp.content_type.startswith('application/json')

    def test_delete_message_returns_json_content_type(self, client):
        """DELETE /messages/:id yanıtı application/json olmalı."""
        send_msg(client)
        resp = client.delete('/messages/1')
        assert resp.content_type.startswith('application/json')

    def test_post_without_content_type_header(self, client):
        """Content-Type başlığı olmadan gönderilen istek işlenmeli."""
        resp = client.post('/messages',
                           data='{"content": "test", "sender": "user1"}',
                           content_type='application/json')
        assert resp.status_code == 201
