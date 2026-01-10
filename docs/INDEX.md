# MOA 문서 인덱스

> **MOA v2.0 Documentation Hub**

---

## 🎯 빠른 시작

처음 시작하시나요? 다음 순서대로 문서를 읽어보세요:

1. **[README.md](../README.md)** - 프로젝트 개요 및 빠른 시작
2. **[MOA_CODE_DESIGN.md](./MOA_CODE_DESIGN.md)** - 전체 시스템 설계
3. **[LANGGRAPH_ARCHITECTURE.md](./LANGGRAPH_ARCHITECTURE.md)** - AI 파이프라인 상세
4. **[API_GUIDE_V2.md](./API_GUIDE_V2.md)** - API 사용법

---

## 📚 문서 목록

### 개요 및 설계

#### [README.md](../README.md)
- **대상**: 모든 사용자
- **내용**:
  - 프로젝트 소개
  - 주요 기능
  - 빠른 시작 가이드
  - 기술 스택
  - 프로젝트 구조

#### [MOA_CODE_DESIGN.md](./MOA_CODE_DESIGN.md)
- **대상**: 개발자, 아키텍트
- **내용**:
  - 제품 비전 및 MVP 범위
  - 기술 스택 선정 근거
  - 데이터 모델 설계 (ERD, Pydantic 스키마)
  - API 설계 (RESTful endpoints)
  - LangGraph v2.0 상태 스키마
  - 그래프 구조 및 노드 구현

### 아키텍처

#### [LANGGRAPH_ARCHITECTURE.md](./LANGGRAPH_ARCHITECTURE.md)
- **대상**: 백엔드 개발자, AI 엔지니어
- **내용**:
  - LangGraph 워크플로우 상세
  - Tus 프로토콜 통합
  - PostgreSQL 체크포인터 설정
  - Human-in-the-Loop 패턴
  - MCP 통합 전략
  - 상태 영속성 및 스케일링
  - 노드별 구현 가이드

### API

#### [API_GUIDE_V2.md](./API_GUIDE_V2.md)
- **대상**: 프론트엔드 개발자, API 사용자
- **내용**:
  - Tus 업로드 API
  - 회의 처리 API
  - Human Review API (HITL)
  - 상태 모니터링
  - 최종 결과 조회
  - 에러 처리
  - 클라이언트 라이브러리

### 변경 이력

#### [CHANGELOG.md](../CHANGELOG.md)
- **대상**: 모든 사용자
- **내용**:
  - v2.0.0 주요 변경사항
  - Breaking changes
  - Migration 가이드
  - 향후 작업

### 참고 자료

#### [서브 에이전트 및 스킬 설정 가이드.txt](./서브 에이전트 및 스킬 설정 가이드.txt)
- **대상**: 아키텍트, 고급 개발자
- **내용**:
  - Claude Code CLI 서브 에이전트 패턴
  - LangGraph 기반 엔터프라이즈 아키텍처
  - MCP (Model Context Protocol) 통합
  - Human-in-the-Loop 구현 패턴
  - Tus 프로토콜 상세

---

## 🔍 주제별 가이드

### 회의 처리 워크플로우 이해하기

1. **업로드**: [API_GUIDE_V2.md § 1. Resumable Upload](./API_GUIDE_V2.md#1-resumable-upload-tus-protocol)
2. **처리 시작**: [API_GUIDE_V2.md § 2. Meeting Processing](./API_GUIDE_V2.md#2-meeting-processing)
3. **상태 관리**: [LANGGRAPH_ARCHITECTURE.md § State Schema](./LANGGRAPH_ARCHITECTURE.md#state-schema)
4. **Human Review**: [API_GUIDE_V2.md § 3. Human Review](./API_GUIDE_V2.md#3-human-review-hitl)
5. **결과 조회**: [API_GUIDE_V2.md § 4. Meeting Results](./API_GUIDE_V2.md#4-meeting-results)

### LangGraph 워크플로우 구현하기

1. **상태 스키마**: [MOA_CODE_DESIGN.md § 6.1](./MOA_CODE_DESIGN.md#61-상태-스키마-enhanced)
2. **그래프 구조**: [MOA_CODE_DESIGN.md § 6.2](./MOA_CODE_DESIGN.md#62-그래프-구조-v20-enhanced-with-dual-retry-loops)
3. **PostgreSQL 체크포인터**: [LANGGRAPH_ARCHITECTURE.md § PostgreSQL Checkpointer](./LANGGRAPH_ARCHITECTURE.md#postgresql-checkpointer)
4. **interrupt() 패턴**: [MOA_CODE_DESIGN.md § 6.3.2](./MOA_CODE_DESIGN.md#632-human-review-node-interrupt-패턴)
5. **노드 구현**: [LANGGRAPH_ARCHITECTURE.md § Node Implementations](./LANGGRAPH_ARCHITECTURE.md#node-implementations)

### Tus 업로드 구현하기

1. **서버 설정**: [LANGGRAPH_ARCHITECTURE.md § Tus Protocol](./LANGGRAPH_ARCHITECTURE.md#architecture-diagram)
2. **클라이언트 사용법**: [API_GUIDE_V2.md § 1.1](./API_GUIDE_V2.md#11-upload-audio-file)
3. **백엔드 통합**: 코드 참조 `backend/app/api/v1/tus_upload.py`

### MCP 통합하기

1. **개요**: [LANGGRAPH_ARCHITECTURE.md § MCP Integration](./LANGGRAPH_ARCHITECTURE.md#mcp-integration-executor-node)
2. **ActionItem 구조**: [MOA_CODE_DESIGN.md § ActionItem](./MOA_CODE_DESIGN.md#61-상태-스키마-enhanced)
3. **Executor 노드**: 코드 참조 `ai_pipeline/pipeline/nodes/executor_node.py`

---

## 🔗 외부 참고 자료

### LangGraph
- [공식 문서](https://docs.langchain.com/oss/python/langgraph/)
- [Human-in-the-Loop 가이드](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Interrupts 문서](https://docs.langchain.com/oss/javascript/langgraph/interrupts)

### Tus Protocol
- [공식 사이트](https://tus.io/)
- [Python 서버](https://github.com/liviaerxin/fastapi-tusd)
- [JavaScript 클라이언트](https://github.com/tus/tus-js-client)

### Model Context Protocol (MCP)
- [공식 문서](https://modelcontextprotocol.io/)
- [Jira MCP Server](https://github.com/CDataSoftware/jira-mcp-server)
- [Google Calendar MCP](https://github.com/nspady/google-calendar-mcp)

### Claude API
- [Anthropic 문서](https://docs.anthropic.com/)
- [LangChain Anthropic](https://python.langchain.com/docs/integrations/providers/anthropic)

### Naver Clova STT
- [API 문서](https://api.ncloud-docs.com/docs/ai-application-service-clovaspeech)

---

## 📊 다이어그램 색인

### 시스템 아키텍처
- [전체 아키텍처](./MOA_CODE_DESIGN.md#21-아키텍처-개요)
- [LangGraph 워크플로우](./LANGGRAPH_ARCHITECTURE.md#architecture-diagram)

### 데이터 모델
- [ERD](./MOA_CODE_DESIGN.md#41-erd-entity-relationship-diagram)
- [상태 스키마](./MOA_CODE_DESIGN.md#61-상태-스키마-enhanced)

### 워크플로우
- [그래프 구조](./MOA_CODE_DESIGN.md#62-그래프-구조-v20-enhanced-with-dual-retry-loops)
- [API 흐름](./API_GUIDE_V2.md#5-workflow-diagram)

---

## 🆕 v2.0 주요 변경사항

### 새로운 기능
- ✅ Tus 프로토콜 기반 재개 가능한 업로드
- ✅ PostgreSQL 체크포인터 (영구 상태 저장)
- ✅ Modern interrupt() 패턴 (HITL)
- ✅ 이중 재시도 메커니즘
- ✅ MCP 통합 준비

### 변경된 파일
- `backend/requirements.txt` - LangGraph, fastapi-tusd 추가
- `ai_pipeline/pipeline/state.py` - ActionItem 구조 개선
- `ai_pipeline/pipeline/graph.py` - interrupt() 패턴 적용

### 새로운 파일
- `backend/app/api/v1/tus_upload.py`
- `backend/app/api/v1/review.py`
- `ai_pipeline/pipeline/checkpointer.py`
- `ai_pipeline/pipeline/nodes/executor_node.py`

**상세 내용**: [CHANGELOG.md](../CHANGELOG.md)

---

## 💡 팁

### 개발 시작 전
1. README 먼저 읽기
2. MOA_CODE_DESIGN 전체 훑어보기
3. 구현할 기능에 해당하는 섹션 깊이 읽기

### 문제 해결
1. CHANGELOG에서 최근 변경사항 확인
2. API_GUIDE에서 에러 처리 섹션 참고
3. GitHub Issues 검색

### 기여하기
1. 문서 수정은 Pull Request로
2. 새로운 기능은 설계 문서 먼저 업데이트
3. API 변경은 API_GUIDE 반드시 업데이트

---

**마지막 업데이트**: 2026-01-10
**문서 버전**: 2.0.0
