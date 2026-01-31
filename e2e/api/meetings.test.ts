/**
 * Meetings API E2E 테스트
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { apiClient } from '../helpers/client';
import { createTestMeeting, TestMeeting } from '../helpers/fixtures';

describe('Meetings API', () => {
  let createdMeetingId: string;

  describe('POST /api/meetings', () => {
    it('should create a new meeting', async () => {
      const meeting = createTestMeeting();

      const response = await apiClient.post('/api/meetings', meeting);

      expect(response.status).toBe(201);
      expect(response.data.data).toHaveProperty('id');
      expect(response.data.data.title).toBe(meeting.title);
      expect(response.data.data.status).toBe('uploaded');

      createdMeetingId = response.data.data.id;
    });

    it('should return 400 for missing title', async () => {
      try {
        await apiClient.post('/api/meetings', {});
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data).toHaveProperty('detail');
      }
    });

    it('should validate meeting_date format', async () => {
      const meeting = createTestMeeting({
        meeting_date: 'invalid-date',
      });

      try {
        await apiClient.post('/api/meetings', meeting);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
      }
    });
  });

  describe('GET /api/meetings', () => {
    it('should return paginated meetings list', async () => {
      const response = await apiClient.get('/api/meetings');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('items');
      expect(response.data).toHaveProperty('total');
      expect(response.data).toHaveProperty('page');
      expect(response.data).toHaveProperty('size');
      expect(Array.isArray(response.data.items)).toBe(true);
    });

    it('should support pagination parameters', async () => {
      const response = await apiClient.get('/api/meetings', {
        params: { page: 1, size: 5 },
      });

      expect(response.status).toBe(200);
      expect(response.data.page).toBe(1);
      expect(response.data.size).toBe(5);
      expect(response.data.items.length).toBeLessThanOrEqual(5);
    });

    it('should support status filter', async () => {
      const response = await apiClient.get('/api/meetings', {
        params: { status: 'completed' },
      });

      expect(response.status).toBe(200);
      response.data.items.forEach((meeting: TestMeeting) => {
        expect(meeting.status).toBe('completed');
      });
    });

    it('should support search by title', async () => {
      const response = await apiClient.get('/api/meetings', {
        params: { search: '테스트' },
      });

      expect(response.status).toBe(200);
      response.data.items.forEach((meeting: TestMeeting) => {
        expect(meeting.title.toLowerCase()).toContain('테스트');
      });
    });
  });

  describe('GET /api/meetings/:id', () => {
    it('should return meeting by id', async () => {
      // 먼저 회의 생성
      const meeting = createTestMeeting();
      const createResponse = await apiClient.post('/api/meetings', meeting);
      const meetingId = createResponse.data.data.id;

      const response = await apiClient.get(`/api/meetings/${meetingId}`);

      expect(response.status).toBe(200);
      expect(response.data.data.id).toBe(meetingId);
      expect(response.data.data.title).toBe(meeting.title);
    });

    it('should return 404 for non-existent meeting', async () => {
      try {
        await apiClient.get('/api/meetings/non-existent-id');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(404);
      }
    });
  });

  describe('PUT /api/meetings/:id', () => {
    it('should update meeting', async () => {
      // 먼저 회의 생성
      const meeting = createTestMeeting();
      const createResponse = await apiClient.post('/api/meetings', meeting);
      const meetingId = createResponse.data.data.id;

      const updatedTitle = '업데이트된 회의 제목';
      const response = await apiClient.put(`/api/meetings/${meetingId}`, {
        title: updatedTitle,
      });

      expect(response.status).toBe(200);
      expect(response.data.data.title).toBe(updatedTitle);
    });

    it('should return 404 for non-existent meeting', async () => {
      try {
        await apiClient.put('/api/meetings/non-existent-id', {
          title: 'New Title',
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(404);
      }
    });
  });

  describe('DELETE /api/meetings/:id', () => {
    it('should delete meeting', async () => {
      // 먼저 회의 생성
      const meeting = createTestMeeting();
      const createResponse = await apiClient.post('/api/meetings', meeting);
      const meetingId = createResponse.data.data.id;

      const response = await apiClient.delete(`/api/meetings/${meetingId}`);

      expect(response.status).toBe(204);

      // 삭제 확인
      try {
        await apiClient.get(`/api/meetings/${meetingId}`);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(404);
      }
    });
  });

  describe('GET /api/meetings/:id/summary', () => {
    it('should return meeting summary', async () => {
      // 완료된 회의가 필요
      const response = await apiClient.get('/api/meetings', {
        params: { status: 'completed', size: 1 },
      });

      if (response.data.items.length > 0) {
        const meetingId = response.data.items[0].id;
        const summaryResponse = await apiClient.get(`/api/meetings/${meetingId}/summary`);

        expect(summaryResponse.status).toBe(200);
        expect(summaryResponse.data.data).toHaveProperty('summary');
      }
    });
  });

  describe('GET /api/meetings/:id/actions', () => {
    it('should return meeting action items', async () => {
      // 완료된 회의가 필요
      const response = await apiClient.get('/api/meetings', {
        params: { status: 'completed', size: 1 },
      });

      if (response.data.items.length > 0) {
        const meetingId = response.data.items[0].id;
        const actionsResponse = await apiClient.get(`/api/meetings/${meetingId}/actions`);

        expect(actionsResponse.status).toBe(200);
        expect(actionsResponse.data).toHaveProperty('items');
        expect(Array.isArray(actionsResponse.data.items)).toBe(true);
      }
    });
  });

  // 테스트 후 정리
  afterAll(async () => {
    if (createdMeetingId) {
      try {
        await apiClient.delete(`/api/meetings/${createdMeetingId}`);
      } catch {
        // 이미 삭제된 경우 무시
      }
    }
  });
});
