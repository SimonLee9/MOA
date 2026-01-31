/**
 * E2E 테스트 환경 설정
 *
 * monet-registry의 e2e/setup.ts를 참고하여 구현
 * 테스트 실행 전 서버 준비 상태를 확인합니다.
 */

import waitOn from 'wait-on';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const HEALTH_ENDPOINT = `${API_BASE_URL}/api/health`;
const TIMEOUT = parseInt(process.env.TEST_SETUP_TIMEOUT || '60000', 10);

/**
 * 테스트 시작 전 실행되는 글로벌 설정
 */
export async function setup(): Promise<void> {
  console.log('🚀 MOA E2E Test Setup');
  console.log(`   API URL: ${API_BASE_URL}`);
  console.log(`   Timeout: ${TIMEOUT}ms`);
  console.log('');

  try {
    console.log('⏳ Waiting for API server...');

    await waitOn({
      resources: [HEALTH_ENDPOINT],
      timeout: TIMEOUT,
      interval: 1000,
      validateStatus: (status: number) => status === 200,
      headers: {
        'Accept': 'application/json',
      },
    });

    console.log('✅ API server is ready!');
    console.log('');

    // 추가 초기화 (필요시)
    await initializeTestData();

  } catch (error) {
    console.error('❌ Failed to connect to API server');
    console.error(`   Endpoint: ${HEALTH_ENDPOINT}`);
    console.error(`   Error: ${error instanceof Error ? error.message : error}`);
    console.error('');
    console.error('💡 Make sure the server is running:');
    console.error('   docker-compose up -d');
    console.error('   OR');
    console.error('   cd backend && uvicorn app.main:app --reload');
    console.error('');

    process.exit(1);
  }
}

/**
 * 테스트 종료 후 실행되는 정리 작업
 */
export async function teardown(): Promise<void> {
  console.log('');
  console.log('🧹 MOA E2E Test Teardown');

  try {
    await cleanupTestData();
    console.log('✅ Cleanup completed');
  } catch (error) {
    console.warn('⚠️ Cleanup warning:', error);
  }
}

/**
 * 테스트 데이터 초기화
 */
async function initializeTestData(): Promise<void> {
  // 테스트용 시드 데이터 생성
  // 실제 구현에서는 API를 호출하여 테스트 데이터 설정
  console.log('📦 Initializing test data...');

  // 예: 테스트 사용자 생성, 테스트 회의 생성 등
}

/**
 * 테스트 데이터 정리
 */
async function cleanupTestData(): Promise<void> {
  // 테스트 중 생성된 데이터 정리
  console.log('🗑️  Cleaning up test data...');

  // 예: 테스트 회의 삭제, 업로드된 파일 삭제 등
}

// Default export for Vitest globalSetup
export default async function globalSetup(): Promise<() => Promise<void>> {
  await setup();
  return teardown;
}
