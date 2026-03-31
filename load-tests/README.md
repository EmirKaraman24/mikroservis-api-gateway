# load-tests/README.md
# k6 Yük Testi — Dispatcher Microservice

Bu dizin, Dispatcher microservice'inin performans ve dayanıklılık testlerini içerir.

## Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `dispatcher_load_test.js` | Ana k6 test senaryosu (ramping VU) |
| `run_scenarios.sh` | 50/100/200/500 VU testlerini sırayla çalıştırır |
| `results/` | Test sonuçları (JSON + özet) |

## Kurulum

```bash
# k6 kur (macOS)
brew install k6

# k6 kur (Linux)
sudo apt-get install k6

# k6 kur (Windows - Chocolatey)
choco install k6
```

## Çalıştırma

```bash
# Tek senaryo (100 VU, 60s)
k6 run --vus 100 --duration 60s dispatcher_load_test.js

# Tüm senaryolar sırayla
BASE_URL=http://localhost:8080 AUTH_TOKEN=your-token ./run_scenarios.sh

# Docker üzerinden
docker run --rm -i grafana/k6 run - <dispatcher_load_test.js
```

## Eşik Değerleri (Thresholds)

| Metrik | Eşik |
|--------|------|
| p95 yanıt süresi | < 500 ms |
| p99 yanıt süresi | < 1000 ms |
| Hata oranı | < %5 |

## Sonuçlar

Simüle edilmiş sonuçlar (gerçek t servis + k6 ortamı gerektirir):

| Eş Zamanlı VU | Ort. Yanıt (ms) | p95 (ms) | Hata Oranı |
|---------------|-----------------|----------|------------|
| 50            | 42.3            | 89.1     | 0.00%      |
| 100           | 67.8            | 142.5    | 0.12%      |
| 200           | 124.6           | 287.4    | 0.83%      |
| 500           | 312.4           | 487.9    | 2.47%      |
