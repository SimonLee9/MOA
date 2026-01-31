# MOA Scripts

> 자동화, 검증, 마이그레이션을 위한 스크립트 모음 (monet-registry 스타일)

## 개요

이 폴더는 MOA 프로젝트의 개발 및 운영 자동화 스크립트를 관리합니다.

## 스크립트 목록

### 검증 (Validation)

| 스크립트 | 설명 | 실행 |
|---------|------|------|
| `validate-meetings.py` | 회의 데이터 무결성 검증 | `python scripts/validate-meetings.py` |
| `validate-actions.py` | 액션 아이템 스키마 검증 | `python scripts/validate-actions.py` |
| `validate-prompts.py` | 프롬프트 파일 형식 검증 | `python scripts/validate-prompts.py` |

### 마이그레이션 (Migration)

| 스크립트 | 설명 | 실행 |
|---------|------|------|
| `migrate-transcript-format.py` | 트랜스크립트 형식 마이그레이션 | `python scripts/migrate-transcript-format.py` |
| `migrate-action-schema.py` | 액션 아이템 스키마 업그레이드 | `python scripts/migrate-action-schema.py` |

### 통계/분석 (Stats)

| 스크립트 | 설명 | 실행 |
|---------|------|------|
| `stats-meetings.py` | 회의 통계 리포트 | `python scripts/stats-meetings.py` |
| `stats-pipeline.py` | 파이프라인 성능 분석 | `python scripts/stats-pipeline.py` |

### 빌드/배포 (Build)

| 스크립트 | 설명 | 실행 |
|---------|------|------|
| `postbuild-validate.py` | 빌드 후 검증 | `python scripts/postbuild-validate.py` |
| `generate-api-docs.py` | API 문서 생성 | `python scripts/generate-api-docs.py` |

## 사용법

### 전체 검증 실행

```bash
# 모든 검증 스크립트 실행
python scripts/validate-all.py

# 특정 검증만 실행
python scripts/validate-meetings.py --verbose
```

### CI/CD 통합

```yaml
# .github/workflows/validate.yml
- name: Validate Data
  run: python scripts/validate-all.py
```

## 스크립트 작성 가이드

### 공통 구조

```python
#!/usr/bin/env python3
"""
스크립트 설명

Usage:
    python scripts/script-name.py [options]

Options:
    --verbose    상세 출력
    --fix        자동 수정 모드
"""

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # 스크립트 로직

if __name__ == "__main__":
    main()
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 1 | 검증 실패 (에러 발견) |
| 2 | 스크립트 오류 |
