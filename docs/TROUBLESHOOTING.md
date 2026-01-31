# MOA 트러블슈팅 가이드

이 문서는 MOA 프로젝트 실행 시 발생할 수 있는 일반적인 문제와 해결 방법을 정리합니다.

---

## 목차

1. [Docker 환경 문제](#docker-환경-문제)
2. [데이터베이스 연결 문제](#데이터베이스-연결-문제)
3. [인증 관련 문제](#인증-관련-문제)
4. [프론트엔드 문제](#프론트엔드-문제)
5. [백엔드 API 문제](#백엔드-api-문제)
6. [Review API 문제](#review-api-문제)
7. [알려진 이슈](#알려진-이슈)

---

## Docker 환경 문제

### 1. 컨테이너 간 통신 실패

**증상**:
```
Error connecting to redis://localhost:6379
Error 111 connecting to localhost:6379. Connection refused
```

**원인**: Docker Compose 환경에서 `localhost`를 사용하여 다른 컨테이너에 접근 시도

**해결책**:
`.env` 파일에서 호스트를 **Docker 서비스명**으로 변경:

```bash
# ❌ 잘못된 설정
DATABASE_URL=postgresql+asyncpg://moa:password@localhost:5432/moa
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=localhost:9000

# ✅ 올바른 설정 (Docker Compose)
DATABASE_URL=postgresql+asyncpg://moa:password@db:5432/moa
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
```

**설정 후 컨테이너 재시작**:
```bash
docker-compose down
docker-compose up -d
```

---

### 2. 포트 충돌 (Port Already in Use)

**증상**:
```
Error: bind: address already in use
```

**해결책**:

#### Windows:
```powershell
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /F /PID <프로세스ID>
```

#### Linux/Mac:
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :3000
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

#### 또는 docker-compose.yml에서 포트 변경:
```yaml
services:
  frontend:
    ports:
      - "3002:3000"  # 호스트:컨테이너
  backend:
    ports:
      - "8001:8000"
```

---

### 3. Docker 빌드 캐시 문제

**증상**: 코드 변경 후 반영이 안 됨

**해결책**:

```bash
# 방법 1: 강제 재빌드
docker-compose up -d --build

# 방법 2: 완전 초기화 (캐시 제거)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 방법 3: 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
docker-compose up -d
```

---

### 4. 컨테이너 로그 확인

**서비스별 로그 확인**:
```bash
# 백엔드 로그 (실시간)
docker-compose logs -f backend

# AI Worker 로그
docker-compose logs -f ai_worker

# 프론트엔드 로그
docker-compose logs -f frontend

# 최근 100줄만
docker logs moa-backend --tail 100

# 전체 컨테이너 상태
docker-compose ps
```

---

## 데이터베이스 연결 문제

### 1. PostgreSQL 연결 실패

**증상**:
```
FATAL: password authentication failed for user "moa"
```

**해결책**:

1. **환경 변수 확인**:
```bash
# .env 파일 확인
cat .env | grep DATABASE_URL
```

2. **PostgreSQL 컨테이너 상태 확인**:
```bash
docker-compose ps db
docker logs moa-db
```

3. **수동 연결 테스트**:
```bash
docker exec -it moa-db psql -U moa -d moa
```

4. **데이터베이스 재초기화** (주의: 데이터 삭제됨):
```bash
docker-compose down -v
docker-compose up -d db
```

---

### 2. 마이그레이션 문제

**증상**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxxx'
```

**해결책**:

```bash
# 현재 리비전 확인
cd backend
alembic current

# 헤드로 업그레이드
alembic upgrade head

# 또는 강제 초기화
alembic downgrade base
alembic upgrade head
```

---

## 인증 관련 문제

### 1. "Not authenticated" 에러

**증상**:
```json
{"detail": "Not authenticated"}
```

**원인**: JWT 토큰이 없거나 만료됨

**해결책 (데모 모드)**:

MOA는 개발 환경에서 **선택적 인증**을 지원합니다.

#### 자동 데모 사용자 생성 확인:
```bash
docker exec moa-db psql -U moa -d moa -c "SELECT email, name FROM users WHERE email='demo@moa.local';"
```

#### 수동으로 데모 사용자 생성:
```bash
docker exec moa-db psql -U moa -d moa -c "
INSERT INTO users (id, email, name, hashed_password, is_active, created_at)
VALUES (
  gen_random_uuid(),
  'demo@moa.local',
  'Demo User',
  '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyFz.c/oG9K2',
  true,
  NOW()
) ON CONFLICT DO NOTHING;
"
```

#### 프로덕션 환경에서는:
- JWT 토큰 발급 후 사용
- 데모 사용자 비활성화

---

### 2. JWT 토큰 만료

**증상**:
```json
{"detail": "Invalid or expired token"}
```

**해결책**:

```bash
# 새로운 토큰 발급
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@moa.local", "password": "Demo@12345"}'

# 응답에서 access_token 사용
# Authorization: Bearer <access_token>
```

---

## 프론트엔드 문제

### 1. "시작하기" 버튼 클릭 시 반응 없음

**원인**: 백엔드 API 연결 실패 또는 인증 문제

**진단 단계**:

1. **브라우저 개발자 도구 확인** (F12):
   - Console 탭에서 에러 확인
   - Network 탭에서 API 요청 실패 확인

2. **백엔드 헬스체크**:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/metrics/health
```

3. **CORS 에러 확인**:
```bash
# .env 파일에서 CORS 설정 확인
CORS_ORIGINS=http://localhost:3000,http://localhost:3002
```

---

### 2. Next.js 빌드 에러

**증상**:
```
Module not found: Can't resolve '@/components/...'
```

**해결책**:

```bash
cd frontend

# node_modules 재설치
rm -rf node_modules .next
npm install

# 개발 서버 재시작
npm run dev
```

---

### 3. Tailwind CSS 스타일 미적용

**원인**: Tailwind CSS 4.0 마이그레이션 이슈

**해결책**:

1. **설정 확인**:
```javascript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  // ...
};
```

2. **빌드 재실행**:
```bash
npm run build
npm run dev
```

---

## 백엔드 API 문제

### 1. Internal Server Error (500)

**증상**:
```
Internal Server Error
```

**진단**:

```bash
# 백엔드 로그 확인
docker logs moa-backend --tail 50

# 실시간 로그 모니터링
docker logs -f moa-backend
```

**일반적인 원인**:
- 환경 변수 누락 (API 키 등)
- 데이터베이스 연결 실패
- Redis 연결 실패
- 코드 오류

---

### 2. AI 파이프라인 에러

**증상**:
```
ai_pipeline: unhealthy: No module named 'ai_pipeline'
```

**원인**: AI Worker 컨테이너가 제대로 빌드되지 않음

**해결책**:

```bash
# AI Worker 재빌드
docker-compose up -d --build ai_worker

# 로그 확인
docker logs moa-ai-worker
```

---

### 3. MinIO/S3 업로드 실패

**증상**:
```
NoSuchBucket: The specified bucket does not exist
```

**해결책**:

1. **MinIO 웹 콘솔 접속**: http://localhost:9001
   - 사용자: `moa_minio`
   - 비밀번호: `moa_minio_password`

2. **버킷 수동 생성**:
   - Buckets 메뉴에서 `moa-audio` 버킷 생성

3. **또는 API로 생성**:
```bash
docker exec moa-backend python -c "
import boto3
client = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='moa_minio',
    aws_secret_access_key='moa_minio_password'
)
client.create_bucket(Bucket='moa-audio')
"
```

---

## Review API 문제

### 1. Review API 500 에러 - "No module named 'ai_pipeline'"

**증상**:
```json
{"detail": "Failed to get review status: No module named 'ai_pipeline'"}
```

**원인**: Review API가 LangGraph 워크플로우 상태를 조회하기 위해 `ai_pipeline` 모듈을 import하는데, 백엔드 컨테이너에 해당 모듈이 마운트되지 않음

**해결책**:

`docker-compose.yml`에서 백엔드 컨테이너에 ai_pipeline 볼륨 추가:

```yaml
backend:
  volumes:
    - ./backend:/app
    - ./ai_pipeline:/app/ai_pipeline  # 추가
```

**적용 방법**:
```bash
docker-compose down
docker-compose up -d
```

**참고**:
- Review API는 현재 LangGraph 워크플로우와 강하게 결합되어 있습니다
- ai_pipeline 의존성이 없어도 프론트엔드는 정상 작동하도록 에러 처리가 되어 있습니다
- 프로덕션 환경에서는 Review 상태를 DB에 저장하는 것이 권장됩니다

---

### 2. 회의 상세 페이지 탭 클릭 시 콘텐츠 미표시

**증상**:
- 탭(요약, 액션 아이템, 트랜스크립트)을 클릭하면 색상은 변하지만 아래 콘텐츠가 표시되지 않음

**원인**:
- 회의 데이터가 아직 생성되지 않았거나 처리 중인 상태
- 조건부 렌더링으로 인해 빈 화면 표시

**해결 상태**: ✅ 해결됨
- 각 탭에 "데이터 없음" 상태 UI 추가
- 회의 상태에 따른 적절한 안내 메시지 표시

**현재 동작**:
- **요약 탭**: 데이터 없을 시 회의 상태에 따른 메시지 표시
- **액션 아이템 탭**: 액션 아이템 추가 UI 항상 표시
- **트랜스크립트 탭**: 데이터 없을 시 상태에 따른 메시지 표시
- **진행 상황 탭**: 처리 중일 때만 표시

---

### 3. Review API 401 Unauthorized 에러

**증상**:
```
Request failed with status code 401
```

**원인**: Review API 엔드포인트가 필수 인증을 요구했으나, 프론트엔드에서 JWT 토큰을 제공하지 않음

**해결 상태**: ✅ 해결됨
- Review API를 선택적 인증(`get_optional_user`)으로 변경
- 인증되지 않은 요청은 자동으로 demo 사용자 사용

**수정된 엔드포인트**:
- `GET /api/v1/meetings/{meeting_id}/review`
- `POST /api/v1/meetings/{meeting_id}/review`
- `GET /api/v1/meetings/{meeting_id}/results`

---

## 알려진 이슈

### 1. bcrypt/passlib 초기화 에러 (해결됨)

**증상**:
```
ValueError: password cannot be longer than 72 bytes
```

**해결 상태**: ✅ 해결됨
- 데모 사용자는 데이터베이스에 직접 삽입
- 런타임에서 비밀번호 해싱 제거

**이전 임시 해결책** (참고용):
```python
# backend/app/core/security.py
def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_password)
```

---

### 2. Naver Clova API 키 필수

**증상**: STT 단계에서 실패

**해결책**:
- Naver Cloud Platform에서 Clova Speech API 키 발급 필요
- `.env`에 `CLOVA_API_KEY`, `CLOVA_API_SECRET` 설정

**임시 우회** (테스트용):
- AI 파이프라인 비활성화하고 수동으로 transcript 삽입

---

### 3. Frontend 포트가 3002로 변경됨

**이유**: 개발 환경에서 3000번 포트 충돌 회피

**영향**:
- 프론트엔드: http://localhost:3002
- 백엔드: http://localhost:8000

**변경 방법**:
```bash
# frontend 디렉토리에서
PORT=3000 npm run dev

# 또는 package.json 수정
"scripts": {
  "dev": "next dev -p 3000"
}
```

---

## 서비스 상태 확인 체크리스트

문제 발생 시 다음 순서로 확인:

### 1. Docker 컨테이너 상태
```bash
docker-compose ps
```
모든 서비스가 `Up` 상태여야 함

### 2. 헬스체크
```bash
# 백엔드
curl http://localhost:8000/health

# 백엔드 상세
curl http://localhost:8000/api/v1/metrics/health
```

예상 응답:
```json
{
  "status": "healthy",  // 또는 "degraded"
  "database": "healthy",
  "redis": "healthy",
  "ai_pipeline": "unhealthy",  // API 키 없으면 정상
  "timestamp": "2026-01-31T..."
}
```

### 3. 프론트엔드 접근
- http://localhost:3002 접속
- 페이지 로드 확인

### 4. API 테스트
```bash
# 회의 목록 조회
curl http://localhost:8000/api/v1/meetings

# 회의 생성
curl -X POST http://localhost:8000/api/v1/meetings \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Meeting", "meeting_date": "2026-01-31"}'
```

---

## 완전 초기화 (Last Resort)

모든 방법이 실패할 경우:

```bash
# 1. 모든 컨테이너 및 볼륨 삭제 (데이터 손실 주의!)
docker-compose down -v

# 2. 이미지까지 삭제
docker-compose down --rmi all -v

# 3. .env 파일 재설정
cp .env.example .env
# .env 파일 편집하여 API 키 등 설정

# 4. 처음부터 재시작
docker-compose build --no-cache
docker-compose up -d

# 5. 로그 확인
docker-compose logs -f
```

---

## 추가 도움이 필요한 경우

1. **GitHub Issues**: 버그 리포트 및 기능 요청
2. **로그 첨부**: 문제 발생 시 반드시 로그 포함
3. **환경 정보**: OS, Docker 버전, 브라우저 등

```bash
# 환경 정보 수집
docker --version
docker-compose --version
node --version
python --version

# 로그 내보내기
docker logs moa-backend > backend.log 2>&1
docker logs moa-frontend > frontend.log 2>&1
```

---

**Last Updated**: 2026-01-31
**Version**: 2.0.0
