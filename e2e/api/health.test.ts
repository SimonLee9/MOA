/**
 * Health Check API E2E 테스트
 */

import { describe, it, expect } from 'vitest';
import { apiClient } from '../helpers/client';

describe('Health API', () => {
  describe('GET /api/health', () => {
    it('should return 200 OK', async () => {
      const response = await apiClient.get('/api/health');

      expect(response.status).toBe(200);
    });

    it('should return health status', async () => {
      const response = await apiClient.get('/api/health');

      expect(response.data).toHaveProperty('status');
      expect(response.data.status).toBe('healthy');
    });

    it('should include service checks', async () => {
      const response = await apiClient.get('/api/health');

      expect(response.data).toHaveProperty('services');
      expect(response.data.services).toHaveProperty('database');
      expect(response.data.services).toHaveProperty('redis');
    });

    it('should include version info', async () => {
      const response = await apiClient.get('/api/health');

      expect(response.data).toHaveProperty('version');
    });
  });

  describe('GET /api/health/ready', () => {
    it('should return readiness status', async () => {
      const response = await apiClient.get('/api/health/ready');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('ready');
    });
  });

  describe('GET /api/health/live', () => {
    it('should return liveness status', async () => {
      const response = await apiClient.get('/api/health/live');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('alive');
      expect(response.data.alive).toBe(true);
    });
  });
});
