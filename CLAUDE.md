# CLAUDE.md - MOA 프로젝트 컨텍스트

> 이 파일은 Claude Code가 프로젝트의 맥락을 이해하고 일관된 코드를 생성하도록 돕습니다.

## 프로젝트 개요

**MOA (Minutes Of Action)** - 회의를 실행으로 전환하는 AI 회의 액션 매니저

### 핵심 기능
1. 오디오 파일 업로드 및 관리
2. 음성-텍스트 변환 (STT) with 화자 분리
3. AI 기반 회의 요약 생성
4. 액션 아이템 자동 추출
5. Human-in-the-Loop 검토 프로세스

## 기술 스택

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, SQLAlchemy |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis |
| Storage | MinIO (S3 compatible) |
| AI Pipeline | LangGraph, Claude API |
| STT | Naver Clova Speech API |

## 코딩 컨벤션

### Python (Backend & AI Pipeline)

```python
# 변수명: snake_case
meeting_id = "123"
audio_file_path = "/path/to/file"

# 클래스명: PascalCase
class MeetingService:
    pass

# 상수: UPPER_SNAKE_CASE
MAX_AUDIO_SIZE_MB = 100
DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024

# 함수/메서드: snake_case, 동사로 시작
def get_meeting_by_id(meeting_id: str) -> Meeting:
    pass

async def process_audio_file(file_path: str) -> TranscriptResult:
    pass

# Type hints 필수
def create_action_item(
    content: str,
    assignee: Optional[str] = None,
    due_date: Optional[date] = None
) -> ActionItem:
    pass
```

### TypeScript (Frontend)

```typescript
// 변수명: camelCase
const meetingId = "123";
const audioFileUrl = "/api/upload";

// 인터페이스/타입: PascalCase
interface Meeting {
  id: string;
  title: string;
  status: MeetingStatus;
}

type MeetingStatus = "uploaded" | "processing" | "completed";

// 컴포넌트: PascalCase
const MeetingCard: React.FC<MeetingCardProps> = ({ meeting }) => {
  return <div>{meeting.title}</div>;
};

// 훅: use 접두사
const useMeetings = () => {
  // ...
};

// 유틸 함수: camelCase
const formatDuration = (seconds: number): string => {
  // ...
};
```

## 날짜/시간 규칙

- **모든 날짜**: ISO 8601 형식 (`YYYY-MM-DD`)
- **모든 시간**: UTC 기준 ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`)
- **타임존 표시**: 필요시 클라이언트에서 로컬 변환

```python
# Python
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# TypeScript
const now = new Date().toISOString();
```

## API 응답 형식

### 성공 응답
```json
{
  "data": { ... },
  "message": "Success"
}
```

### 목록 응답 (페이지네이션)
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### 에러 응답
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "field": "optional_field_name"
}
```

## 디렉토리 구조 규칙

### Backend
- `api/` - API 라우터 (엔드포인트 정의만)
- `services/` - 비즈니스 로직
- `models/` - SQLAlchemy ORM 모델
- `schemas/` - Pydantic 스키마
- `core/` - 설정, 보안, DB 연결

### Frontend
- `app/` - Next.js App Router 페이지
- `components/ui/` - 재사용 가능한 기본 컴포넌트
- `components/{feature}/` - 기능별 컴포넌트
- `lib/` - 유틸리티, API 클라이언트
- `types/` - TypeScript 타입 정의

### AI Pipeline
- `nodes/` - LangGraph 노드
- `prompts/` - LLM 프롬프트 템플릿
- `integrations/` - 외부 서비스 연동

## 주요 명령어

```bash
# 개발 환경 시작
docker-compose up -d

# 백엔드만 실행
cd backend && uvicorn app.main:app --reload

# 프론트엔드만 실행
cd frontend && npm run dev

# DB 마이그레이션
cd backend && alembic upgrade head

# 테스트 실행
cd backend && pytest
cd frontend && npm test
```

## Git 컨벤션

### 브랜치 네이밍
- `feature/기능명` - 새 기능
- `fix/이슈명` - 버그 수정
- `refactor/대상` - 리팩토링
- `docs/문서명` - 문서 작업

### 커밋 메시지
```
type(scope): 간단한 설명

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

예시:
```
feat(meeting): 회의 요약 API 추가
fix(upload): 대용량 파일 업로드 타임아웃 수정
docs(readme): 설치 가이드 업데이트
```

## 한국어 처리 주의사항

1. **STT 결과**: Naver Clova가 자동으로 띄어쓰기 교정
2. **검색**: PostgreSQL의 `pg_trgm` 확장 사용 권장
3. **정렬**: 유니코드 정렬 (`COLLATE "ko_KR.UTF-8"`)
4. **형태소 분석**: 필요시 Mecab-ko 연동

## 환경 변수

필수 환경 변수 (.env):
```
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379
CLOVA_API_KEY=xxx
CLAUDE_API_KEY=xxx
JWT_SECRET_KEY=xxx
```

## 참고 문서

- `docs/MOA_CODE_DESIGN.md` - 상세 설계 문서
- `docs/API.md` - API 명세 (자동 생성: /docs)
- `docs/DEPLOYMENT.md` - 배포 가이드

---

> 이 파일을 수정할 때는 팀원들과 공유하세요.
