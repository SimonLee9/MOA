# MOA (Minutes Of Action)

> **Version**: 2.0.0
> **차세대 AI 에이전트 기반 회의 인텔리전스 플랫폼**

회의를 실행으로 전환하는 시스템. 단순한 회의록 작성을 넘어, AI가 자동으로 요약하고, 액션 아이템을 추출하며, 외부 도구와 연동하여 실행까지 책임집니다.

---

## ✨ 주요 기능

### v2.0 신규 기능 🆕

- **🔄 재개 가능한 업로드** - Tus 프로토콜 기반, 최대 2GB 오디오 파일 지원
- **🧠 지능형 워크플로우** - LangGraph 기반 상태 관리 파이프라인
- **✅ Human-in-the-Loop** - 사용자 검토 및 승인 프로세스
- **🔁 이중 재시도** - AI 자가 검증 + 사용자 피드백 반영
- **💾 영구 상태 저장** - PostgreSQL 체크포인터로 멀티 데이 워크플로우 지원
- **🔌 MCP 통합** - Jira, Google Calendar 등 외부 도구 자동 연동

### 핵심 기능

- **🎙️ STT (Speech-to-Text)** - Naver Clova 기반 한국어 최적화
- **👥 화자 분리** - 누가 무엇을 말했는지 자동 구분
- **📝 AI 요약** - Claude API 기반 회의록 자동 생성
- **✅ 액션 아이템 추출** - 할 일, 담당자, 마감일 자동 파싱
- **🎯 외부 도구 연동** - Jira 티켓 생성, 캘린더 일정 등록

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                         │
│                   React + TypeScript + Tailwind                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Tus Upload   │  │ Review API   │  │ Meeting API  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Processing Pipeline                       │
│                                                                 │
│   STT → Summarizer → ActionExtractor → Critique                │
│          ↑                                ↓                     │
│          └─────(retry)────────────HumanReview                   │
│                                           ↓                     │
│                                         Save                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│   PostgreSQL         Redis            MinIO/S3                  │
│ (State + Data)    (Queue/Cache)    (File Storage)               │
└─────────────────────────────────────────────────────────────────┘
```

**자세한 아키텍처**: [docs/LANGGRAPH_ARCHITECTURE.md](docs/LANGGRAPH_ARCHITECTURE.md)

---

## 🚀 빠른 시작

### 필수 요구사항

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 16+

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-org/MOA.git
cd MOA

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 설정
```

### 2. 서비스 시작 (Docker Compose)

```bash
docker-compose up -d
```

서비스:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **MinIO**: http://localhost:9001

### 3. 개발 환경 설정 (로컬)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

#### AI Pipeline

```bash
cd ai_pipeline
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📖 사용 방법

### 1. 회의 녹음 파일 업로드 (Tus Protocol)

```javascript
import * as tus from "tus-js-client";

const upload = new tus.Upload(audioFile, {
  endpoint: "http://localhost:8000/api/v1/upload/files",
  onSuccess: () => {
    console.log("Upload complete!");
  }
});

upload.start();
```

### 2. AI 처리 시작

```bash
curl -X POST http://localhost:8000/api/v1/upload/meetings/{meeting_id}/process \
  -H "Authorization: Bearer <token>" \
  -d '{"file_id": "abc123"}'
```

### 3. 상태 모니터링

```bash
curl http://localhost:8000/api/v1/upload/meetings/{meeting_id}/status \
  -H "Authorization: Bearer <token>"
```

### 4. 검토 및 승인

```bash
# 검토 데이터 조회
curl http://localhost:8000/api/v1/meetings/{meeting_id}/review \
  -H "Authorization: Bearer <token>"

# 승인
curl -X POST http://localhost:8000/api/v1/meetings/{meeting_id}/review \
  -H "Authorization: Bearer <token>" \
  -d '{"action": "approve"}'
```

### 5. 최종 결과 조회

```bash
curl http://localhost:8000/api/v1/meetings/{meeting_id}/results \
  -H "Authorization: Bearer <token>"
```

**자세한 API 가이드**: [docs/API_GUIDE_V2.md](docs/API_GUIDE_V2.md)

---

## 🛠️ 기술 스택

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **React Query**

### Backend
- **FastAPI** (Python 3.11+)
- **SQLAlchemy** (Async)
- **PostgreSQL**
- **Redis**
- **MinIO/S3**

### AI/ML
- **LangGraph** (Workflow orchestration)
- **Claude API** (Summarization, extraction)
- **Naver Clova STT** (Speech-to-text)
- **MCP** (Model Context Protocol)

### Infrastructure
- **Docker & Docker Compose**
- **Celery** (Background tasks)
- **Tus** (Resumable uploads)

---

## 📁 프로젝트 구조

```
MOA/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/v1/         # API 엔드포인트
│   │   ├── models/         # SQLAlchemy 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   └── services/       # 비즈니스 로직
│   └── requirements.txt
│
├── ai_pipeline/             # LangGraph AI 파이프라인
│   ├── pipeline/
│   │   ├── graph.py        # 워크플로우 정의
│   │   ├── state.py        # 상태 스키마
│   │   ├── nodes/          # 노드 구현
│   │   ├── checkpointer.py # PostgreSQL 체크포인터
│   │   └── prompts/        # LLM 프롬프트
│   └── requirements.txt
│
├── frontend/                # Next.js 프론트엔드
│   ├── app/
│   ├── components/
│   └── package.json
│
├── docs/                    # 문서
│   ├── MOA_CODE_DESIGN.md
│   ├── LANGGRAPH_ARCHITECTURE.md
│   └── API_GUIDE_V2.md
│
├── docker-compose.yml
├── CHANGELOG.md
└── README.md
```

---

## 🔧 환경 변수

```bash
# Database
DATABASE_URL=postgresql+asyncpg://moa:moa@localhost:5432/moa

# Redis
REDIS_URL=redis://localhost:6379

# Storage
UPLOAD_DIR=./meeting_uploads
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=moa
MINIO_SECRET_KEY=moa12345

# AI Services
CLOVA_API_KEY=your_clova_key
CLOVA_API_SECRET=your_clova_secret
CLAUDE_API_KEY=your_claude_key

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📚 문서

- **[설계 문서](docs/MOA_CODE_DESIGN.md)** - 전체 시스템 설계
- **[아키텍처 가이드](docs/LANGGRAPH_ARCHITECTURE.md)** - LangGraph 워크플로우 상세
- **[API 가이드 v2.0](docs/API_GUIDE_V2.md)** - API 엔드포인트 레퍼런스
- **[변경 이력](CHANGELOG.md)** - 버전별 변경사항

---

## 🧪 테스트

```bash
# Backend 테스트
cd backend
pytest

# AI Pipeline 테스트
cd ai_pipeline
pytest
```

---

## 🔍 트러블슈팅

### Docker 환경 실행 시 주의사항

#### 1. 환경 변수 설정
Docker Compose 환경에서는 데이터베이스 호스트를 서비스명으로 지정해야 합니다:

```bash
# .env 파일에서
DATABASE_URL=postgresql+asyncpg://moa:moa_dev_password@db:5432/moa  # localhost가 아닌 db
```

#### 2. bcrypt 초기화 문제 (Known Issue)
현재 `passlib[bcrypt]` 라이브러리의 초기화 과정에서 72바이트 제한 관련 에러가 발생할 수 있습니다.

**증상**:
```
ValueError: password cannot be longer than 72 bytes
```

**임시 해결책**:
- `backend/app/core/security.py`에서 비밀번호를 72바이트로 자동 절단
- 백엔드 Dockerfile에 `build-essential`, `libffi-dev` 추가하여 bcrypt 네이티브 빌드 지원

**향후 개선 예정**:
- passlib 버전 다운그레이드 또는 대체 라이브러리 검토

#### 3. 포트 충돌
프론트엔드가 3000 포트를 사용 중일 경우:

```bash
# 포트 사용 중인 프로세스 확인 (Windows)
netstat -ano | findstr :3000

# 프로세스 종료
taskkill //F //PID <프로세스ID>

# 프론트엔드 재시작
cd frontend && npm run dev
```

#### 4. Docker 빌드 캐시 문제
코드 변경 후 반영이 안 될 경우:

```bash
# 컨테이너 재빌드
docker-compose up -d --build

# 또는 완전히 클린 빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 서비스 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker-compose ps

# 특정 서비스 로그 확인
docker-compose logs -f backend
docker-compose logs -f ai_worker

# 백엔드 헬스체크
curl http://localhost:8000/health
```

---

## 📝 라이선스

MIT License

---

## 🤝 기여

이슈 등록 및 Pull Request를 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 문의

- **Issues**: https://github.com/your-org/MOA/issues
- **Email**: support@moa.ai

---

**Built with ❤️ using Claude Sonnet 4.5**

> Based on "차세대 AI 에이전트 오케스트레이션" architecture guide
