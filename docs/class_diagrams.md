# Sınıf Diyagramları — Tüm Mikroservisler

**Commit 30 — 1 Nisan 2026 | Nuh**  
`docs: add class diagrams for all microservices (Mermaid)`

---

## 1. Dispatcher (API Gateway) — Tam Sınıf Diyagramı

```mermaid
classDiagram
    class Dispatcher {
        -_router: Router
        -_timeout: float
        +ALLOWED_METHODS: frozenset
        +__init__(router, timeout)
        +forward(method, path, headers, body, params) Response
        -_validate_method(method) void
        -_build_url(base, path) str
    }

    class Router {
        -_routes: dict
        +SERVICE_MAP: dict
        +__init__(routes)
        +resolve(path) str|None
        +add_route(prefix, url) void
    }

    class AuthMiddleware {
        -_collection: MongoCollection
        -_BEARER_PREFIX: str
        +__init__(mongo_client, db_name, collection_name)
        +authenticate(headers) str
        -_lookup_token(token) str
    }

    class DispatcherError {
        <<exception>>
    }

    class RouteNotFoundError {
        <<exception>>
    }

    class UpstreamError {
        <<exception>>
        +status_code: int
        +__init__(status_code, message)
    }

    class AuthError {
        <<exception>>
        +status_code: int
        +__init__(status_code, message)
    }

    Dispatcher --> Router : uses
    Dispatcher --> AuthMiddleware : uses
    Dispatcher ..> DispatcherError : raises
    DispatcherError <|-- RouteNotFoundError
    DispatcherError <|-- UpstreamError
    AuthMiddleware ..> AuthError : raises
```

---

## 2. Auth Service — Sınıf Diyagramı

```mermaid
classDiagram
    class AuthService {
        <<Flask App>>
        +app: Flask
        +auth_logic: AuthLogic
        +POST /auth/login()
        +POST /auth/register()
        +GET  /health()
    }

    class AuthLogic {
        -_collection: MongoCollection
        +__init__(mongo_client, db_name)
        +login(username, password) dict
        +register(username, password) dict
        -_hash_password(password) str
        -_verify_password(password, hash) bool
        -_generate_token() str
    }

    class UserCredential {
        <<document>>
        +_id: ObjectId
        +username: str
        +password_hash: str
        +created_at: datetime
    }

    class Session {
        <<document>>
        +_id: ObjectId
        +token: str
        +user_id: str
        +expires_at: datetime
    }

    AuthService --> AuthLogic : delegates
    AuthLogic ..> UserCredential : creates/reads
    AuthLogic ..> Session : creates
```

---

## 3. User Service — Sınıf Diyagramı

```mermaid
classDiagram
    class UserService {
        <<Flask App>>
        +app: Flask
        +repo: UserRepository
        +GET  /users()
        +GET  /users/{id}()
        +POST /users()
        +PUT  /users/{id}()
        +DELETE /users/{id}()
        +GET  /health()
    }

    class UserRepository {
        -_collection: MongoCollection
        +__init__(mongo_client, db_name)
        +find_all() list
        +find_by_id(user_id) dict|None
        +create(data) str
        +update(user_id, data) bool
        +delete(user_id) bool
    }

    class UserDocument {
        <<document>>
        +_id: ObjectId
        +name: str
        +email: str
        +created_at: datetime
        +updated_at: datetime
    }

    UserService --> UserRepository : uses
    UserRepository ..> UserDocument : manages
```

---

## 4. Message Service — Sınıf Diyagramı

```mermaid
classDiagram
    class MessageService {
        <<Flask App>>
        +app: Flask
        +messages_db: dict
        +message_counter: int
        +GET  /messages()
        +POST /messages()
        +DELETE /messages/{id}()
        +GET  /health()
    }

    class MessageDocument {
        <<document>>
        +_id: str
        +sender: str
        +content: str
        +ts: int
    }

    MessageService ..> MessageDocument : manages
```

---

## 5. Tüm Sistem — Bileşen İlişkileri

```mermaid
classDiagram
    class Client {
        <<external>>
    }

    class Dispatcher {
        +forward(method, path, ...)
    }

    class AuthService {
        +POST /auth/login
        +POST /auth/register
    }

    class UserService {
        +GET  /users
        +POST /users
        +PUT  /users/{id}
        +DELETE /users/{id}
    }

    class MessageService {
        +GET  /messages
        +POST /messages
        +DELETE /messages/{id}
    }

    class MongoDB_Dispatcher {
        <<database>>
        +sessions: Collection
    }

    class MongoDB_Auth {
        <<database>>
        +credentials: Collection
        +sessions: Collection
    }

    class MongoDB_Users {
        <<database>>
        +users: Collection
    }

    class MongoDB_Messages {
        <<database>>
        +messages: Collection
    }

    class Prometheus {
        <<monitoring>>
        +scrape /metrics
    }

    class Grafana {
        <<visualization>>
        +dashboard: TrafficDashboard
    }

    Client --> Dispatcher : HTTP :8080
    Dispatcher --> MongoDB_Dispatcher : token lookup
    Dispatcher --> AuthService : /auth/*
    Dispatcher --> UserService : /users/*
    Dispatcher --> MessageService : /messages/*
    AuthService --> MongoDB_Auth : read/write
    UserService --> MongoDB_Users : CRUD
    MessageService --> MongoDB_Messages : CRUD
    Prometheus --> Dispatcher : scrape :8080/metrics
    Grafana --> Prometheus : query
```

---

## 6. RateLimiter — Sınıf Diyagramı (Commit 32 ile eklenecek)

```mermaid
classDiagram
    class RateLimiter {
        -_window: dict
        -_limit: int
        -_period: float
        +__init__(limit, period)
        +check(ip) bool
        +is_allowed(ip) bool
        -_cleanup_old_entries() void
    }

    class RateLimitExceeded {
        <<exception>>
        +status_code: int
        +retry_after: int
        +__init__(retry_after)
    }

    RateLimiter ..> RateLimitExceeded : raises
    Dispatcher --> RateLimiter : uses
```

---

## 7. Docker Bileşen Mimarisi

```mermaid
classDiagram
    class DockerCompose {
        <<infrastructure>>
        +version: "3.9"
        +networks: internal, external
        +volumes: mongo-data-*
    }

    class DispatcherContainer {
        <<container>>
        +image: dispatcher:latest
        +ports: "8080:5000"
        +network: external + internal
    }

    class AuthServiceContainer {
        <<container>>
        +image: auth-service:latest
        +ports: internal only
        +network: internal
    }

    class UserServiceContainer {
        <<container>>
        +image: user-service:latest
        +ports: internal only
        +network: internal
    }

    class MessageServiceContainer {
        <<container>>
        +image: message-service:latest
        +ports: internal only
        +network: internal
    }

    class MongoDBContainer {
        <<container>>
        +image: mongo:6
        +volumes: mongo-data
        +network: internal
    }

    class PrometheusContainer {
        <<container>>
        +image: prom/prometheus:latest
        +network: internal
    }

    class GrafanaContainer {
        <<container>>
        +image: grafana/grafana:latest
        +ports: "3000:3000"
        +network: internal
    }

    DockerCompose --> DispatcherContainer
    DockerCompose --> AuthServiceContainer
    DockerCompose --> UserServiceContainer
    DockerCompose --> MessageServiceContainer
    DockerCompose --> MongoDBContainer
    DockerCompose --> PrometheusContainer
    DockerCompose --> GrafanaContainer
    DispatcherContainer --> AuthServiceContainer : internal net
    DispatcherContainer --> UserServiceContainer : internal net
    DispatcherContainer --> MessageServiceContainer : internal net
    PrometheusContainer --> DispatcherContainer : scrape
    GrafanaContainer --> PrometheusContainer : query
```
