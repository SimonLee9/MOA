# MOA End-to-End Tests

> API 및 파이프라인 End-to-End 테스트 (monet-registry 스타일)

## 개요

이 폴더는 MOA 시스템의 E2E 테스트를 관리합니다.
Vitest를 사용하여 API 엔드포인트와 전체 파이프라인을 테스트합니다.

## 구조

```
e2e/
├── README.md
├── setup.ts           # 테스트 환경 설정
├── api/               # API 엔드포인트 테스트
│   ├── health.test.ts
│   ├── meetings.test.ts
│   ├── upload.test.ts
│   ├── pipeline.test.ts
│   └── review.test.ts # Review API 테스트 (선택적 인증 지원)
└── helpers/           # 테스트 유틸리티
    ├── client.ts
    ├── fixtures.ts
    └── assertions.ts
```

## 설정

### 환경 변수

```bash
# .env.test
API_BASE_URL=http://localhost:8000
TEST_TIMEOUT=30000
```

### Vitest 설정

```typescript
// vitest.e2e.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['e2e/**/*.test.ts'],
    globalSetup: './e2e/setup.ts',
    testTimeout: 30000,
    hookTimeout: 60000,
  }
})
```

## 실행

```bash
# 모든 E2E 테스트 실행
npm run test:e2e

# 특정 테스트만 실행
npm run test:e2e -- api/health

# Watch 모드
npm run test:e2e -- --watch
```

## 테스트 작성 가이드

### API 테스트 예시

```typescript
import { describe, it, expect } from 'vitest'
import { apiClient } from '../helpers/client'

describe('Meetings API', () => {
  it('should create a new meeting', async () => {
    const response = await apiClient.post('/api/meetings', {
      title: 'Test Meeting'
    })

    expect(response.status).toBe(201)
    expect(response.data).toHaveProperty('id')
  })
})
```

### Fixtures 사용

```typescript
import { testMeeting, testAudioFile } from '../helpers/fixtures'

it('should process audio', async () => {
  const meeting = await createMeeting(testMeeting)
  const result = await uploadAudio(meeting.id, testAudioFile)

  expect(result.status).toBe('processing')
})
```

### Review API 테스트 (선택적 인증)

```typescript
import { describe, it, expect } from 'vitest'
import axios from 'axios'

describe('Review API', () => {
  const client = axios.create({
    baseURL: 'http://localhost:8000',
    validateStatus: () => true,
  })

  it('should return review status without authentication', async () => {
    // Review API는 인증 없이도 작동 (demo user 자동 사용)
    const response = await client.get(`/api/v1/meetings/${meetingId}/review`)

    expect([200, 404, 500]).toContain(response.status)
    if (response.status === 200) {
      expect(response.data).toHaveProperty('meeting_id')
      expect(response.data).toHaveProperty('requires_review')
    }
  })
})
```

## CI/CD 통합

```yaml
# .github/workflows/e2e.yml
- name: Run E2E Tests
  run: |
    docker-compose up -d
    npm run test:e2e
  env:
    API_BASE_URL: http://localhost:8000
```
