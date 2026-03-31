# Sıralama Diyagramları — Dispatcher Routing Flow

**Commit 29 — 1 Nisan 2026 | Emir**  
`docs: add sequence diagrams for dispatcher routing flow (Mermaid)`

---

## 1. Başarılı İstek — Tam Akış

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant AM as AuthMiddleware
    participant MG as MongoDB\n(sessions)
    participant R  as Router
    participant US as UserService\n(:5002)

    Client->>+D: GET /users/42\nAuthorization: Bearer <token>

    Note over D: 1. Auth Middleware devreye giriyor

    D->>+AM: authenticate(headers)
    AM->>+MG: find_one({token: "<token>"})
    MG-->>-AM: {user_id: "usr-7", expires_at: ...}
    AM-->>-D: user_id = "usr-7"

    Note over D: 2. Router path çözümlüyor

    D->>+R: resolve("/users/42")
    R-->>-D: "http://user-service:5002"

    Note over D: 3. Upstream'e yönlendirme

    D->>+US: GET http://user-service:5002/users/42\nHeaders: {Authorization: Bearer <token>}
    US-->>-D: 200 OK\n{id: 42, name: "Emir", email: "..."}

    D-->>-Client: 200 OK\n{id: 42, name: "Emir", email: "..."}
```

---

## 2. Kimlik Doğrulama Hatası (401 — Token Eksik)

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant AM as AuthMiddleware

    Client->>+D: GET /users/42\n(Authorization header yok)

    D->>+AM: authenticate(headers)
    AM-->>-D: ❌ AuthError(401, "Authorization başlığı eksik")

    D-->>-Client: 401 Unauthorized\n"Authorization başlığı eksik"
```

---

## 3. Geçersiz Token (403 — Token Bulunamadı)

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant AM as AuthMiddleware
    participant MG as MongoDB\n(sessions)

    Client->>+D: GET /users/42\nAuthorization: Bearer invalid-token

    D->>+AM: authenticate(headers)
    AM->>+MG: find_one({token: "invalid-token"})
    MG-->>-AM: null (bulunamadı)
    AM-->>-D: ❌ AuthError(403, "Geçersiz veya süresi dolmuş token")

    D-->>-Client: 403 Forbidden\n"Geçersiz veya süresi dolmuş token"
```

---

## 4. Bilinmeyen Route (404 — Rota Yok)

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant AM as AuthMiddleware
    participant R  as Router

    Client->>+D: GET /admin/panel\nAuthorization: Bearer valid-token

    D->>+AM: authenticate(headers)
    AM-->>-D: user_id = "usr-7"

    D->>+R: resolve("/admin/panel")
    R-->>-D: None (eşleşen rota yok)

    D-->>-Client: 404 Not Found\n"'/admin/panel' için eşleşen rota bulunamadı"
```

---

## 5. Upstream Servis Hatası (503 — Bağlantı Reddedildi)

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant AM as AuthMiddleware
    participant US as UserService\n(:5002)

    Client->>+D: POST /users\nAuthorization: Bearer valid-token\n{name: "Yeni Kullanıcı"}

    D->>+AM: authenticate(headers)
    AM-->>-D: user_id = "usr-7"

    D->>+US: POST http://user-service:5002/users
    US--x D: ❌ ConnectionError (servis kapalı)

    Note over D: requests.ConnectionError yakalandı\nUpstreamError(503) fırlatılıyor

    D-->>-Client: 503 Service Unavailable\n"Upstream bağlantı hatası"
```

---

## 6. Zaman Aşımı (504 — Gateway Timeout)

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant MS as MessageService\n(:5003)

    Client->>+D: POST /messages\nAuthorization: Bearer valid-token

    D->>+MS: POST http://message-service:5003/messages
    Note over MS: Servis 10+ saniye yanıt vermiyor...
    MS--xD: ⏱ Timeout (10s aşıldı)

    Note over D: requests.Timeout yakalandı\nUpstreamError(504) fırlatılıyor

    D-->>-Client: 504 Gateway Timeout\n"Upstream zaman aşımı"
```

---

## 7. Kullanıcı Kaydı Akışı (Auth Service)

```mermaid
sequenceDiagram
    autonumber
    actor Client as İstemci
    participant D  as Dispatcher\n(:8080)
    participant AS as AuthService\n(:5001)
    participant MG as MongoDB\n(users)

    Note over Client,D: /auth/* rotaları AuthMiddleware'i atlar

    Client->>+D: POST /auth/register\n{username: "emir", password: "..."}

    Note over D: /auth ile başladığı için\nAuthMiddleware devreye girmez

    D->>+AS: POST http://auth-service:5001/auth/register\n{username: "emir", password: "..."}
    AS->>+MG: insert_one({username: "emir", hash: "..."})
    MG-->>-AS: inserted_id: "abc123"
    AS-->>-D: 201 Created\n{message: "Kayıt başarılı", user_id: "abc123"}

    D-->>-Client: 201 Created\n{message: "Kayıt başarılı", user_id: "abc123"}
```

---

## 8. Prometheus Metrics Akışı

```mermaid
sequenceDiagram
    autonumber
    participant Prometheus
    participant D as Dispatcher\n(:8080/metrics)

    loop Her 15 saniyede
        Prometheus->>+D: GET /metrics
        D-->>-Prometheus: 200 OK\n# HELP http_requests_total...\nhttp_requests_total{method="GET"} 142\nhttp_request_duration_seconds{...} 0.045\n...
    end
```
