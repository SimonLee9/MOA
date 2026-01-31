/**
 * AI Pipeline E2E 테스트
 *
 * 전체 파이프라인 흐름을 테스트합니다:
 * 오디오 업로드 → STT → 요약 → 액션 추출 → 완료
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { apiClient, uploadFile } from '../helpers/client';
import { createTestMeeting, testAudioFile, testTranscript } from '../helpers/fixtures';

describe('Pipeline E2E', () => {
  let testMeetingId: string;

  beforeAll(async () => {
    // 테스트용 회의 생성
    const meeting = createTestMeeting({ title: 'Pipeline E2E 테스트 회의' });
    const response = await apiClient.post('/api/meetings', meeting);
    testMeetingId = response.data.data.id;
  });

  describe('Full Pipeline Flow', () => {
    it('should process meeting through entire pipeline', async () => {
      // 1. 오디오 업로드
      const uploadResponse = await uploadFile(
        `/api/meetings/${testMeetingId}/upload`,
        testAudioFile.toBuffer(),
        testAudioFile.name
      );

      expect(uploadResponse.status).toBe(202); // Accepted
      expect(uploadResponse.data).toHaveProperty('task_id');

      const taskId = uploadResponse.data.task_id;

      // 2. 처리 상태 폴링
      let status = 'processing';
      let attempts = 0;
      const maxAttempts = 60; // 최대 60초 대기

      while (status === 'processing' && attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 1000));

        const statusResponse = await apiClient.get(`/api/tasks/${taskId}`);
        status = statusResponse.data.status;
        attempts++;

        if (process.env.DEBUG) {
          console.log(`Pipeline status: ${status} (attempt ${attempts})`);
        }
      }

      // 3. 최종 상태 확인
      expect(status).toBe('completed');

      // 4. 결과 검증
      const meetingResponse = await apiClient.get(`/api/meetings/${testMeetingId}`);
      const meeting = meetingResponse.data.data;

      expect(meeting.status).toBe('completed');
      expect(meeting).toHaveProperty('transcript');
      expect(meeting).toHaveProperty('summary');
      expect(meeting).toHaveProperty('action_items');
    }, 120000); // 2분 타임아웃
  });

  describe('Pipeline Status API', () => {
    it('should return pipeline status for meeting', async () => {
      const response = await apiClient.get(`/api/meetings/${testMeetingId}/pipeline-status`);

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('stages');
      expect(response.data.stages).toHaveProperty('stt');
      expect(response.data.stages).toHaveProperty('summarization');
      expect(response.data.stages).toHaveProperty('action_extraction');
    });

    it('should include timing information', async () => {
      const response = await apiClient.get(`/api/meetings/${testMeetingId}/pipeline-status`);

      expect(response.data).toHaveProperty('started_at');
      expect(response.data).toHaveProperty('completed_at');
      expect(response.data).toHaveProperty('duration_seconds');
    });
  });

  describe('Pipeline Retry', () => {
    it('should allow retrying failed pipeline', async () => {
      // 실패한 회의 찾기 또는 시뮬레이션
      const failedMeetings = await apiClient.get('/api/meetings', {
        params: { status: 'failed', size: 1 },
      });

      if (failedMeetings.data.items.length > 0) {
        const failedMeetingId = failedMeetings.data.items[0].id;

        const response = await apiClient.post(`/api/meetings/${failedMeetingId}/retry`);

        expect(response.status).toBe(202);
        expect(response.data).toHaveProperty('task_id');
      }
    });
  });

  describe('Pipeline Cancel', () => {
    it('should allow canceling processing pipeline', async () => {
      // 새 회의 생성 및 처리 시작
      const meeting = createTestMeeting({ title: 'Cancel 테스트' });
      const createResponse = await apiClient.post('/api/meetings', meeting);
      const meetingId = createResponse.data.data.id;

      // 오디오 업로드하여 처리 시작
      await uploadFile(
        `/api/meetings/${meetingId}/upload`,
        testAudioFile.toBuffer(),
        testAudioFile.name
      );

      // 즉시 취소 시도
      const cancelResponse = await apiClient.post(`/api/meetings/${meetingId}/cancel`);

      // 취소가 가능한 경우
      if (cancelResponse.status === 200) {
        expect(cancelResponse.data.status).toBe('cancelled');
      }
      // 이미 완료된 경우
      else if (cancelResponse.status === 400) {
        expect(cancelResponse.data.detail).toContain('already');
      }
    });
  });

  describe('Pipeline Stages', () => {
    describe('STT Stage', () => {
      it('should return transcript with speaker diarization', async () => {
        const response = await apiClient.get(`/api/meetings/${testMeetingId}/transcript`);

        expect(response.status).toBe(200);
        expect(response.data.data).toHaveProperty('text');
        expect(response.data.data).toHaveProperty('segments');
        expect(response.data.data).toHaveProperty('speakers');

        // 세그먼트 구조 확인
        if (response.data.data.segments.length > 0) {
          const segment = response.data.data.segments[0];
          expect(segment).toHaveProperty('speaker');
          expect(segment).toHaveProperty('start');
          expect(segment).toHaveProperty('end');
          expect(segment).toHaveProperty('text');
        }
      });
    });

    describe('Summarization Stage', () => {
      it('should return structured summary', async () => {
        const response = await apiClient.get(`/api/meetings/${testMeetingId}/summary`);

        expect(response.status).toBe(200);
        expect(response.data.data).toHaveProperty('summary');
        expect(response.data.data).toHaveProperty('key_points');
      });
    });

    describe('Action Extraction Stage', () => {
      it('should return extracted action items', async () => {
        const response = await apiClient.get(`/api/meetings/${testMeetingId}/actions`);

        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('items');

        if (response.data.items.length > 0) {
          const action = response.data.items[0];
          expect(action).toHaveProperty('content');
          expect(action).toHaveProperty('priority');
        }
      });
    });
  });
});
