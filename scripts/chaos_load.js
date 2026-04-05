import http from 'k6/http';
import { sleep, check } from 'k6';

// ── SENARYO: CHAOS & BURST SALDIRISI ──────────────────────────────────────────
// Bu script, sisteme aşırı yüklenerek hem Rate Limiting hem de hatalı giriş gibi 
// karmaşa/saldırı durumlarını test eder.
// Dispatcher'ın 429 Too Many Requests cevabı vermesi hedeflenir.

export const options = {
  stages: [
    { duration: '10s', target: 50  }, // Isınma: 50 kullanıcı
    { duration: '30s', target: 200 }, // Zirve: 200 kullanıcı (Saldırı simülasyonu)
    { duration: '10s', target: 0   }, // Soğuma
  ],
};

const BASE_URL = __ENV.BASE_URL || 'http://host.docker.internal:8080';

export default function () {
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 1. Durum: Rate Limiting Hamlesi (Hammet / Burst)
    // BEKLEME SÜRESİ YOK — Saniyeler içinde çok sayıda istek gönderir.
    const res = http.get(`${BASE_URL}/health`);
    
    check(res, {
      'status is 200 or 429': (r) => [200, 429].includes(r.status),
      'is rate limited (429)': (r) => r.status === 429,
    });
    
    // Çok hızlı gönderim
    sleep(0.01);

  } else if (scenario < 0.7) {
    // 2. Durum: Yetkisiz Erişim / Hatalı Token
    const params = {
      headers: { 'Authorization': 'Bearer SALDIRGAN_VEYA_HATALI_TOKEN' },
    };
    const res = http.get(`${BASE_URL}/users`, params);
    
    check(res, {
      'status is 401 (Auth failed)': (r) => r.status === 401,
    });
    
    sleep(0.5);

  } else {
    // 3. Durum: Kaynak Tüketimi (Geçersiz Path'ler)
    const randomPath = `/unknown/api/${Math.random().toString(36).substring(7)}`;
    const res = http.get(`${BASE_URL}${randomPath}`);
    
    check(res, {
      'status is 404 (Not Found)': (r) => r.status === 404,
    });

    sleep(0.5);
  }
}
