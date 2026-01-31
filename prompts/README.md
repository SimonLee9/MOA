# MOA Prompts

> AI 에이전트 작업을 위한 프롬프트 템플릿 (monet-registry 스타일)

## 개요

이 폴더는 MOA AI 파이프라인에서 사용하는 에이전트 프롬프트를 관리합니다.
각 프롬프트는 특정 작업을 수행하는 AI 에이전트를 위한 지침입니다.

## 프롬프트 목록

| 파일 | 용도 | 입력 | 출력 |
|------|------|------|------|
| `audio-to-transcript.md` | 오디오 파일 → 텍스트 변환 지침 | 오디오 URL | 트랜스크립트 |
| `transcript-to-summary.md` | 트랜스크립트 → 요약 | 트랜스크립트 | 구조화된 요약 |
| `extract-action-items.md` | 액션 아이템 추출 | 트랜스크립트, 요약 | 액션 아이템 목록 |
| `generate-meeting-report.md` | 전체 회의 리포트 생성 | 모든 데이터 | 완성된 리포트 |
| `review-and-critique.md` | 결과물 검토 및 피드백 | AI 생성 결과물 | 피드백, 수정사항 |
| `init.md` | 새 회의 처리 초기화 | 회의 메타데이터 | 처리 계획 |

## 프롬프트 구조

```markdown
---
name: prompt-name
version: "1.0"
description: 프롬프트 설명
agent_type: processor | reviewer | generator
requires:
  - input_field_1
  - input_field_2
produces:
  - output_field_1
---

# 에이전트 역할

에이전트의 역할과 목표 설명...

# 작업 지침

구체적인 작업 단계...

# 출력 형식

예상 출력 형식...

# 예시

입출력 예시...
```

## 사용법

프롬프트는 AI 파이프라인의 각 노드에서 로드되어 사용됩니다:

```python
from ai_pipeline.skills import SkillRegistry

registry = SkillRegistry(skills_dir="prompts/")
prompt = registry.get_skill("transcript-to-summary")
```

## 새 프롬프트 추가

1. 마크다운 파일 생성 (`kebab-case.md`)
2. YAML 프론트매터에 메타데이터 정의
3. 에이전트 역할, 작업 지침, 출력 형식 작성
4. 예시 추가
