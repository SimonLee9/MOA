#!/usr/bin/env python3
"""
회의 데이터 무결성 검증 스크립트

monet-registry의 validate-metadata.ts를 참고하여 구현

Usage:
    python scripts/validate-meetings.py [options]

Options:
    --verbose    상세 출력
    --path       검증할 데이터 경로
    --fix        자동 수정 모드
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# 색상 코드 (터미널 출력용)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


@dataclass
class ValidationResult:
    """검증 결과"""

    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_valid(self) -> bool:
        return not self.has_errors


# 회의 상태 Enum
VALID_STATUSES = ["uploaded", "processing", "transcribed", "summarized", "completed", "failed"]

# 우선순위 Enum
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]

# 필수 필드
REQUIRED_FIELDS = ["id", "status", "created_at"]

# 선택 필드 타입
OPTIONAL_FIELDS = {
    "title": str,
    "audio_url": str,
    "duration_seconds": (int, float),
    "speakers": list,
    "transcript": str,
    "summary": str,
    "action_items": list,
}


def validate_meeting_schema(meeting: dict, file_path: str) -> ValidationResult:
    """단일 회의 데이터 스키마 검증"""
    result = ValidationResult()

    # 필수 필드 검증
    for field_name in REQUIRED_FIELDS:
        if field_name not in meeting:
            result.errors.append({
                "type": "missing_required_field",
                "field": field_name,
                "file": file_path,
                "message": f"필수 필드 '{field_name}'이(가) 누락되었습니다.",
            })

    # 상태 값 검증
    if "status" in meeting:
        if meeting["status"] not in VALID_STATUSES:
            result.errors.append({
                "type": "invalid_status",
                "field": "status",
                "value": meeting["status"],
                "file": file_path,
                "message": f"유효하지 않은 상태: '{meeting['status']}'. "
                          f"허용값: {VALID_STATUSES}",
                "suggestion": f"status를 {VALID_STATUSES} 중 하나로 변경하세요.",
            })

    # 날짜 형식 검증
    for date_field in ["created_at", "updated_at", "meeting_date"]:
        if date_field in meeting and meeting[date_field]:
            try:
                datetime.fromisoformat(meeting[date_field].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                result.errors.append({
                    "type": "invalid_date_format",
                    "field": date_field,
                    "value": meeting[date_field],
                    "file": file_path,
                    "message": f"'{date_field}'가 ISO 8601 형식이 아닙니다.",
                    "suggestion": "YYYY-MM-DDTHH:mm:ssZ 형식으로 변경하세요.",
                })

    # 선택 필드 타입 검증
    for field_name, expected_type in OPTIONAL_FIELDS.items():
        if field_name in meeting and meeting[field_name] is not None:
            if not isinstance(meeting[field_name], expected_type):
                result.warnings.append({
                    "type": "type_mismatch",
                    "field": field_name,
                    "expected": str(expected_type),
                    "actual": type(meeting[field_name]).__name__,
                    "file": file_path,
                    "message": f"'{field_name}' 필드 타입이 올바르지 않습니다.",
                })

    # 액션 아이템 검증
    if "action_items" in meeting and meeting["action_items"]:
        for i, action in enumerate(meeting["action_items"]):
            action_result = validate_action_item(action, f"{file_path}:action_items[{i}]")
            result.errors.extend(action_result.errors)
            result.warnings.extend(action_result.warnings)

    # 오디오 URL 검증 (상태에 따른 필수 여부)
    if meeting.get("status") in ["processing", "transcribed", "summarized", "completed"]:
        if not meeting.get("audio_url"):
            result.warnings.append({
                "type": "missing_audio_url",
                "field": "audio_url",
                "file": file_path,
                "message": "처리된 회의에 audio_url이 없습니다.",
            })

    # 트랜스크립트 검증 (상태에 따른 필수 여부)
    if meeting.get("status") in ["summarized", "completed"]:
        if not meeting.get("transcript"):
            result.errors.append({
                "type": "missing_transcript",
                "field": "transcript",
                "file": file_path,
                "message": "요약된 회의에 트랜스크립트가 없습니다.",
            })

    return result


def validate_action_item(action: dict, context: str) -> ValidationResult:
    """액션 아이템 검증"""
    result = ValidationResult()

    # content 필수
    if not action.get("content"):
        result.errors.append({
            "type": "missing_action_content",
            "field": "content",
            "context": context,
            "message": "액션 아이템에 내용(content)이 없습니다.",
        })

    # priority 검증
    if action.get("priority") and action["priority"] not in VALID_PRIORITIES:
        result.warnings.append({
            "type": "invalid_priority",
            "field": "priority",
            "value": action["priority"],
            "context": context,
            "message": f"유효하지 않은 우선순위: '{action['priority']}'",
        })

    # due_date 형식 검증
    if action.get("due_date"):
        try:
            datetime.strptime(action["due_date"], "%Y-%m-%d")
        except ValueError:
            result.warnings.append({
                "type": "invalid_due_date",
                "field": "due_date",
                "value": action["due_date"],
                "context": context,
                "message": "마감일이 YYYY-MM-DD 형식이 아닙니다.",
            })

    return result


def validate_duplicate_ids(meetings: list[dict]) -> ValidationResult:
    """중복 ID 검증"""
    result = ValidationResult()
    seen_ids: dict[str, str] = {}

    for meeting in meetings:
        meeting_id = meeting.get("id")
        file_path = meeting.get("_file_path", "unknown")

        if meeting_id in seen_ids:
            result.errors.append({
                "type": "duplicate_id",
                "id": meeting_id,
                "files": [seen_ids[meeting_id], file_path],
                "message": f"중복된 회의 ID: '{meeting_id}'",
            })
        else:
            seen_ids[meeting_id] = file_path

    return result


def load_meetings_from_path(path: Path) -> list[dict]:
    """경로에서 회의 데이터 로드"""
    meetings = []

    if path.is_file():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for m in data:
                    m["_file_path"] = str(path)
                meetings.extend(data)
            else:
                data["_file_path"] = str(path)
                meetings.append(data)
    elif path.is_dir():
        for json_file in path.glob("**/*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for m in data:
                            m["_file_path"] = str(json_file)
                        meetings.extend(data)
                    else:
                        data["_file_path"] = str(json_file)
                        meetings.append(data)
            except json.JSONDecodeError as e:
                print(f"{RED}Error:{RESET} {json_file}: JSON 파싱 실패 - {e}")

    return meetings


def print_result(result: ValidationResult, verbose: bool = False) -> None:
    """검증 결과 출력"""
    # 에러 출력
    if result.errors:
        print(f"\n{RED}=== Errors ({len(result.errors)}) ==={RESET}")
        for error in result.errors:
            print(f"{RED}✗{RESET} [{error.get('type')}] {error.get('message')}")
            if verbose:
                print(f"  File: {error.get('file', error.get('context', 'N/A'))}")
                if "suggestion" in error:
                    print(f"  {BLUE}Suggestion:{RESET} {error['suggestion']}")

    # 경고 출력
    if result.warnings:
        print(f"\n{YELLOW}=== Warnings ({len(result.warnings)}) ==={RESET}")
        for warning in result.warnings:
            print(f"{YELLOW}⚠{RESET} [{warning.get('type')}] {warning.get('message')}")
            if verbose:
                print(f"  File: {warning.get('file', warning.get('context', 'N/A'))}")


def print_stats(meetings: list[dict]) -> None:
    """통계 출력"""
    print(f"\n{BLUE}=== Statistics ==={RESET}")
    print(f"Total meetings: {len(meetings)}")

    # 상태별 분포
    status_counts: dict[str, int] = {}
    for meeting in meetings:
        status = meeting.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\nStatus distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")


def main() -> int:
    parser = argparse.ArgumentParser(description="회의 데이터 무결성 검증")
    parser.add_argument("--path", type=Path, default=Path("data/meetings"),
                       help="검증할 데이터 경로")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="상세 출력")
    parser.add_argument("--fix", action="store_true",
                       help="자동 수정 모드 (아직 미구현)")
    args = parser.parse_args()

    print(f"{BLUE}MOA Meeting Validator{RESET}")
    print(f"Path: {args.path}")
    print("-" * 40)

    # 데이터 로드
    if not args.path.exists():
        print(f"{YELLOW}Warning:{RESET} 경로가 존재하지 않습니다: {args.path}")
        print("샘플 데이터로 검증을 건너뜁니다.")
        return 0

    meetings = load_meetings_from_path(args.path)
    print(f"Loaded {len(meetings)} meeting(s)")

    if not meetings:
        print(f"{YELLOW}Warning:{RESET} 검증할 회의 데이터가 없습니다.")
        return 0

    # 검증 실행
    all_results = ValidationResult()

    # 개별 회의 검증
    for meeting in meetings:
        file_path = meeting.get("_file_path", "unknown")
        result = validate_meeting_schema(meeting, file_path)
        all_results.errors.extend(result.errors)
        all_results.warnings.extend(result.warnings)

    # 중복 ID 검증
    dup_result = validate_duplicate_ids(meetings)
    all_results.errors.extend(dup_result.errors)

    # 결과 출력
    print_result(all_results, args.verbose)
    print_stats(meetings)

    # 최종 결과
    print("\n" + "=" * 40)
    if all_results.is_valid:
        print(f"{GREEN}✓ Validation passed!{RESET}")
        if all_results.warnings:
            print(f"  ({len(all_results.warnings)} warnings)")
        return 0
    else:
        print(f"{RED}✗ Validation failed!{RESET}")
        print(f"  {len(all_results.errors)} error(s), {len(all_results.warnings)} warning(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
