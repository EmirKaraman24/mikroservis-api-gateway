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

Projenin tüm fonksiyonlarının çalıştığına dair 8 kritik adımın kanıtları aşağıdadır:

### 1-4. Sistem Başlatma ve Güvenlik Testleri
| 1. Docker Logları | 2. Health Check | 3. JWT Token / Auth | 4. 401 Güvenlik Engeli |
|:---:|:---:|:---:|:---:|
| ![Step 1](docs/images/step1.png) | ![Step 2](docs/images/step2.png) | ![Step 3](docs/images/step3.png) | ![Step 4](docs/images/step4.png) |
| *Sistemin hatasız ayağa kalkış kanıtı.* | *Tüm servislerin sağlıklı (OK) durumu.* | *Auth servisinden alınan JWT.* | *Yetkisiz girişin engellenmesi.* |

### 5. Canlı Trafik Dashboard (Geliştirilmiş)
![Traffic Dashboard](docs/images/step5.png)
*Sistemde akan trafiğin saniyelik, metod ve HTTP kodu bazlı izlendiği özel arayüz.*

### 6-7. Grafana ve Performans (k6) Analizi
![Grafana & k6](docs/images/step6_7.png)
*Sistemin 17 bin isteği karşıladığı stres testi ve metriklerin Grafana üzerindeki yansıması.*

### 8. Ağ İzolasyonu Kanıtı
![Isolation](docs/images/step8.png)
*Mikroservislere dışarıdan doğrudan ulaşılamadığı (Connection Refused), sadece 8080 üzerinden ulaşıldığının ispatı.*

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
