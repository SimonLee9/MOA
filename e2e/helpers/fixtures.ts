/**
 * E2E 테스트용 Fixtures (테스트 데이터)
 */

import { randomUUID } from 'crypto';

/**
 * 테스트용 회의 데이터
 */
export interface TestMeeting {
  id?: string;
  title: string;
  meeting_date?: string;
  speakers?: string[];
  status?: string;
}

export const testMeeting: TestMeeting = {
  title: 'E2E 테스트 회의',
  meeting_date: new Date().toISOString(),
  speakers: ['테스트 화자 1', '테스트 화자 2'],
};

export function createTestMeeting(overrides: Partial<TestMeeting> = {}): TestMeeting {
  return {
    ...testMeeting,
    title: `테스트 회의 ${randomUUID().slice(0, 8)}`,
    ...overrides,
  };
}

/**
 * 테스트용 액션 아이템 데이터
 */
export interface TestActionItem {
  content: string;
  assignee?: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export const testActionItem: TestActionItem = {
  content: 'E2E 테스트 액션 아이템',
  assignee: '테스트 담당자',
  priority: 'medium',
};

export function createTestActionItem(overrides: Partial<TestActionItem> = {}): TestActionItem {
  return {
    ...testActionItem,
    content: `테스트 액션 ${randomUUID().slice(0, 8)}`,
    ...overrides,
  };
}

/**
 * 테스트용 오디오 파일 (더미)
 */
export const testAudioFile = {
  name: 'test-audio.mp3',
  type: 'audio/mpeg',
  size: 1024 * 100, // 100KB

  // 더미 오디오 버퍼 생성
  toBuffer(): Buffer {
    // 실제 테스트에서는 fixtures 폴더의 실제 파일 사용
    return Buffer.alloc(this.size);
  },
};

/**
 * 테스트용 트랜스크립트 데이터
 */
export const testTranscript = {
  text: `
화자 1: 안녕하세요, 오늘 회의를 시작하겠습니다.
화자 2: 네, 준비되었습니다.
화자 1: 첫 번째 안건은 프로젝트 진행 상황입니다.
화자 2: 현재 80% 완료되었고, 다음 주까지 마무리할 예정입니다.
화자 1: 좋습니다. 그럼 다음 주 금요일까지 최종 보고서를 제출해 주세요.
화자 2: 네, 알겠습니다.
  `.trim(),

  segments: [
    { speaker: '화자 1', start: 0, end: 5, text: '안녕하세요, 오늘 회의를 시작하겠습니다.' },
    { speaker: '화자 2', start: 5, end: 8, text: '네, 준비되었습니다.' },
    { speaker: '화자 1', start: 8, end: 15, text: '첫 번째 안건은 프로젝트 진행 상황입니다.' },
    { speaker: '화자 2', start: 15, end: 25, text: '현재 80% 완료되었고, 다음 주까지 마무리할 예정입니다.' },
    { speaker: '화자 1', start: 25, end: 35, text: '좋습니다. 그럼 다음 주 금요일까지 최종 보고서를 제출해 주세요.' },
    { speaker: '화자 2', start: 35, end: 38, text: '네, 알겠습니다.' },
  ],

  speakers: ['화자 1', '화자 2'],
  duration_seconds: 38,
};

/**
 * 테스트용 사용자 데이터
 */
export interface TestUser {
  email: string;
  password: string;
  name: string;
}

export const testUser: TestUser = {
  email: 'test@example.com',
  password: 'testpassword123',
  name: '테스트 사용자',
};

export function createTestUser(overrides: Partial<TestUser> = {}): TestUser {
  const uuid = randomUUID().slice(0, 8);
  return {
    email: `test-${uuid}@example.com`,
    password: 'testpassword123',
    name: `테스트 사용자 ${uuid}`,
    ...overrides,
  };
}

/**
 * 테스트 ID 생성
 */
export function generateTestId(prefix = 'test'): string {
  return `${prefix}-${randomUUID()}`;
}

/**
 * 테스트 날짜 생성
 */
export function generateTestDate(daysFromNow = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString().split('T')[0];
}
