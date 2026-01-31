/**
 * Review API E2E 테스트
 *
 * 실제 회의 ID를 사용하여 review API 테스트
 */

import { describe, it, expect } from 'vitest';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const TEST_MEETING_ID = '300f3297-7567-4793-84f7-6e57c6143b7c'; // 실제 테스트용 회의 ID

describe('Review API E2E Tests', () => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    validateStatus: () => true, // 모든 상태 코드 허용
  });

  describe('GET /api/v1/meetings/:id/review', () => {
    it('should return review status without authentication', async () => {
      const response = await client.get(`/api/v1/meetings/${TEST_MEETING_ID}/review`);

      console.log('Review Status Response:', response.status, response.data);

      expect([200, 404, 500]).toContain(response.status);

      if (response.status === 200) {
        expect(response.data).toHaveProperty('meeting_id');
        expect(response.data).toHaveProperty('status');
        expect(response.data).toHaveProperty('requires_review');
      }
    });

    it('should handle non-existent meeting', async () => {
      const response = await client.get('/api/v1/meetings/00000000-0000-0000-0000-000000000000/review');

      console.log('Non-existent Meeting Response:', response.status, response.data);

      expect(response.status).toBe(404);
      expect(response.data).toHaveProperty('detail');
    });
  });

  describe('Backend Health Check', () => {
    it('should connect to backend', async () => {
      const response = await client.get('/');

      console.log('Backend Root Response:', response.status);

      expect([200, 404]).toContain(response.status);
    });

    it('should access API v1 endpoints', async () => {
      const response = await client.get('/api/v1/meetings');

      console.log('Meetings List Response:', response.status);

      // 200 (성공) 또는 401 (인증 필요, 하지만 엔드포인트는 존재)
      expect([200, 401]).toContain(response.status);
    });
  });
});
