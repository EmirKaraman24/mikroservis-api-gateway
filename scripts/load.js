import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 50 },  // Ramp up to 50 users
    { duration: '30s', target: 50 },  // Maintain 50 concurrent users
    { duration: '10s', target: 0 },   // Scale down
  ],
};

export default function () {
  // Rastgele sekilde 4 ayri endpoint'e saldir
  const endpoints = ['/health', '/users', '/messages', '/auth/login'];
  const p = endpoints[Math.floor(Math.random() * endpoints.length)];
  
  if (p === '/auth/login') {
      http.post(`http://host.docker.internal:8080${p}`, JSON.stringify({username: "demo", password: "123"}), {headers: {"Content-Type": "application/json"}});
  } else {
      http.get(`http://host.docker.internal:8080${p}`);
  }
  
  // Kismi gecikme ile CPU tavan yapmasini engelle
  sleep(0.1);
}
