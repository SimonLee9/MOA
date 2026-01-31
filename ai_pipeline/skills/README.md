# MOA Skills Registry

> AI 회의 매니저를 위한 확장 가능한 스킬 시스템

## 개요

monet-registry의 prompt 시스템에서 영감을 받아 설계된 MOA 스킬 레지스트리입니다.
각 스킬은 독립적인 마크다운 파일로 정의되며, AI 파이프라인에서 동적으로 로드됩니다.

## 스킬 목록

| 스킬 | 파일 | 설명 |
|------|------|------|
| 회의 요약 | `summarize.md` | 회의 트랜스크립트를 구조화된 요약으로 변환 |
| 액션 추출 | `extract-actions.md` | 회의에서 할 일 항목 자동 추출 |
| 의사결정 추출 | `extract-decisions.md` | 회의에서 결정된 사항만 추출 |
| 안건 생성 | `generate-agenda.md` | 이전 회의 기반 다음 회의 안건 생성 |
| 참석자 분석 | `analyze-speakers.md` | 화자별 발언 분석 및 참여도 측정 |
| 토픽 추출 | `extract-topics.md` | 회의 주제 및 키워드 분류 |
| 후속 회의 | `suggest-followup.md` | 후속 조치 및 다음 회의 필요성 판단 |
| 회의록 포맷 | `format-minutes.md` | 공식 회의록 형식으로 변환 |

## 스킬 파일 구조

각 스킬 파일은 YAML 프론트매터와 마크다운 본문으로 구성됩니다:

```markdown
---
name: skill-name
version: "1.0"
description: 스킬 설명
input_schema:
  - transcript: string
  - meeting_title: string (optional)
output_schema:
  type: json
  fields:
    - field_name: type
---

# System Prompt

시스템 프롬프트 내용...

# User Prompt Template

사용자 프롬프트 템플릿...
```

## 사용법

```python
from ai_pipeline.skills import SkillRegistry

# 스킬 레지스트리 초기화
registry = SkillRegistry()

# 스킬 로드
skill = registry.get_skill("summarize")

# 프롬프트 생성
system_prompt = skill.get_system_prompt()
user_prompt = skill.format_user_prompt(
    transcript="...",
    meeting_title="프로젝트 킥오프"
)
```

## 새 스킬 추가

1. `skills/` 폴더에 새 마크다운 파일 생성
2. YAML 프론트매터에 메타데이터 정의
3. System Prompt와 User Prompt Template 섹션 작성
4. `SkillRegistry`가 자동으로 새 스킬을 인식

## 기여

새 스킬을 추가하거나 기존 스킬을 개선하려면:
1. 스킬 파일 생성/수정
2. 테스트 케이스 추가 (`tests/test_skills.py`)
3. PR 제출
