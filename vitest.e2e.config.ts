/**
 * Vitest E2E 테스트 설정
 *
 * monet-registry의 vitest 설정을 참고하여 구현
 */

import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // E2E 테스트 파일 패턴
    include: ['e2e/**/*.test.ts'],

    // 글로벌 설정 파일 (일시적으로 비활성화)
    // globalSetup: './e2e/setup.ts',

    // 테스트 타임아웃 (30초)
    testTimeout: 30000,

    // 훅 타임아웃 (60초)
    hookTimeout: 60000,

    // 순차 실행 (E2E 테스트는 순차 실행 권장)
    sequence: {
      shuffle: false,
    },

    // 환경
    environment: 'node',

    // 리포터
    reporters: ['verbose'],

    // 커버리지 (E2E는 보통 비활성화)
    coverage: {
      enabled: false,
    },

    // 재시도
    retry: 1,

    // 병렬 실행 비활성화
    pool: 'forks',
    poolOptions: {
      singleFork: true,
    },
  },
});
