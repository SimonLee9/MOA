# MOA (Minutes Of Action) - 코드 설계 문서

> **Version**: 1.0.0  
> **Last Updated**: 2025-01-10  
> **Focus**: 회의 자동 요약 (Meeting Auto-Summary)

---

## 1. 프로젝트 개요

### 1.1 제품 비전
MOA는 단순한 회의록 도구가 아닌, **"회의를 실행으로 전환하는 시스템"**입니다.

```
회의 녹음 → 텍스트 변환 → AI 요약 → 액션 아이템 추출 → 실행 관리
```

### 1.2 MVP 범위 (Phase 1: 회의 자동 요약)

| 기능 | 포함 여부 | 우선순위 |
|------|----------|---------|
| 오디오 파일 업로드 | ✅ | P0 |
| Speech-to-Text (STT) | ✅ | P0 |
| 화자 분리 (Diarization) | ✅ | P0 |
| AI 기반 요약 생성 | ✅ | P0 |
| 액션 아이템 추출 | ✅ | P0 |
| 웹 대시보드 | ✅ | P0 |
| 사용자 인증 | ✅ | P1 |
| 실시간 녹음 | ❌ | Phase 2 |
| 외부 서비스 연동 (Jira/Notion) | ❌ | Phase 3 |

---

## 2. 기술 스택 (권장)

### 2.1 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Next.js 14 (App Router)                     │   │
│  │         React + TypeScript + Tailwind CSS                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              FastAPI (Python 3.11+)                      │   │
│  │         Async/Await + Pydantic + SQLAlchemy              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Redis       │  │   MinIO/S3      │
│   (Database)    │  │ (Queue/Cache)   │  │ (File Storage)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI PIPELINE LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LangGraph + Claude API                      │   │
│  │      Naver Clova STT / OpenAI Whisper (Fallback)        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 기술 선정 근거

#### Frontend: **Next.js 14 + TypeScript**
| 선정 이유 |
|-----------|
| App Router로 서버 컴포넌트 지원 → 빠른 초기 로딩 |
| TypeScript로 백엔드 스키마와 타입 동기화 용이 |
| Vercel 배포 시 자동 최적화 |
| React 생태계의 풍부한 UI 라이브러리 |

#### Backend: **FastAPI (Python)**
| 선정 이유 |
|-----------|
| 비동기 처리 기본 지원 → 대용량 오디오 업로드에 적합 |
| Pydantic으로 자동 검증 및 OpenAPI 문서 생성 |
| Python ML/AI 생태계와 자연스러운 통합 |
| LangGraph, LangChain과 동일 언어로 일관성 유지 |

#### AI/LLM: **LangGraph + Claude API**
| 선정 이유 |
|-----------|
| 상태 기반 워크플로우로 복잡한 회의 처리 파이프라인 구현 |
| Human-in-the-Loop 지원 → 사용자 검토/승인 프로세스 |
| 자가 검증(Critique) 노드로 품질 보장 |
| Claude의 한국어 이해력 우수 |

#### STT: **Naver Clova Speech (Primary)**
| 선정 이유 |
|-----------|
| 한국어 최적화 (조사, 어미, 띄어쓰기 정확도) |
| 화자 분리 기능 내장 → 추가 모델 불필요 |
| 키워드 부스팅으로 전문 용어 인식률 향상 |
| 개발 복잡도 낮음 (통합 API) |

---

## 3. 프로젝트 구조

```
MOA/
├── README.md
├── CLAUDE.md                    # Claude Code 컨텍스트 파일
├── docker-compose.yml
├── .env.example
│
├── frontend/                    # Next.js 프론트엔드
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   │
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # 랜딩/대시보드
│   │   ├── globals.css
│   │   │
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   │
│   │   ├── meetings/
│   │   │   ├── page.tsx         # 회의 목록
│   │   │   ├── [id]/page.tsx    # 회의 상세
│   │   │   └── upload/page.tsx  # 오디오 업로드
│   │   │
│   │   └── api/                 # API Routes (BFF)
│   │       └── upload/route.ts
│   │
│   ├── components/
│   │   ├── ui/                  # 공통 UI 컴포넌트
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Modal.tsx
│   │   │
│   │   ├── meeting/
│   │   │   ├── MeetingCard.tsx
│   │   │   ├── MeetingSummary.tsx
│   │   │   ├── ActionItemList.tsx
│   │   │   ├── TranscriptView.tsx
│   │   │   └── AudioUploader.tsx
│   │   │
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   │
│   ├── lib/
│   │   ├── api.ts               # API 클라이언트
│   │   ├── auth.ts              # 인증 유틸
│   │   └── utils.ts
│   │
│   └── types/
│       ├── meeting.ts
│       └── user.ts
│
├── backend/                     # FastAPI 백엔드
│   ├── pyproject.toml
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── config.py            # 설정 관리
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # 의존성 주입
│   │   │   │
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py    # API 라우터 통합
│   │   │       ├── meetings.py  # 회의 엔드포인트
│   │   │       ├── upload.py    # 파일 업로드
│   │   │       └── auth.py      # 인증
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── meeting.py       # Meeting ORM 모델
│   │   │   ├── user.py
│   │   │   └── action_item.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── meeting.py       # Pydantic 스키마
│   │   │   ├── user.py
│   │   │   └── action_item.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── meeting_service.py
│   │   │   ├── storage_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # JWT, 암호화
│   │   │   └── database.py      # DB 연결
│   │   │
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── celery_app.py    # Celery 워커
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_meetings.py
│
├── ai_pipeline/                 # LangGraph AI 파이프라인
│   ├── pyproject.toml
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph 메인 그래프
│   │   ├── state.py             # 상태 스키마
│   │   │
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── stt_node.py      # STT 처리 노드
│   │   │   ├── summarizer_node.py
│   │   │   ├── action_extractor_node.py
│   │   │   ├── critique_node.py
│   │   │   └── human_review_node.py
│   │   │
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── summarize.py
│   │   │   ├── extract_actions.py
│   │   │   └── critique.py
│   │   │
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── clova_stt.py     # Naver Clova 연동
│   │       ├── whisper_stt.py   # Whisper 연동 (Fallback)
│   │       └── claude_llm.py    # Claude API 연동
│   │
│   └── tests/
│       └── test_pipeline.py
│
└── infra/                       # 인프라 설정
    ├── docker/
    │   ├── Dockerfile.frontend
    │   ├── Dockerfile.backend
    │   └── Dockerfile.ai
    │
    └── k8s/                     # (선택) Kubernetes 설정
        ├── deployment.yaml
        └── service.yaml
```

---

## 4. 데이터 모델 설계

### 4.1 ERD (Entity Relationship Diagram)

```
┌─────────────────────────────────────────────────────────────────┐
│                            users                                │
├─────────────────────────────────────────────────────────────────┤
│ id              UUID         PK                                 │
│ email           VARCHAR(255) UNIQUE NOT NULL                    │
│ hashed_password VARCHAR(255) NOT NULL                           │
│ name            VARCHAR(100) NOT NULL                           │
│ created_at      TIMESTAMP    DEFAULT NOW()                      │
│ updated_at      TIMESTAMP    DEFAULT NOW()                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          meetings                               │
├─────────────────────────────────────────────────────────────────┤
│ id              UUID         PK                                 │
│ user_id         UUID         FK → users.id                      │
│ title           VARCHAR(255) NOT NULL                           │
│ audio_file_url  VARCHAR(500)                                    │
│ audio_duration  INTEGER      (seconds)                          │
│ status          ENUM         (uploaded, processing, completed,  │
│                               failed, review_pending)           │
│ meeting_date    DATE                                            │
│ created_at      TIMESTAMP    DEFAULT NOW()                      │
│ updated_at      TIMESTAMP    DEFAULT NOW()                      │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │ 1:1               │ 1:N               │ 1:N
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ meeting_summary │  │  transcripts    │  │    action_items     │
├─────────────────┤  ├─────────────────┤  ├─────────────────────┤
│ id         UUID │  │ id         UUID │  │ id             UUID │
│ meeting_id UUID │  │ meeting_id UUID │  │ meeting_id     UUID │
│ summary    TEXT │  │ speaker    STR  │  │ content        TEXT │
│ key_points JSON │  │ text       TEXT │  │ assignee       STR  │
│ decisions  JSON │  │ start_time FLOAT│  │ due_date       DATE │
│ created_at TS   │  │ end_time   FLOAT│  │ status         ENUM │
│ updated_at TS   │  │ confidence FLOAT│  │ priority       ENUM │
└─────────────────┘  └─────────────────┘  │ created_at     TS   │
                                          └─────────────────────┘
```

### 4.2 Pydantic 스키마

```python
# backend/app/schemas/meeting.py

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from uuid import UUID


class MeetingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_PENDING = "review_pending"


class ActionItemStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActionItemPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# --- Transcript ---
class TranscriptSegment(BaseModel):
    speaker: str = Field(..., description="화자 이름 또는 ID")
    text: str = Field(..., description="발화 내용")
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    confidence: Optional[float] = Field(None, ge=0, le=1)


# --- Action Item ---
class ActionItemBase(BaseModel):
    content: str = Field(..., description="할 일 내용")
    assignee: Optional[str] = Field(None, description="담당자")
    due_date: Optional[date] = Field(None, description="마감일")
    priority: ActionItemPriority = ActionItemPriority.MEDIUM


class ActionItemCreate(ActionItemBase):
    pass


class ActionItemResponse(ActionItemBase):
    id: UUID
    meeting_id: UUID
    status: ActionItemStatus
    created_at: datetime

    class Config:
        from_attributes = True


# --- Meeting Summary ---
class MeetingSummaryResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    summary: str = Field(..., description="전체 요약")
    key_points: List[str] = Field(default_factory=list, description="핵심 포인트")
    decisions: List[str] = Field(default_factory=list, description="결정 사항")
    created_at: datetime


# --- Meeting ---
class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    meeting_date: Optional[date] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingResponse(MeetingBase):
    id: UUID
    user_id: UUID
    status: MeetingStatus
    audio_file_url: Optional[str]
    audio_duration: Optional[int]
    created_at: datetime
    updated_at: datetime

    # Relations (optional, for detail view)
    summary: Optional[MeetingSummaryResponse] = None
    transcripts: Optional[List[TranscriptSegment]] = None
    action_items: Optional[List[ActionItemResponse]] = None

    class Config:
        from_attributes = True
```

---

## 5. API 설계

### 5.1 RESTful Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **Meetings** ||||
| POST | `/api/v1/meetings` | 새 회의 생성 | ✅ |
| GET | `/api/v1/meetings` | 회의 목록 조회 | ✅ |
| GET | `/api/v1/meetings/{id}` | 회의 상세 조회 | ✅ |
| DELETE | `/api/v1/meetings/{id}` | 회의 삭제 | ✅ |
| **Upload** ||||
| POST | `/api/v1/meetings/{id}/upload` | 오디오 파일 업로드 | ✅ |
| GET | `/api/v1/meetings/{id}/upload/status` | 업로드 상태 조회 | ✅ |
| **Processing** ||||
| POST | `/api/v1/meetings/{id}/process` | AI 처리 시작 | ✅ |
| GET | `/api/v1/meetings/{id}/process/status` | 처리 상태 조회 | ✅ |
| **Results** ||||
| GET | `/api/v1/meetings/{id}/transcript` | 트랜스크립트 조회 | ✅ |
| GET | `/api/v1/meetings/{id}/summary` | 요약 조회 | ✅ |
| PUT | `/api/v1/meetings/{id}/summary` | 요약 수정 (Human Review) | ✅ |
| GET | `/api/v1/meetings/{id}/actions` | 액션 아이템 조회 | ✅ |
| PUT | `/api/v1/meetings/{id}/actions/{action_id}` | 액션 아이템 수정 | ✅ |
| **Auth** ||||
| POST | `/api/v1/auth/register` | 회원가입 | ❌ |
| POST | `/api/v1/auth/login` | 로그인 | ❌ |
| POST | `/api/v1/auth/refresh` | 토큰 갱신 | ✅ |

### 5.2 API Request/Response 예시

#### 5.2.1 회의 생성 및 오디오 업로드

```http
POST /api/v1/meetings
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "2025년 1분기 기획 회의",
  "meeting_date": "2025-01-10"
}
```

```json
// Response: 201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "...",
  "title": "2025년 1분기 기획 회의",
  "status": "uploaded",
  "meeting_date": "2025-01-10",
  "created_at": "2025-01-10T14:30:00Z"
}
```

#### 5.2.2 오디오 업로드 (Multipart)

```http
POST /api/v1/meetings/550e8400.../upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

audio_file: <binary data>
```

```json
// Response: 202 Accepted
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_file_url": "https://storage.moa.ai/meetings/550e8400.../audio.m4a",
  "audio_duration": 3600,
  "status": "uploaded",
  "message": "Upload successful. Ready for processing."
}
```

#### 5.2.3 AI 처리 완료 후 결과

```json
// GET /api/v1/meetings/550e8400.../summary
{
  "id": "...",
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "이번 회의에서는 2025년 1분기 마케팅 전략과 신규 제품 출시 일정에 대해 논의했습니다. 김 부장님이 디지털 마케팅 예산 20% 증액을 제안했으며, 이에 대해 전원 합의하였습니다.",
  "key_points": [
    "마케팅 예산 20% 증액 합의",
    "신제품 출시일 3월 15일 확정",
    "파트너사 미팅 다음 주 진행 예정"
  ],
  "decisions": [
    "디지털 마케팅 예산을 기존 대비 20% 증액한다",
    "신제품 베타 테스트를 2월 말까지 완료한다"
  ],
  "created_at": "2025-01-10T15:00:00Z"
}
```

```json
// GET /api/v1/meetings/550e8400.../actions
{
  "items": [
    {
      "id": "...",
      "content": "파트너사 미팅 일정 잡기",
      "assignee": "박 대리",
      "due_date": "2025-01-17",
      "priority": "high",
      "status": "pending"
    },
    {
      "id": "...",
      "content": "마케팅 예산 증액 품의서 작성",
      "assignee": "김 부장",
      "due_date": "2025-01-15",
      "priority": "urgent",
      "status": "pending"
    }
  ]
}
```

---

## 6. AI 파이프라인 설계 (LangGraph)

### 6.1 상태 스키마

```python
# ai_pipeline/pipeline/state.py

from typing import TypedDict, List, Optional, Literal
from datetime import datetime


class TranscriptSegment(TypedDict):
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float]


class ActionItem(TypedDict):
    content: str
    assignee: Optional[str]
    due_date: Optional[str]
    priority: Literal["low", "medium", "high", "urgent"]


class MeetingAgentState(TypedDict):
    # Input
    meeting_id: str
    audio_file_path: str
    
    # STT Output
    transcript_segments: List[TranscriptSegment]
    raw_text: str
    
    # LLM Outputs
    draft_summary: str
    key_points: List[str]
    decisions: List[str]
    action_items: List[ActionItem]
    
    # Quality Control
    critique: str
    critique_passed: bool
    retry_count: int
    
    # Human-in-the-Loop
    requires_human_review: bool
    human_feedback: Optional[str]
    
    # Final
    final_output: Optional[dict]
    status: Literal["processing", "review_pending", "completed", "failed"]
    error_message: Optional[str]
```

### 6.2 그래프 구조

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  STT Node   │ ◄── Naver Clova / Whisper
                    │ (음성→텍스트) │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Summarizer  │ ◄── Claude API
                    │   Node      │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Action     │ ◄── Claude API
                    │ Extractor   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Critique   │ ◄── 자가 검증
                    │    Node     │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │             │
            (Pass)  ▼             ▼  (Fail, retry < 3)
         ┌─────────────┐   ┌─────────────┐
         │   Human     │   │   Retry     │───┐
         │   Review    │   │             │   │
         └──────┬──────┘   └─────────────┘   │
                │                 ▲          │
                │                 └──────────┘
                │  (Approve)            
                ▼                       
         ┌─────────────┐               
         │    Save     │               
         │    Node     │               
         └──────┬──────┘               
                │
                ▼
         ┌─────────────┐
         │     END     │
         └─────────────┘
```

### 6.3 노드 구현 상세

```python
# ai_pipeline/pipeline/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import MeetingAgentState
from .nodes import (
    stt_node,
    summarizer_node,
    action_extractor_node,
    critique_node,
    human_review_node,
    save_node
)


def create_meeting_graph():
    """회의 처리 LangGraph 생성"""
    
    builder = StateGraph(MeetingAgentState)
    
    # 노드 추가
    builder.add_node("stt", stt_node)
    builder.add_node("summarize", summarizer_node)
    builder.add_node("extract_actions", action_extractor_node)
    builder.add_node("critique", critique_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("save", save_node)
    
    # 엣지 정의
    builder.set_entry_point("stt")
    builder.add_edge("stt", "summarize")
    builder.add_edge("summarize", "extract_actions")
    builder.add_edge("extract_actions", "critique")
    
    # 조건부 엣지: Critique 결과에 따른 분기
    builder.add_conditional_edges(
        "critique",
        lambda state: _route_after_critique(state),
        {
            "pass": "human_review",
            "retry": "summarize",
            "fail": END
        }
    )
    
    builder.add_edge("human_review", "save")
    builder.add_edge("save", END)
    
    # Human-in-the-Loop: human_review 전에 인터럽트
    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["human_review"]
    )
    
    return graph


def _route_after_critique(state: MeetingAgentState) -> str:
    """Critique 결과에 따른 라우팅"""
    if state["critique_passed"]:
        return "pass"
    elif state["retry_count"] < 3:
        return "retry"
    else:
        return "fail"
```

### 6.4 프롬프트 예시

```python
# ai_pipeline/pipeline/prompts/summarize.py

SUMMARY_SYSTEM_PROMPT = """당신은 회의록 전문 작성자입니다. 
주어진 회의 트랜스크립트를 분석하여 구조화된 요약을 작성합니다.

## 작성 원칙
1. 객관적이고 명확한 문장을 사용합니다
2. 화자 정보를 활용하여 "누가 무엇을 말했는지" 명시합니다
3. 결정사항과 합의사항을 강조합니다
4. 불필요한 잡담이나 인사는 제외합니다

## 출력 형식
다음 JSON 형식으로 응답하세요:
```json
{
  "summary": "전체 회의 요약 (2-3 문단)",
  "key_points": ["핵심 포인트 1", "핵심 포인트 2", ...],
  "decisions": ["결정사항 1", "결정사항 2", ...]
}
```
"""

SUMMARY_USER_PROMPT = """다음 회의 트랜스크립트를 요약해주세요:

<transcript>
{transcript}
</transcript>

회의 제목: {meeting_title}
회의 일시: {meeting_date}
"""
```

```python
# ai_pipeline/pipeline/prompts/extract_actions.py

ACTION_SYSTEM_PROMPT = """당신은 회의에서 액션 아이템을 추출하는 전문가입니다.

## 액션 아이템 식별 기준
다음과 같은 표현에서 액션 아이템을 찾습니다:
- "~하겠습니다", "~할게요"
- "~까지 해주세요", "~부탁드립니다"
- "~언제까지", "다음 주까지"
- 명시적인 업무 지시 또는 자발적 약속

## 추출 원칙
1. 담당자가 명확하지 않으면 문맥에서 유추하거나 "미정"으로 표시
2. 마감일이 상대적이면 (예: "다음 주") 절대 날짜로 변환
3. 우선순위는 문맥의 긴급성을 고려하여 판단

## 출력 형식
```json
{
  "action_items": [
    {
      "content": "할 일 내용",
      "assignee": "담당자 이름 또는 미정",
      "due_date": "YYYY-MM-DD 또는 null",
      "priority": "low|medium|high|urgent"
    }
  ]
}
```
"""
```

---

## 7. 프론트엔드 설계

### 7.1 주요 페이지 구성

```
/                       → 대시보드 (최근 회의, 통계)
/meetings               → 회의 목록
/meetings/upload        → 새 회의 업로드
/meetings/[id]          → 회의 상세 (요약, 트랜스크립트, 액션)
/login                  → 로그인
/register               → 회원가입
```

### 7.2 핵심 컴포넌트 인터페이스

```typescript
// frontend/types/meeting.ts

export type MeetingStatus = 
  | "uploaded" 
  | "processing" 
  | "completed" 
  | "failed" 
  | "review_pending";

export type ActionItemStatus = 
  | "pending" 
  | "in_progress" 
  | "completed";

export type ActionItemPriority = 
  | "low" 
  | "medium" 
  | "high" 
  | "urgent";

export interface TranscriptSegment {
  speaker: string;
  text: string;
  startTime: number;
  endTime: number;
  confidence?: number;
}

export interface ActionItem {
  id: string;
  meetingId: string;
  content: string;
  assignee?: string;
  dueDate?: string;
  priority: ActionItemPriority;
  status: ActionItemStatus;
  createdAt: string;
}

export interface MeetingSummary {
  id: string;
  meetingId: string;
  summary: string;
  keyPoints: string[];
  decisions: string[];
  createdAt: string;
}

export interface Meeting {
  id: string;
  userId: string;
  title: string;
  status: MeetingStatus;
  audioFileUrl?: string;
  audioDuration?: number;
  meetingDate?: string;
  createdAt: string;
  updatedAt: string;
  
  // Optional relations
  summary?: MeetingSummary;
  transcripts?: TranscriptSegment[];
  actionItems?: ActionItem[];
}
```

### 7.3 UI/UX 설계 원칙

| 원칙 | 설명 |
|------|------|
| **다크 모드 기본** | 브랜드 톤에 맞는 다크 테마 + 포인트 컬러 (예: #3B82F6) |
| **미니멀 애니메이션** | 과하지 않은 트랜지션, 로딩 인디케이터만 사용 |
| **상태 시각화** | 처리 진행률을 명확히 표시 (Stepper, Progress Bar) |
| **액션 중심** | 요약/트랜스크립트보다 액션 아이템을 먼저 노출 |
| **키보드 친화** | 주요 기능에 단축키 지원 |

---

## 8. 인프라 및 배포

### 8.1 Docker Compose (개발 환경)

```yaml
# docker-compose.yml

version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: ../infra/docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

  backend:
    build:
      context: ./backend
      dockerfile: ../infra/docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://moa:moa@db:5432/moa
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - CLOVA_API_KEY=${CLOVA_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    depends_on:
      - db
      - redis
      - minio
    volumes:
      - ./backend:/app

  ai_worker:
    build:
      context: ./ai_pipeline
      dockerfile: ../infra/docker/Dockerfile.ai
    environment:
      - DATABASE_URL=postgresql://moa:moa@db:5432/moa
      - REDIS_URL=redis://redis:6379
      - CLOVA_API_KEY=${CLOVA_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    depends_on:
      - redis
      - backend

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=moa
      - POSTGRES_PASSWORD=moa
      - POSTGRES_DB=moa
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=moa
      - MINIO_ROOT_PASSWORD=moa12345
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

### 8.2 환경 변수

```bash
# .env.example

# Database
DATABASE_URL=postgresql://moa:moa@localhost:5432/moa

# Redis
REDIS_URL=redis://localhost:6379

# Storage (MinIO / S3)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=moa
MINIO_SECRET_KEY=moa12345
MINIO_BUCKET=moa-audio

# AI Services
CLOVA_API_KEY=your_clova_api_key
CLOVA_API_SECRET=your_clova_secret
CLAUDE_API_KEY=your_claude_api_key

# Auth
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 9. 개발 로드맵

### Phase 1: MVP (4주)

| 주차 | 목표 | 산출물 |
|------|------|--------|
| **1주차** | 프로젝트 셋업 | Docker 환경, DB 스키마, API 스켈레톤 |
| **2주차** | 백엔드 핵심 | 파일 업로드, STT 연동, 기본 CRUD |
| **3주차** | AI 파이프라인 | LangGraph 그래프, 요약/추출 노드 |
| **4주차** | 프론트엔드 | 업로드 UI, 결과 조회, 기본 인증 |

### Phase 2: 고도화 (4주)

- Human-in-the-Loop 완성
- 실시간 처리 상태 (WebSocket)
- 회의 검색 및 필터링
- 팀/조직 기능

### Phase 3: 확장 (TBD)

- 모바일 앱 (Flutter)
- 외부 연동 (Jira, Notion, Slack)
- MOA Insight (회의 패턴 분석)

---

## 10. 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com)
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [Naver Clova Speech API](https://api.ncloud-docs.com/docs/ai-application-service-clovaspeech)
- [Next.js App Router](https://nextjs.org/docs/app)

---

> **문서 작성**: Claude AI  
> **최종 검토 필요**: 기술 스택, 비용 추정, 일정 조정
