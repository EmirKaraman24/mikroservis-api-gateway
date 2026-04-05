import http from 'k6/http';
import { sleep, check } from 'k6';

// ── SENARYO: NORMAL YÜK TESTİ ──────────────────────────────────────────────
// Bu script, sistemin sağlıklı ve stabil olduğunu göstermek içindir.
// Kademeli olarak 50 kullanıcıya çıkar ve sistemin performansını ölçer.

export const options = {
  stages: [
    { duration: '10s', target: 50 },  // Isınma: 50 kullanıcıya çık
    { duration: '30s', target: 50 },  // Stabil: 30 saniye boyunca yük altında tut
    { duration: '10s', target: 0  },  // Soğuma: Sistemi rahatlat
  ],
  thresholds: {
    // Yanıtların %95'i 200ms altında olmalı
    http_req_duration: ['p(95)<200'],
    // İsteklerin %99'u başarılı olmalı (2xx veya 3xx)
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://host.docker.internal:8080';

export default function () {
  // Rastgele bir endpoint seç
  const endpoints = ['/health', '/auth/login', '/users', '/messages'];
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  
  let res;
  if (endpoint === '/auth/login') {
    res = http.post(`${BASE_URL}${endpoint}`, 
      JSON.stringify({ username: "emir", password: "pass123" }), 
      { headers: { 'Content-Type': 'application/json' } }
    );
  } else {
    // Diğerleri için GET (Auth gerektirenlerde 401 bekliyoruz)
    res = http.get(`${BASE_URL}${endpoint}`);
  }

  // Kontroller: Durum kodlarını doğrula
  check(res, {
    'status is expected': (r) => [200, 201, 401].includes(r.status),
    'response time ok':   (r) => r.timings.duration < 500,
  });
  
  // Gerçekçi bekleme süresi: 0.2 - 0.5 saniye
  sleep(Math.random() * 0.3 + 0.2);
}
