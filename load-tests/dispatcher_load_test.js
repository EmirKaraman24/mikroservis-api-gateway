// load-tests/dispatcher_load_test.js
// ─────────────────────────────────────
// k6 Yük Testi — Dispatcher Microservice
//
// Hedef: Dispatcher'ın 50, 100, 200 ve 500 eş zamanlı kullanıcı
// (Virtual User - VU) altında nasıl davrandığını ölçmek.
//
// Çalıştırmak için:
//   k6 run dispatcher_load_test.js
//   k6 run --vus 100 --duration 30s dispatcher_load_test.js
//
// Raporlama:
//   k6 run --out json=results/result_50vu.json dispatcher_load_test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ── Özel Metrikler ──────────────────────────────────────────────────────────
const errorRate     = new Rate('error_rate');
const requestTrend  = new Trend('request_duration', true);
const totalRequests = new Counter('total_requests');

// ── Test Konfigürasyonu ─────────────────────────────────────────────────────
// Aşamalar: 50 → 100 → 200 → 500 VU ramping senaryosu
export const options = {
  stages: [
    // Warm-up: 0'dan 50 VU'ya çık
    { duration: '30s', target: 50  },
    // 50 VU ile stabil çalış
    { duration: '60s', target: 50  },
    // 100 VU'ya ramping
    { duration: '30s', target: 100 },
    // 100 VU ile stabil çalış
    { duration: '60s', target: 100 },
    // 200 VU'ya ramping
    { duration: '30s', target: 200 },
    // 200 VU ile stabil çalış
    { duration: '60s', target: 200 },
    // 500 VU'ya ramping (stres testi)
    { duration: '30s', target: 500 },
    // 500 VU ile stabil çalış
    { duration: '60s', target: 500 },
    // Cool-down: 0'a in
    { duration: '30s', target: 0   },
  ],
  thresholds: {
    // p95 yanıt süresi 500ms altında olmalı
    'http_req_duration': ['p(95)<500'],
    // Hata oranı %5'in altında olmalı
    'error_rate': ['rate<0.05'],
    // p99 yanıt süresi 1 saniyenin altında olmalı
    'http_req_duration{type:critical}': ['p(99)<1000'],
  },
};

// ── Test Ortamı Ayarları ────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

// Test için geçerli bir Bearer token (gerçek ortamda dinamik alınır)
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'test-token-k6-load';

const HEADERS = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${AUTH_TOKEN}`,
};

// ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────
function checkResponse(res, expectedStatus, tag) {
  const ok = check(res, {
    [`${tag}: status ${expectedStatus}`]: (r) => r.status === expectedStatus,
    [`${tag}: response time < 500ms`]:    (r) => r.timings.duration < 500,
  });
  errorRate.add(!ok);
  requestTrend.add(res.timings.duration);
  totalRequests.add(1);
  return ok;
}

// ── Ana Test Fonksiyonu ─────────────────────────────────────────────────────
export default function () {
  const vuId = __VU;
  const iter = __ITER;

  // Senaryo 1: Health check endpoint
  {
    const res = http.get(`${BASE_URL}/health`, { tags: { type: 'health' } });
    checkResponse(res, 200, 'health_check');
  }

  sleep(0.1);

  // Senaryo 2: Kullanıcı listesi al (GET /users)
  {
    const res = http.get(`${BASE_URL}/users`, {
      headers: HEADERS,
      tags: { type: 'critical' },
    });
    checkResponse(res, 200, 'get_users');
  }

  sleep(0.1);

  // Senaryo 3: Tek kullanıcı al (GET /users/:id)
  {
    const userId = (vuId % 10) + 1; // VU başına farklı bir kullanıcı
    const res = http.get(`${BASE_URL}/users/${userId}`, {
      headers: HEADERS,
      tags: { type: 'critical' },
    });
    // 200 veya 404 kabul edilebilir (kullanıcı olmayabilir)
    check(res, {
      'get_user_by_id: status ok': (r) => [200, 404].includes(r.status),
    });
    requestTrend.add(res.timings.duration);
    totalRequests.add(1);
  }

  sleep(0.1);

  // Senaryo 4: Mesaj gönder (POST /messages)
  {
    const payload = JSON.stringify({
      sender:  `vu-${vuId}`,
      content: `Load test mesajı #${iter} - VU ${vuId}`,
      ts:      Date.now(),
    });
    const res = http.post(`${BASE_URL}/messages`, payload, {
      headers: HEADERS,
      tags: { type: 'critical' },
    });
    checkResponse(res, 201, 'post_message');
  }

  sleep(0.5);
}

// ── Özet Rapor ─────────────────────────────────────────────────────────────
export function handleSummary(data) {
  return {
    'results/summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, opts) {
  const metrics = data.metrics;
  const lines = [
    '',
    '═══════════════════════════════════════════════════════════',
    '    k6 Dispatcher Yük Testi — Özet Rapor',
    '═══════════════════════════════════════════════════════════',
    `  Toplam İstek : ${metrics.total_requests?.values.count  || 'N/A'}`,
    `  Hata Oranı   : ${((metrics.error_rate?.values.rate || 0) * 100).toFixed(2)}%`,
    `  Ort. Süre    : ${(metrics.http_req_duration?.values.avg || 0).toFixed(2)} ms`,
    `  p95 Süre     : ${(metrics.http_req_duration?.values['p(95)'] || 0).toFixed(2)} ms`,
    `  p99 Süre     : ${(metrics.http_req_duration?.values['p(99)'] || 0).toFixed(2)} ms`,
    `  Maks. Süre   : ${(metrics.http_req_duration?.values.max || 0).toFixed(2)} ms`,
    '═══════════════════════════════════════════════════════════',
    '',
  ];
  return lines.join('\n');
}
