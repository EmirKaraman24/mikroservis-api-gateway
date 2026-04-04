# SUNUM AKIŞ HARİTASI VE GÖSTERİM PLANI
# ═══════════════════════════════════════
# Tahmini Süre: 20-25 dakika

---

## AKIŞ HARİTASI (Sıralı Adımlar)

```
┌─────────────────────────────────────────┐
│  1. GİRİŞ (2 dk)                        │
│  "Proje nedir? Neden bu mimari?"        │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  2. MİMARİ TANITIM (3 dk)              │
│  Sistem diyagramını göster              │
│  Docker Compose yapısını anlat          │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  3. CANLI DEMO - Sistemi Ayağa Kaldır  │
│  (3 dk)                                 │
│  docker-compose up --build              │
│  GET /health → tüm servisler "ok"       │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  4. CANLI DEMO - Auth Akışı (3 dk)     │
│  POST /auth/register → 201             │
│  POST /auth/login → JWT token           │
│  GET /users (token yok) → 401           │
│  GET /users (token var) → 200           │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  5. CANLI DEMO - CRUD (3 dk)           │
│  POST /messages → mesaj gönder          │
│  GET /messages → mesajları listele      │
│  DELETE /messages/:id → sil             │
│  GET /users/:id → kullanıcı getir      │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  6. KOD YAPISI - OOP & TDD (3 dk)      │
│  Dispatcher, Router, AuthMiddleware     │
│  sınıflarını göster                     │
│  Test dosyalarını ve TDD döngüsünü     │
│  commit geçmişinden göster              │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  7. İZLEME - Grafana & Prometheus       │
│  (2 dk)                                 │
│  localhost:3000 → Grafana dashboard     │
│  localhost:9090 → Prometheus metrikleri │
│  /metrics endpoint'ini göster           │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  8. TESTLER (2 dk)                      │
│  pytest çıktısını göster                │
│  ~112 test, E2E test sonuçları          │
│  k6 yük testi senaryolarını anlat       │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  9. SORULAR & KAPANIŞ (2 dk)           │
└─────────────────────────────────────────┘
```

---

## DETAYLI GÖSTERİM PLANI

### ADIM 1: GİRİŞ (2 dakika)
**Söyle:**
> "Bu projede bir Dispatcher (API Gateway) tabanlı mikroservis sistemi geliştirdik.
> Monolitik yapı yerine 4 bağımsız servis kullandık: Auth, User, Message ve Dispatcher.
> Tüm dış istekler yalnızca Dispatcher üzerinden geçer."

**Göster:** README.md'deki Mermaid mimari diyagramını (ekrana yansıt)

---

### ADIM 2: MİMARİ TANITIM (3 dakika)
**Söyle:**
> "Sistemde 10 Docker container çalışıyor. Her servisin kendi izole MongoDB'si var.
> Network isolation sayesinde sadece Dispatcher dışarıya port açıyor.
> İç servisler (auth, user, message) dışarıdan erişilemez."

**Göster:**
- `docker-compose.yml` dosyasını aç → `internal: true` ağını göster
- `networks` ve `expose` vs `ports` farkını işaret et
- `docs/architecture.md` diyagramını göster

---

### ADIM 3: CANLI DEMO — Sistemi Ayağa Kaldır (3 dakika)
> ÖNEMLİ: Sunumdan ÖNCE sistemi ayağa kaldır ki bekleme olmasın!
> `docker-compose up --build` komutunu sunum öncesi çalıştır.

**Terminalde yap:**
```powershell
# Sağlık kontrolü
curl http://localhost:8080/health
```

**Göster:** JSON yanıtında tüm servislerin "ok" olduğunu
```json
{"status": "ok", "services": {"auth-service": "ok", "user-service": "ok", "message-service": "ok"}}
```

**Söyle:**
> "Health check endpoint'i tüm bağımlı servisleri ping'ler.
> Herhangi biri çökerse status 'degraded' olur ve 503 döner."

---

### ADIM 4: CANLI DEMO — Auth Akışı (3 dakika)
**Terminalde sırayla yap:**

```powershell
# 1. Kullanıcı kaydı
curl -X POST http://localhost:8080/auth/register -H "Content-Type: application/json" -d "{\"username\": \"demo\", \"email\": \"demo@test.com\", \"password\": \"pass123\"}"
# → 201 Created

# 2. Giriş yap
curl -X POST http://localhost:8080/auth/login -H "Content-Type: application/json" -d "{\"username\": \"demo\", \"password\": \"pass123\"}"
# → 200 + JWT token

# 3. Token OLMADAN korumalı endpoint
curl http://localhost:8080/users
# → 401 Unauthorized (Auth middleware çalışıyor!)

# 4. Token İLE korumalı endpoint
curl http://localhost:8080/users -H "Authorization: Bearer <BURAYA_TOKEN_YAPISTIR>"
# → 200 OK
```

**Söyle:**
> "/auth/* rotaları authentication kontrolünden muaftır çünkü henüz kullanıcının token'ı yok.
> Diğer tüm rotalar (/users, /messages) Bearer token gerektirir.
> Token yoksa 401, geçersiz token ise 403 döner."

---

### ADIM 5: CANLI DEMO — CRUD İşlemleri (3 dakika)
**Terminalde yap:**

```powershell
# Mesaj gönder
curl -X POST http://localhost:8080/messages -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" -d "{\"content\": \"Merhaba Hocam\", \"sender\": \"demo\"}"
# → 201 Created

# Mesajları listele
curl http://localhost:8080/messages -H "Authorization: Bearer <TOKEN>"
# → 200 + mesaj listesi

# Mesaj sil
curl -X DELETE http://localhost:8080/messages/1 -H "Authorization: Bearer <TOKEN>"
# → 200 Deleted
```

**Söyle:**
> "Richardson Maturity Model Seviye 2: Kaynak bazlı URI'lar (/users, /messages) +
> doğru HTTP metotları (GET=oku, POST=oluştur, PUT=güncelle, DELETE=sil) +
> anlamlı durum kodları (200, 201, 401, 404, 500)."

---

### ADIM 6: KOD YAPISI — OOP & TDD (3 dakika)
**IDE'de göster:**

1. **`dispatcher/src/dispatcher.py`** → `Dispatcher` sınıfı, `forward()` metodu
   > "Dispatcher sınıfı Router'dan bağımsız. Router dışarıdan enjekte ediliyor (Dependency Injection).
   > Bu sayede test sırasında sahte (mock) Router kullanabiliyoruz."

2. **`dispatcher/src/router.py`** → `Router` sınıfı, `resolve()` metodu
   > "Router prefix eşleme yapıyor. /users ile başlayan istekler User Service'e,
   > /auth ile başlayanlar Auth Service'e yönlendiriliyor."

3. **`dispatcher/src/rate_limiter.py`** → Sliding Window
   > "Rate limiter thread-safe, sliding window algoritması kullanıyor.
   > Her IP için son 60 saniyedeki istekler bir deque'de tutulur."

4. **Git log göster:**
```powershell
git log --oneline -15
```
   > "Commit geçmişinde Red→Green→Refactor döngüsü görülüyor.
   > Önce test yazılmış, sonra implementasyon yapılmış."

---

### ADIM 7: İZLEME — Grafana & Prometheus (2 dakika)
**Tarayıcıda göster:**

1. **http://localhost:9090** → Prometheus
   - Targets sayfasında Dispatcher'ın scrape edildiğini göster

2. **http://localhost:3000** → Grafana (admin/admin)
   - Dashboard'u aç, metrik grafiklerini göster

3. **http://localhost:8080/metrics** → Ham Prometheus metrikleri
   > "Prometheus her 15 saniyede /metrics endpoint'ini çekiyor.
   > Grafana bu verileri görselleştiriyor."

---

### ADIM 8: TESTLER (2 dakika)
**Göster:**

1. **Test sayısı:** ~112 birim test + 7 E2E senaryo
2. **Test dosyalarını listele:**
   - `dispatcher/tests/test_dispatcher.py` (18 test)
   - `dispatcher/tests/test_router.py` (12 test)
   - `dispatcher/tests/test_auth_middleware.py` (14 test)
   - `dispatcher/tests/test_edge_cases.py` (32 test)
   - `tests/e2e/test_full_lifecycle.py` (15+ test)

3. **k6 yük testi senaryolarını anlat:**
   > "k6 ile smoke (5 VU), load (50-200 VU), stress (500 VU), spike senaryoları yazıldı.
   > Hedef: p95 yanıt süresi 500ms altında, hata oranı %1'in altında."

---

### ADIM 9: KAPANIŞ
**Söyle:**
> "Özet olarak: Mikroservis mimarisi, OOP ve TDD ile geliştirdik.
> Docker ile tam izole konteyner ortamı, MongoDB ile NoSQL entegrasyonu,
> Prometheus+Grafana ile izleme, k6 ile yük testi yaptık.
> Rate limiting, health check ve trafik dashboard bonus özellik olarak eklendi."

---

## SUNUM ÖNCESİ HAZIRLIK KONTROL LİSTESİ

- [ ] Docker Desktop çalışıyor mu?
- [ ] `docker-compose up --build` sunumdan 10 dk önce çalıştır
- [ ] `curl http://localhost:8080/health` → "ok" döndüğünü doğrula
- [ ] Postman veya terminal hazır mı? (curl komutları için)
- [ ] Tarayıcıda Grafana (localhost:3000) ve Prometheus (localhost:9090) açık mı?
- [ ] IDE'de dispatcher/src/ dosyaları açık mı?
- [ ] Bu dosyayı (SUNUM_PLANI.md) telefonuna at, göz ucuyla bakabilirsin

---

## HOCADAN GELEBİLECEK OLASI SORULAR VE CEVAPLARI

### S: "Neden mikroservis kullandınız, monolitik yapmadiniz?"
> Monolitik yapıda tek bir hata tüm sistemi çökertir. Mikroserviste her servis bağımsız deploy edilir,
> bağımsız ölçeklenir. Örneğin mesajlaşma yoğunsa sadece message-service'i scale edebiliriz.

### S: "TDD sürecini nasıl izlediniz?"
> Git commit geçmişinden gösterilebilir. Önce test yazdık (red), sonra minimum kodla geçirdik (green),
> sonra refactor yaptık. Her commit mesajında bu döngü belirtilmiş.

### S: "Network isolation nasıl çalışıyor?"
> docker-compose.yml'de `internal: true` ağı var. Bu ağdaki containerlar dış internete erişemez.
> Sadece Dispatcher hem public hem internal ağda, diğer servisler sadece internal ağda.

### S: "Rate limiting neden sliding window?"
> Fixed window'da pencere sınırında burst olabilir (59. saniyede 100 + 61. saniyede 100 = 2 saniyede 200 istek).
> Sliding window bunu önler çünkü son 60 saniyelik pencere sürekli kayar.

### S: "JWT nasıl doğrulanıyor?"
> Auth service login'de PyJWT ile token üretir. Dispatcher'daki AuthMiddleware JWT'nin payload kısmını decode eder
> ve username'i çıkarır. Token 3 parçadan oluşur: header.payload.signature (Base64 encoded).

### S: "Prometheus ne işe yarıyor?"
> Prometheus her 15 saniyede Dispatcher'ın /metrics endpoint'ini çeker (pull modeli).
> İstek sayısı, yanıt süresi gibi metrikleri toplar. Grafana bu verileri görsel panolarda gösterir.

### S: "Richardson Maturity Model nedir?"
> REST API olgunluk seviyesidir. Seviye 0: tek URL. Seviye 1: kaynak bazlı URI (/users).
> Seviye 2: HTTP metotları + durum kodları. Seviye 3: HATEOAS. Biz Seviye 2'deyiz.
