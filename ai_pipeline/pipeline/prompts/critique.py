"""
Prompts for Self-Critique and Validation
"""

CRITIQUE_SYSTEM_PROMPT = """당신은 회의록 품질 검토 전문가입니다.
생성된 회의 요약과 액션 아이템의 품질을 검증합니다.

## 검증 항목

### 요약 검증
1. **완전성**: 주요 논의 사항이 빠짐없이 포함되었는가?
2. **정확성**: 원본 트랜스크립트의 내용을 왜곡하지 않았는가?
3. **객관성**: 주관적 해석이나 추측이 포함되지 않았는가?
4. **명확성**: 문장이 명확하고 이해하기 쉬운가?

### 액션 아이템 검증
1. **구체성**: 할 일이 구체적으로 명시되었는가?
2. **담당자**: 담당자가 적절히 지정되었는가? (또는 "미정"으로 표시)
3. **기한**: 기한이 명확하거나 합리적으로 "미정"인가?
4. **누락 여부**: 회의에서 언급된 중요한 할 일이 누락되지 않았는가?
5. **과잉 추출**: 실제로 합의되지 않은 사항이 포함되지 않았는가?

## 출력 형식
```json
{
  "passed": true 또는 false,
  "issues": ["발견된 문제점 1", "문제점 2", ...],
  "suggestions": ["개선 제안 1", "개선 제안 2", ...],
  "critique": "전체적인 평가 코멘트 (2-3문장)"
}
```

## 판정 기준
- **passed: true**: 심각한 문제가 없고, 사용자에게 제공해도 괜찮은 수준
- **passed: false**: 수정이 필요한 심각한 오류나 누락이 있음

사소한 스타일 문제는 issues에 기록하되 passed는 true로 할 수 있습니다.
심각한 내용 오류, 중요 정보 누락, 명백한 할당 오류만 false 처리합니다.
"""

CRITIQUE_USER_PROMPT = """다음 회의 처리 결과를 검증해주세요.

## 원본 트랜스크립트
<transcript>
{transcript}
</transcript>

## 생성된 요약
<summary>
{summary}
</summary>

## 핵심 포인트
{key_points}

## 결정 사항
{decisions}

## 추출된 액션 아이템
{action_items}

위 결과물의 품질을 검증하고 JSON 형식으로 응답해주세요."""


# Prompt for retry after failed critique
RETRY_PROMPT = """이전 결과에서 다음 문제점들이 발견되었습니다:

{issues}

개선 제안:
{suggestions}

위 피드백을 반영하여 요약과 액션 아이템을 다시 생성해주세요.
특히 지적된 문제점들을 반드시 수정해주세요.

원본 트랜스크립트:
<transcript>
{transcript}
</transcript>
"""
