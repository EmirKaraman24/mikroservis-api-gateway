# 📡 Dispatcher — Mikroservis API Gateway Projesi

![Dispatcher Banner](https://img.shields.io/badge/Dispatcher-API--Gateway-blue?style=for-the-badge&logo=python) 
![Status](https://img.shields.io/badge/Status-Delivery--Ready-success?style=for-the-badge)

**Modern, Güvenli ve Yüksek Performanslı Mikroservis Yönetimi.**

Bu proje, bir **API Gateway (Dispatcher)** merkezli mikroservis mimarisinin (Auth, User, Message) nasıl kurgulanacağını, Richardson Maturity Model (Seviye 2) standartlarına uygunluğunu ve Docker ekosistemiyle nasıl izole edileceğini sergiler.

---

## 🏛 Sistem Mimarisi

Sistem, dış dünyaya kapalı olan mikroservislerin sadece **Dispatcher (Gateway)** üzerinden birleştirilmesi (Aggregation) prensibiyle çalışır.

```mermaid
graph TD
    Client[Dünya / İstemci] -- Port 8080 --> Dispatcher
    
    subgraph "İzole Mikroservis Ağı (Internal)"
        Dispatcher -- Auth Header Check --> AuthService[Auth Service :5002]
        Dispatcher -- Routing --> UserService[User Service :5001]
        Dispatcher -- Routing --> MsgService[Message Service :5003]
        
        AuthService --- DB_Auth[(MongoDB Auth)]
        UserService --- DB_User[(MongoDB User)]
        MsgService --- DB_Msg[(MongoDB Msg)]
    end
    
    subgraph "Gözlemlenebilirlik (Observability)"
        Prometheus[Prometheus Metrics] --- Dispatcher
        Grafana[Grafana Dashboard] --- Prometheus
    end
```

---

## 🚀 Öne Çıkan Özellikler

- **🔐 JWT Güvenlik Katmanı**: Yetkisiz tüm istekler Dispatcher seviyesinde 401 Unauthorized ile engellenir.
- **⚡ Dinamik Rate Limiting**: Burst saldırılara karşı IP bazlı saniyelik sınırlama (429 Too Many Requests).
- **📡 Mikroservis İzolasyonu**: Servisler sadece iç ağda çalışır, doğrudan dışarıdan ulaşılamaz.
- **📊 Canlı İzleme (Observability)**: Prometheus ve Grafana entegrasyonu ile tam kontrol.
- **🧪 TDD Odaklı Geliştirme**: 100+ birim ve uçtan uca (E2E) test ile %100 güvenilirlik.

---

## 🖼 Doğrulama Galerisi (Ekran Görüntüleri)

Projenin tüm fonksiyonlarının çalıştığına dair 8 ana adımın kanıtları aşağıdadır:

### 1-4. Sistem Başlatma ve Güvenlik Testleri
| 1. Docker Logları | 2. Health Check | 3. JWT Token / Auth | 4. 401 Güvenlik Engeli |
|:---:|:---:|:---:|:---:|
| ![Step 1](docs/images/1.png) | ![Step 2](docs/images/2.png) | ![Step 3](docs/images/3.png) | ![Step 4](docs/images/4.png) |
| *Sistemin hatasız ayağa kalkış kanıtı.* | *Tüm servislerin sağlıklı (OK) durumu.* | *Auth servisinden alınan JWT.* | *Yetkisiz girişin engellenmesi.* |

### 5-6. Dashboard ve İzleme Panelleri
| 5. Trafik Dashboard | 6. Grafana Metrikleri |
|:---:|:---:|
| ![Step 5](docs/images/5.png) | ![Step 6](docs/images/6.png) |
| *Geliştirilmiş özel takip ekranı.* | *Sistemin kaynak ve performans metrikleri.* |

### 7. Performans ve Stres Testleri (k6)
| 7.1. Normal Yük Testi | 7.2. Chaos/Stres Testi |
|:---:|:---:|
| ![Step 7.1](docs/images/7.1.png) | ![Step 7.2](docs/images/7.2.png) |
| *Ortalam trafiğin izlenmesi.* | *Saldırı ve aşırı yük durumundaki tepki.* |

### 8. Ağ İzolasyonu Kanıtı
| 8.1. Doğrudan Erişim Engeli | 8.2. Gateway Üzerinden Erişim |
|:---:|:---:|
| ![Step 8.1](docs/images/8.1.png) | ![Step 8.2](docs/images/8.2.png) |
| *Mikroservislere dışarıdan ulaşılamadığı (Connection Refused).* | *İsteğin sadece Dispatcher (8080) üzerinden geçtiğinin ispatı.* |

## 📘 Adım Adım Doğrulama Kılavuzu

Galerideki her adımın neyi kanıtladığı ve nasıl gerçekleştirileceği aşağıda detaylandırılmıştır:

### 1. Sistem Başlatma (1.png)
*   **Amaç:** Konteyner orkestrasyonunun hatasız çalıştığını doğrulamak.
*   **Komut:** `docker-compose up --build`

### 2. Sağlık Kontrolü (2.png)
*   **Amaç:** Dispatcher'ın tüm mikroservisleri (Auth, User, Msg) canlı olarak takip ettiğini kanıtlamak.
*   **URL:** `http://localhost:8080/health`

### 3. Kimlik Doğrulama (3.png)
*   **Amaç:** `auth-service` üzerinden JWT (JSON Web Token) üretildiğini doğrulamak.
*   **Komut (PS):** `Invoke-RestMethod -Method Post -Uri "http://localhost:8080/auth/login" -ContentType "application/json" -Body '{"username":"emir","password":"sifre123"}'`

### 4. Güvenlik Bariyeri (4.png)
*   **Amaç:** Yetkisiz (tokensız) isteklerin Dispatcher seviyesinde 401 hatasıyla durdurulduğunu kanıtlamak.
*   **URL:** `http://localhost:8080/users`

### 5. Canlı Takip Arayüzü (5.png)
*   **Amaç:** Geliştirilen "Glassmorphism" Dashboard'un gerçek zamanlı trafik verilerini işlediğini göstermek.
*   **URL:** `http://localhost:8080/dashboard`

### 6. Performans Metrikleri (6.png)
*   **Amaç:** Prometheus ve Grafana üzerinden sistem kaynaklarının (CPU/RAM) izlenebildiğini doğrulamak.
*   **URL:** `http://localhost:3000` (admin/admin)

### 7. Yük ve Stres Testleri (7.1 & 7.2.png)
*   **Amaç:** Sistemin stabilite sınırlarını ve Rate Limiter'ın (429 hatası) saldırılara karşı tepkisini ölçmek.
*   **Komut (PS):** `Get-Content "Desktop/Project/scripts/load.js" | docker run --rm -i grafana/k6 run -`

### 8. Ağ İzolasyonu (8.1 & 8.2.png)
*   **Amaç:** Servislerin dışarıdan erişilemez (8.1) olduğunu, sadece Gateway (8.2) üzerinden ulaşılabildiğini kanıtlamak.
*   **Test:** `http://localhost:5001/health` (Başarısız) vs `http://localhost:8080/health` (Başarılı)

---

---

## 🛠 Teknoloji Yığını

*   **Backend**: Python / Flask
*   **Database**: MongoDB (Her servis ayrı DB kullanır)
*   **DevOps**: Docker & Docker Compose
*   **Performance**: k6 Load Testing
*   **Monitoring**: Prometheus & Grafana
*   **Documentation**: Mermaid.js Diagrams

---

## 🏁 Hızlı Başlangıç

Sistemi tek bir komutla ayağa kaldırabilirsiniz:

```powershell
docker-compose up --build
```

- **Dashboard**: `http://localhost:8080/dashboard`
- **Health Check**: `http://localhost:8080/health`
- **Grafana**: `http://localhost:3000` (admin/admin)

---

## 👨‍💻 Hazırlayanlar

*   **Muhammed Emir Karaman**
*   **Nuh**

---
> [!TIP]
> Bu proje, mikroservis dünyasında modern güvenlik ve performans standartlarını uygulamak için bir referans niteliğindedir.
