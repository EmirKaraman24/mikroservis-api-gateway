import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 20 },  // Isınma: 20 kullanıcı
    { duration: '40s', target: 150 }, // Saldırı: 150 eşzamanlı kullanıcı (Sınırları zorla)
    { duration: '20s', target: 300 }, // Zirve: 300 kullanıcı (Stres testi)
    { duration: '20s', target: 0 },   // Soğuma
  ],
};

const BASE_URL = 'http://host.docker.internal:8080';

export default function () {
  // Rastgele bir senaryo seç
  const scenario = Math.random();

  if (scenario < 0.3) {
    // 1. Durum: Meşru ama yoğun trafik (Health & Auth Login)
    http.get(`${BASE_URL}/health`);
    http.post(`${BASE_URL}/auth/login`, JSON.stringify({
      username: "attacker",
      password: "wrong_password"
    }), { headers: { 'Content-Type': 'application/json' } });

  } else if (scenario < 0.6) {
    // 2. Durum: Yetkisiz erişim denemeleri (JWT yok veya hatalı)
    const params = {
      headers: { 'Authorization': 'Bearer hatali_token_123' },
    };
    http.get(`${BASE_URL}/users`, params);
    http.get(`${BASE_URL}/messages`, params);
    
    // Auth başlığı olmadan doğrudan saldırı
    http.get(`${BASE_URL}/users/profile/secret`);

  } else if (scenario < 0.8) {
    // 3. Durum: Fuzzing / Kaynak Tüketimi (Geçersiz rotalar ve metodlar)
    const randomPath = `/api/v1/admin/${Math.random().toString(36).substring(7)}`;
    http.del(`${BASE_URL}${randomPath}`); // Rastgele yerlere DELETE at
    http.patch(`${BASE_URL}/messages/bulk-delete`); // Olmayan bir yere PATCH at

  } else {
    // 4. Durum: Büyük veri gönderimi (Memory zorlama)
    const largeBody = JSON.stringify({ data: "A".repeat(1024 * 10) }); // 10KB veri
    http.post(`${BASE_URL}/messages/send`, largeBody, {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  sleep(0.05); // Çok hızlı istek gönderimi
}
