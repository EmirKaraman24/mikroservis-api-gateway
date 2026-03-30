import http from 'k6/http';
import { check, sleep } from 'k6';

// Allow target VUs to be configured via environment variable, defaulting to 50
const targetVUs = __ENV.VUS ? parseInt(__ENV.VUS) : 50;

export const options = {
  scenarios: {
    dispatcher_load_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: targetVUs }, // Ramp up to target VUs
        { duration: '30s', target: targetVUs }, // Stay at target VUs
        { duration: '10s', target: 0 },         // Ramp down to 0 VUs
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // 1. Health Check
  const healthRes = http.get(`${BASE_URL}/health`, params);
  check(healthRes, {
    'health check is 200': (r) => r.status === 200,
  });

  // 2. Users Endpoint (Simulating read traffic)
  const usersRes = http.get(`${BASE_URL}/users`, params);
  check(usersRes, {
    'users endpoint is 200': (r) => r.status === 200,
  });

  // 3. Messages Endpoint (Simulating read traffic)
  const msgsRes = http.get(`${BASE_URL}/messages`, params);
  check(msgsRes, {
    'messages endpoint is 200': (r) => r.status === 200,
  });

  sleep(1);
}
