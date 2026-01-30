# MOA 개선사항 로드맵

> **Version**: 2.2.0
> **Last Updated**: 2026-01-30
> **Status**: P0-P2 개선 완료

---

## 현재 상태 요약

### ✅ 완료된 기능 (MVP + 개선)

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
| 테스트 코드 | `backend/tests/`, `ai_pipeline/tests/`, `frontend/__tests__/` | ✅ |
| 환경 변수 검증 | `backend/app/config.py` | ✅ |
| 보안 미들웨어 | `backend/app/middleware/security.py`, `rate_limit.py` | ✅ |
| 에러 핸들링 | `ai_pipeline/pipeline/errors.py`, `retry.py` | ✅ |
| 회의 검색/필터 | `backend/app/api/v1/meetings.py` | ✅ |
| TypeScript strict | `frontend/tsconfig.json` | ✅ |
| API 타입 변환 | `frontend/lib/apiTransform.ts` | ✅ |
| 대시보드 UI | `frontend/components/dashboard/*` | ✅ |
| 알림 시스템 | `backend/app/api/v1/notifications.py` | ✅ |
| 회의 태그 | `backend/app/api/v1/meetings.py` (tags) | ✅ |
| 내보내기 | `backend/app/api/v1/export.py` | ✅ |
| **팀/조직 기능** | `backend/app/api/v1/teams.py`, `models/team.py` | ✅ NEW |

---

## 개선사항 목록

### ✅ P0 - 긴급 (완료)

| # | 항목 | 설명 | 상태 |
|---|------|------|------|
| 1 | **테스트 코드 작성** | 백엔드, AI 파이프라인, 프론트엔드 테스트 | ✅ 완료 |
| 2 | **환경 변수 검증** | Pydantic Settings로 시작 시 검증 | ✅ 완료 |
| 3 | **보안 검토** | JWT, CORS, Rate Limiting, Security Headers | ✅ 완료 |

#### 완료 상세: 테스트 코드

```
backend/tests/
├── test_api/
│   ├── test_auth.py        ✅
│   ├── test_meetings.py    ✅
│   ├── test_review.py      ✅
│   ├── test_websocket.py   ✅
│   ├── test_metrics.py     ✅
│   └── test_upload.py      ✅ NEW
├── test_services/
│   └── test_slack_service.py ✅ NEW
└── conftest.py

ai_pipeline/tests/
├── test_mcp_client.py      ✅
├── test_claude_llm.py      ✅
├── test_state.py           ✅
├── test_prompts.py         ✅
├── test_graph.py           ✅ NEW
└── conftest.py

frontend/__tests__/
├── lib/
│   ├── apiTransform.test.ts ✅ NEW
│   └── utils.test.ts        ✅ NEW
└── components/
    └── ThemeToggle.test.tsx ✅ NEW
```

---

### ✅ P1 - 높음 (완료)

| # | 항목 | 설명 | 상태 |
|---|------|------|------|
| 4 | **에러 핸들링 강화** | 노드별 복구 로직, 재시도 메커니즘 | ✅ 완료 |
| 5 | **회의 검색/필터** | 제목, 날짜, 상태, 태그별 검색 | ✅ 완료 |
| 6 | **액션 아이템 관리** | ActionItemManager UI | ✅ 완료 |
| 7 | **TypeScript strict** | strict: true, noUnusedLocals 등 | ✅ 완료 |
| 8 | **API 타입 자동 변환** | apiTransform.ts 라이브러리 | ✅ 완료 |

---

### ✅ P2 - 중간 (완료)

| # | 항목 | 설명 | 상태 |
|---|------|------|------|
| 9 | **대시보드 UI** | StatsCard, DailyChart, StatusPieChart | ✅ 완료 |
| 10 | **알림 시스템** | 인앱 알림, NotificationBell | ✅ 완료 |
| 11 | **팀/조직 기능** | Team 모델, API, 초대 시스템 | ✅ 완료 |
| 12 | **회의 태그** | meetings.py tags 기능 | ✅ 완료 |
| 13 | **내보내기** | Markdown, HTML, JSON 내보내기 | ✅ 완료 |

#### 완료 상세: 팀/조직 기능

```
backend/app/models/team.py
├── Team              # 팀 모델
├── TeamMember        # 팀 멤버십 (역할 포함)
├── TeamInvitation    # 초대 시스템
└── TeamRole          # owner, admin, member, viewer

backend/app/api/v1/teams.py
├── POST   /teams                    # 팀 생성
├── GET    /teams                    # 내 팀 목록
├── GET    /teams/{id}               # 팀 상세 (멤버 포함)
├── PATCH  /teams/{id}               # 팀 수정
├── DELETE /teams/{id}               # 팀 삭제
├── POST   /teams/{id}/members       # 멤버 추가
├── PATCH  /teams/{id}/members/{uid} # 역할 변경
├── DELETE /teams/{id}/members/{uid} # 멤버 제거
├── POST   /teams/{id}/invitations   # 초대 생성
├── GET    /teams/invitations/pending # 내 초대 목록
└── POST   /teams/invitations/accept  # 초대 수락

frontend/types/team.ts              # 타입 정의
frontend/lib/api.ts (teamsApi)      # API 클라이언트
```

---

### 🟢 P3 - 낮음 (향후 고려)

| # | 항목 | 설명 | 예상 작업량 |
|---|------|------|------------|
| 14 | **접근성(a11y)** | 키보드 네비게이션, 스크린 리더 (일부 완료) | 중 |
| 15 | **다국어 지원** | i18n 프레임워크 적용 (완료 - ko/en) | ✅ 완료 |
| 16 | **다크/라이트 테마** | ThemeToggle, ThemeProvider | ✅ 완료 |
| 17 | **모바일 반응형** | MobileNav, 반응형 레이아웃 (일부 완료) | 중 |
| 18 | **오프라인 지원** | ServiceWorkerRegister (기본 구현) | 대 |

---

## Phase 2 기능 (설계 문서 기준)

| # | 기능 | 설명 | 우선순위 |
|---|------|------|---------|
| 19 | **실시간 녹음** | AudioRecorder 컴포넌트 (기본 구현) | P2 |
| 20 | **Jira 연동** | MCP 클라이언트 준비됨, OAuth 필요 | P2 |
| 21 | **Google Calendar 연동** | google_calendar_service.py (기본 구현) | P2 |
| 22 | **Slack 연동** | slack_service.py (완료) | ✅ 완료 |
| 23 | **Notion 연동** | 미구현 | P3 |
| 24 | **모바일 앱** | 미구현 | P3 |

---

## 기술 부채

### 코드 품질

| 항목 | 현재 상태 | 개선 방향 |
|------|----------|----------|
| TypeScript strict | ✅ 적용됨 | - |
| 에러 타입 | ✅ 커스텀 에러 클래스 | - |
| API 응답 타입 | ✅ apiTransform 적용 | - |
| 로깅 | 기본 logger | 구조화된 로거 고려 |

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
| 인증 | ✅ JWT + Refresh Token | - |
| 권한 | ✅ 팀 기반 RBAC | - |
| 입력 검증 | ✅ Pydantic + sanitization | - |
| Rate Limiting | ✅ 메모리 기반 구현 | Redis 기반 고려 |
| Security Headers | ✅ 완료 | - |

---

## 다음 단계 권장

### 완료된 작업 ✅
1. ✅ MVP 기능 완료
2. ✅ P0 테스트 코드 작성
3. ✅ P0 환경 변수 검증
4. ✅ P0 보안 검토
5. ✅ P1 회의 검색/필터
6. ✅ P1 에러 핸들링 강화
7. ✅ P1 TypeScript strict 모드
8. ✅ P2 대시보드 UI
9. ✅ P2 알림 시스템
10. ✅ P2 팀/조직 기능

### 다음 스프린트
1. 🔲 CI/CD 파이프라인 구축 (GitHub Actions)
2. 🔲 팀 UI 페이지 구현 (frontend/app/teams/*)
3. 🔲 E2E 테스트 추가 (Playwright/Cypress)

### 향후 계획
1. 🔲 Phase 2 외부 연동 완성 (Jira, Google Calendar)
2. 🔲 성능 최적화 및 모니터링 강화
3. 🔲 모바일 앱 고려

---

## 참고 문서

- [MOA 설계 문서](./MOA_CODE_DESIGN.md)
- [LangGraph 아키텍처](./LANGGRAPH_ARCHITECTURE.md)
- [API 가이드](./API_GUIDE_V2.md)
- [변경 이력](../CHANGELOG.md)

---

> 이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.
> 마지막 업데이트: 2026-01-30
