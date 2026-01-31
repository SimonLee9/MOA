# Known Issues

현재 알려진 문제와 해결 방안을 정리한 문서입니다.

---

## 🔴 Critical Issues

### 1. bcrypt 라이브러리 초기화 에러

**상태**: 🔴 미해결 (v2.0.0)

**증상**:
- 회원가입 API 호출 시 `Internal Server Error` 발생
- 백엔드 로그에서 다음 에러 확인:
  ```
  ValueError: password cannot be longer than 72 bytes,
  truncate manually if necessary (e.g. my_password[:72])
  ```

**원인**:
- `passlib[bcrypt]` 라이브러리가 초기화될 때 자체 테스트를 수행
- 테스트 과정에서 72바이트를 초과하는 테스트 데이터 사용
- bcrypt의 내재적 72바이트 제한에 걸림

**현재 적용된 임시 해결책**:
1. `backend/app/core/security.py`에서 비밀번호를 72바이트로 자동 절단:
   ```python
   def get_password_hash(password: str) -> str:
       password_bytes = password.encode('utf-8')
       if len(password_bytes) > 72:
           password_bytes = password_bytes[:72]
       truncated_password = password_bytes.decode('utf-8', errors='ignore')
       return pwd_context.hash(truncated_password)
   ```

2. `backend/Dockerfile`에 빌드 도구 추가:
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       gcc \
       g++ \
       build-essential \
       libffi-dev \
       libpq-dev
   ```

**문제점**:
- 위 해결책으로도 passlib 초기화 단계의 에러는 해결되지 않음
- 사용자 함수 호출 이전에 라이브러리 내부에서 에러 발생

**향후 해결 방안**:
1. **Option A**: passlib 버전 다운그레이드
   ```bash
   # requirements.txt
   passlib[bcrypt]==1.7.2  # 또는 더 낮은 버전
   ```

2. **Option B**: bcrypt 직접 사용
   ```python
   import bcrypt

   def get_password_hash(password: str) -> str:
       return bcrypt.hashpw(
           password.encode('utf-8')[:72],
           bcrypt.gensalt()
       ).decode('utf-8')
   ```

3. **Option C**: Argon2로 교체 (권장)
   ```bash
   # requirements.txt
   argon2-cffi>=21.3.0
   ```
   ```python
   from argon2 import PasswordHasher

   pwd_context = PasswordHasher()
   ```

**영향 범위**:
- ❌ 회원가입 불가
- ❌ 로그인 불가
- ✅ 이미 생성된 사용자는 영향 없음 (DB에 해시만 저장)
- ✅ 업로드 기능은 인증만 우회하면 테스트 가능

**우선순위**: P0 (배포 전 필수 해결)

---

## 🟡 Medium Issues

### 2. 프론트엔드 포트 충돌

**상태**: 🟢 해결 방법 확인됨

**증상**:
- `npm run dev` 실행 시 포트 3000이 이미 사용 중
- 프론트엔드가 자동으로 3001 포트로 전환

**해결 방법**:

**Windows**:
```bash
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :3000

# 프로세스 강제 종료
taskkill //F //PID <프로세스ID>
```

**Linux/Mac**:
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :3000

# 프로세스 종료
kill -9 <PID>
```

**우선순위**: P2 (사용자 해결 가능)

---

### 3. Docker 환경 변수 설정

**상태**: 🟢 문서화 완료

**증상**:
- Docker Compose 실행 시 백엔드가 데이터베이스에 연결 실패
- `Connection refused` 에러 발생

**원인**:
- `.env` 파일에서 `DATABASE_URL`이 `localhost`로 설정됨
- Docker 네트워크에서는 서비스명(`db`)을 사용해야 함

**해결 방법**:
```bash
# .env 파일 수정
DATABASE_URL=postgresql+asyncpg://moa:moa_dev_password@db:5432/moa
#                                                      ^^
#                                                  localhost가 아닌 db
```

**우선순위**: P1 (문서화 완료)

---

## 🔵 Minor Issues

### 4. Next.js SWC 버전 불일치

**상태**: ⚠️ 경고만 발생, 기능 정상

**증상**:
```
⚠ Mismatching @next/swc version, detected: 15.5.7 while Next.js is on 15.5.11
```

**영향**: 없음 (경고만 표시, 기능 정상 작동)

**해결 방법** (선택사항):
```bash
cd frontend
npm install --save-exact @next/swc-win32-x64-msvc@15.5.11
# 또는 해당 플랫폼에 맞는 패키지
```

**우선순위**: P3 (선택적)

---

## 📋 해결 로드맵

### v2.0.1 (긴급 패치)
- [ ] **Issue #1**: bcrypt 문제 해결 (Argon2로 전환)
- [ ] 회원가입/로그인 기능 테스트
- [ ] 기존 사용자 마이그레이션 스크립트 작성

### v2.1.0
- [ ] 프론트엔드 업로드 기능 E2E 테스트
- [ ] 에러 핸들링 개선
- [ ] 사용자 피드백 반영

---

## 🆘 문제 발생 시

### 즉시 확인할 사항

1. **백엔드 로그**:
   ```bash
   docker-compose logs -f backend
   ```

2. **프론트엔드 로그**:
   - 브라우저 개발자 도구 (F12) Console 탭
   - 터미널에서 `npm run dev` 출력

3. **데이터베이스 연결**:
   ```bash
   docker-compose exec db psql -U moa -d moa -c "SELECT 1;"
   ```

4. **서비스 상태**:
   ```bash
   docker-compose ps
   ```

### 이슈 리포팅

새로운 문제를 발견하셨나요?

1. 위 체크리스트로 기본 디버깅 수행
2. GitHub Issues에 다음 정보와 함께 등록:
   - OS 및 환경 (Windows/Mac/Linux, Docker 버전)
   - 재현 단계
   - 에러 로그 (백엔드, 프론트엔드)
   - 기대 동작 vs 실제 동작

**Issues**: https://github.com/SimonLee9/MOA/issues

---

**Last Updated**: 2026-01-31
**Next Review**: 2026-02-07
