# MOA 개선사항 로드맵

> **Version**: 2.1.0
> **Last Updated**: 2026-01-10
> **Status**: MVP 완료, 고도화 단계 준비

---

## 현재 상태 요약

### ✅ 완료된 기능 (MVP)

| 기능 | 파일 | 상태 |
|------|------|------|
| Tus 프로토콜 업로드 | `backend/app/api/v1/tus_upload.py` | ✅ |
| Naver Clova STT 통합 | `ai_pipeline/pipeline/integrations/clova_stt.py` | ✅ |
| LLM 요약/추출/검증 | `ai_pipeline/pipeline/prompts/*.py` | ✅ |
| LangGraph 파이프라인 | `ai_pipeline/pipeline/graph.py` | ✅ |
| PostgreSQL 체크포인터 | `ai_pipeline/pipeline/checkpointer.py` | ✅ |
| Human-in-the-Loop API | `backend/app/api/v1/review.py` | ✅ |
| HITL 프론트엔드 UI | `frontend/components/review/ReviewPanel.tsx` | ✅ |
| MCP 클라이언트 | `ai_pipeline/pipeline/integrations/mcp_client.py` | ✅ |
| WebSocket 스트리밍 | `backend/app/api/v1/websocket.py` | ✅ |
| 메트릭 API | `backend/app/api/v1/metrics.py` | ✅ |

---

## 개선사항 목록

### 🔴 P0 - 긴급 (배포 전 필수)

| # | 항목 | 설명 | 예상 작업량 |
|---|------|------|------------|
| 1 | **테스트 코드 작성** | 백엔드 API, AI 파이프라인 단위/통합 테스트 | 대 |
| 2 | **환경 변수 검증** | 시작 시 필수 환경 변수 체크 및 에러 메시지 | 소 |
| 3 | **보안 검토** | JWT 만료 처리, CORS 설정, 입력 검증 강화 | 중 |

#### 상세: 테스트 코드 작성

```
backend/tests/
├── test_api/
│   ├── test_auth.py
│   ├── test_meetings.py
│   ├── test_review.py
│   └── test_upload.py
├── test_services/
│   └── test_meeting_service.py
└── conftest.py (fixtures)

ai_pipeline/tests/
├── test_nodes/
│   ├── test_stt_node.py
│   ├── test_summarizer_node.py
│   └── test_critique_node.py
├── test_integrations/
│   ├── test_clova_stt.py
│   └── test_claude_llm.py
└── test_graph.py
```

---

### 🟠 P1 - 높음 (1차 릴리즈 후)

| # | 항목 | 설명 | 예상 작업량 |
|---|------|------|------------|
| 4 | **에러 핸들링 강화** | 파이프라인 노드별 복구 로직, 재시도 메커니즘 | 중 |
| 5 | **회의 검색/필터** | 제목, 날짜, 상태별 검색 및 정렬 기능 | 중 |
| 6 | **액션 아이템 관리** | 상태 변경, 담당자 변경, 완료 처리 UI | 중 |
| 7 | **TypeScript strict 모드** | `any` 타입 제거, strict 컴파일 옵션 적용 | 중 |
| 8 | **API 타입 자동 변환** | snake_case ↔ camelCase 자동 변환 라이브러리 | 소 |

#### 상세: 회의 검색/필터

```typescript
// frontend/lib/api.ts
interface MeetingSearchParams {
  query?: string;          // 제목 검색
  status?: MeetingStatus;  // 상태 필터
  dateFrom?: string;       // 시작 날짜
  dateTo?: string;         // 종료 날짜
  sortBy?: 'created_at' | 'meeting_date' | 'title';
  sortOrder?: 'asc' | 'desc';
}
```

```python
# backend/app/api/v1/meetings.py
@router.get("/meetings")
async def list_meetings(
    query: Optional[str] = None,
    status: Optional[MeetingStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    ...
)
```

---

### 🟡 P2 - 중간 (2차 릴리즈)

| # | 항목 | 설명 | 예상 작업량 |
|---|------|------|------------|
| 9 | **대시보드 UI** | 메트릭 시각화, 차트, 통계 요약 | 대 |
| 10 | **알림 시스템** | 리뷰 요청 시 이메일/인앱 알림 | 중 |
| 11 | **팀/조직 기능** | 멀티 유저, 팀 워크스페이스, 권한 관리 | 대 |
| 12 | **회의 태그/카테고리** | 회의 분류 및 그룹화 | 소 |
| 13 | **내보내기 기능** | PDF, Markdown, Notion 내보내기 | 중 |

#### 상세: 대시보드 UI

```
frontend/app/dashboard/page.tsx

섹션:
1. 요약 카드
   - 총 회의 수
   - 이번 주 처리된 회의
   - 검토 대기 중
   - 평균 처리 시간

2. 차트
   - 일별 회의 처리량 (7일)
   - 상태별 분포 (파이 차트)
   - 액션 아이템 완료율

3. 최근 활동
   - 최근 처리된 회의 목록
   - 검토 대기 중인 회의
```

---

### 🟢 P3 - 낮음 (향후 고려)

| # | 항목 | 설명 | 예상 작업량 |
|---|------|------|------------|
| 14 | **접근성(a11y)** | 키보드 네비게이션, 스크린 리더 지원 | 중 |
| 15 | **다국어 지원** | i18n 프레임워크 적용 (한/영) | 중 |
| 16 | **다크/라이트 테마** | 시스템 설정 연동, 수동 전환 | 소 |
| 17 | **모바일 반응형** | 태블릿/모바일 레이아웃 최적화 | 중 |
| 18 | **오프라인 지원** | PWA, 오프라인 캐싱 | 대 |

---

## Phase 2 기능 (설계 문서 기준)

| # | 기능 | 설명 | 우선순위 |
|---|------|------|---------|
| 19 | **실시간 녹음** | 브라우저에서 직접 녹음, WebRTC | P2 |
| 20 | **Jira 실제 연동** | MCP 서버 실제 연결, OAuth 인증 | P2 |
| 21 | **Google Calendar 연동** | 일정 자동 생성, OAuth 인증 | P2 |
| 22 | **Slack 연동** | 알림 전송, 채널 연동 | P2 |
| 23 | **Notion 연동** | 회의록 자동 생성 | P3 |
| 24 | **모바일 앱** | Flutter 기반 iOS/Android 앱 | P3 |

---

## 기술 부채

### 코드 품질

| 항목 | 현재 상태 | 개선 방향 |
|------|----------|----------|
| TypeScript strict | 일부 `any` 사용 | `strict: true` 적용 |
| 에러 타입 | 제네릭 Error | 커스텀 에러 클래스 |
| API 응답 타입 | 수동 변환 | `humps` 라이브러리 적용 |
| 로깅 | 기본 console | 구조화된 로거 (winston/pino) |

### 인프라

| 항목 | 현재 상태 | 개선 방향 |
|------|----------|----------|
| CI/CD | 없음 | GitHub Actions 추가 |
| 모니터링 | 기본 메트릭 API | Prometheus + Grafana |
| 로그 수집 | 로컬 stdout | ELK Stack / CloudWatch |
| 컨테이너 | docker-compose | Kubernetes (선택적) |

### 보안

| 항목 | 현재 상태 | 개선 방향 |
|------|----------|----------|
| 인증 | JWT 기본 구현 | Refresh Token 로테이션 |
| 권한 | 단일 사용자 | RBAC (역할 기반 접근 제어) |
| 입력 검증 | Pydantic 기본 | 추가 sanitization |
| Rate Limiting | 없음 | Redis 기반 rate limiter |

---

## 작업 우선순위 매트릭스

```
                    영향도 높음
                        │
         P0 테스트      │      P1 검색/필터
         P0 보안       │      P2 대시보드
                        │
    ────────────────────┼────────────────────
                        │
         P3 접근성      │      P1 에러 핸들링
         P3 다국어      │      P2 알림
                        │
                    영향도 낮음

    노력 많음 ◄─────────┼─────────► 노력 적음
```

---

## 다음 단계 권장

### 즉시 진행 (이번 스프린트)
1. ✅ MVP 기능 완료
2. 🔲 P0 테스트 코드 작성
3. 🔲 P0 환경 변수 검증

### 다음 스프린트
1. 🔲 P1 회의 검색/필터
2. 🔲 P1 에러 핸들링 강화
3. 🔲 P1 TypeScript strict 모드

### 향후 계획
1. 🔲 P2 대시보드 UI
2. 🔲 P2 알림 시스템
3. 🔲 Phase 2 외부 연동

---

## 참고 문서

- [MOA 설계 문서](./MOA_CODE_DESIGN.md)
- [LangGraph 아키텍처](./LANGGRAPH_ARCHITECTURE.md)
- [API 가이드](./API_GUIDE_V2.md)
- [변경 이력](../CHANGELOG.md)

---

> 이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.
> 마지막 업데이트: 2026-01-10
