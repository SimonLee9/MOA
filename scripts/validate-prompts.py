#!/usr/bin/env python3
"""
프롬프트 파일 형식 검증 스크립트

prompts/ 및 ai_pipeline/skills/ 폴더의 마크다운 프롬프트 파일을 검증

Usage:
    python scripts/validate-prompts.py [options]

Options:
    --verbose    상세 출력
    --path       검증할 프롬프트 경로
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# 색상 코드
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

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# 필수 프론트매터 필드
REQUIRED_FRONTMATTER = ["name", "version", "description"]

# 선택 프론트매터 필드
OPTIONAL_FRONTMATTER = ["agent_type", "category", "requires", "produces", "input_schema", "output_schema"]

# 필수 섹션 (최소 하나 이상)
EXPECTED_SECTIONS = ["에이전트 역할", "작업 지침", "출력 형식", "System Prompt", "User Prompt"]


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """YAML 프론트매터 파싱"""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError:
            return None, content

    return None, content


def validate_frontmatter(frontmatter: dict | None, file_path: str) -> ValidationResult:
    """프론트매터 검증"""
    result = ValidationResult()

    if frontmatter is None:
        result.errors.append({
            "type": "missing_frontmatter",
            "file": file_path,
            "message": "YAML 프론트매터가 없거나 파싱에 실패했습니다.",
            "suggestion": "파일 시작에 --- 로 감싼 YAML 블록을 추가하세요.",
        })
        return result

    # 필수 필드 검증
    for field_name in REQUIRED_FRONTMATTER:
        if field_name not in frontmatter:
            result.errors.append({
                "type": "missing_required_field",
                "field": field_name,
                "file": file_path,
                "message": f"필수 프론트매터 필드 '{field_name}'이(가) 누락되었습니다.",
            })

    # name 형식 검증 (kebab-case)
    if "name" in frontmatter:
        name = frontmatter["name"]
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            result.warnings.append({
                "type": "invalid_name_format",
                "field": "name",
                "value": name,
                "file": file_path,
                "message": f"name '{name}'이(가) kebab-case 형식이 아닙니다.",
                "suggestion": "예: 'extract-actions', 'transcript-to-summary'",
            })

    # version 형식 검증
    if "version" in frontmatter:
        version = str(frontmatter["version"])
        if not re.match(r"^\d+\.\d+(\.\d+)?$", version):
            result.warnings.append({
                "type": "invalid_version_format",
                "field": "version",
                "value": version,
                "file": file_path,
                "message": f"version '{version}'이(가) 시맨틱 버전 형식이 아닙니다.",
                "suggestion": "예: '1.0', '1.0.0'",
            })

    # input_schema / output_schema 검증
    for schema_field in ["input_schema", "output_schema"]:
        if schema_field in frontmatter:
            schema = frontmatter[schema_field]
            if not isinstance(schema, dict):
                result.errors.append({
                    "type": "invalid_schema_format",
                    "field": schema_field,
                    "file": file_path,
                    "message": f"{schema_field}는 객체 형식이어야 합니다.",
                })

    return result


def validate_body(body: str, file_path: str) -> ValidationResult:
    """본문 검증"""
    result = ValidationResult()

    # 섹션 헤더 추출
    headers = re.findall(r"^#+\s+(.+)$", body, re.MULTILINE)

    if not headers:
        result.warnings.append({
            "type": "no_sections",
            "file": file_path,
            "message": "마크다운 섹션 헤더가 없습니다.",
            "suggestion": "# 또는 ## 로 시작하는 섹션을 추가하세요.",
        })
    else:
        # 예상 섹션 중 하나 이상 있는지 확인
        found_expected = any(
            any(expected.lower() in header.lower() for expected in EXPECTED_SECTIONS)
            for header in headers
        )

        if not found_expected:
            result.warnings.append({
                "type": "missing_expected_sections",
                "file": file_path,
                "found_sections": headers,
                "message": "표준 섹션이 없습니다.",
                "suggestion": f"다음 중 하나 이상 포함 권장: {EXPECTED_SECTIONS}",
            })

    # 템플릿 변수 검증 {{variable}}
    variables = re.findall(r"\{\{([^}]+)\}\}", body)
    if variables:
        # 조건문이 아닌 변수에서 공백 검사
        for var in variables:
            if not var.startswith("#") and not var.startswith("/"):
                if " " in var.strip():
                    result.warnings.append({
                        "type": "variable_with_spaces",
                        "variable": var,
                        "file": file_path,
                        "message": f"템플릿 변수에 공백이 포함되어 있습니다: '{{{{{var}}}}}'",
                    })

    # 코드 블록 검증 (JSON 출력 형식이 있는 경우)
    json_blocks = re.findall(r"```json\s*(.*?)```", body, re.DOTALL)
    for i, block in enumerate(json_blocks):
        # 간단한 JSON 구조 검증 (중괄호 짝 맞춤)
        open_braces = block.count("{")
        close_braces = block.count("}")
        if open_braces != close_braces:
            result.warnings.append({
                "type": "unbalanced_json",
                "file": file_path,
                "block_index": i,
                "message": f"JSON 블록의 중괄호가 맞지 않습니다. ({{ {open_braces}개, }} {close_braces}개)",
            })

    return result


def validate_file(file_path: Path) -> ValidationResult:
    """단일 파일 검증"""
    result = ValidationResult()

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        result.errors.append({
            "type": "encoding_error",
            "file": str(file_path),
            "message": "파일을 UTF-8로 읽을 수 없습니다.",
        })
        return result

    # 파일명 검증 (kebab-case.md)
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$", file_path.name):
        result.warnings.append({
            "type": "invalid_filename",
            "file": str(file_path),
            "message": f"파일명 '{file_path.name}'이(가) kebab-case.md 형식이 아닙니다.",
        })

    # 프론트매터 파싱 및 검증
    frontmatter, body = parse_frontmatter(content)
    fm_result = validate_frontmatter(frontmatter, str(file_path))
    result.errors.extend(fm_result.errors)
    result.warnings.extend(fm_result.warnings)

    # 본문 검증
    body_result = validate_body(body, str(file_path))
    result.errors.extend(body_result.errors)
    result.warnings.extend(body_result.warnings)

    # 파일명과 name 필드 일치 확인
    if frontmatter and "name" in frontmatter:
        expected_name = file_path.stem
        if frontmatter["name"] != expected_name:
            result.warnings.append({
                "type": "name_mismatch",
                "file": str(file_path),
                "frontmatter_name": frontmatter["name"],
                "filename": expected_name,
                "message": f"프론트매터의 name '{frontmatter['name']}'이(가) "
                          f"파일명 '{expected_name}'과 일치하지 않습니다.",
            })

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="프롬프트 파일 형식 검증")
    parser.add_argument("--path", type=Path, nargs="+",
                       default=[Path("prompts"), Path("ai_pipeline/skills")],
                       help="검증할 프롬프트 경로")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="상세 출력")
    args = parser.parse_args()

    print(f"{BLUE}MOA Prompt Validator{RESET}")
    print("-" * 40)

    all_results = ValidationResult()
    file_count = 0

    for path in args.path:
        if not path.exists():
            print(f"{YELLOW}Warning:{RESET} 경로가 존재하지 않습니다: {path}")
            continue

        print(f"\nScanning: {path}")

        md_files = list(path.glob("**/*.md"))
        # README.md 제외
        md_files = [f for f in md_files if f.name != "README.md"]

        for md_file in md_files:
            file_count += 1
            result = validate_file(md_file)
            all_results.errors.extend(result.errors)
            all_results.warnings.extend(result.warnings)

            if args.verbose:
                status = f"{GREEN}✓{RESET}" if result.is_valid else f"{RED}✗{RESET}"
                print(f"  {status} {md_file.name}")

    # 결과 출력
    print("\n" + "=" * 40)
    print(f"Validated {file_count} file(s)")

    if all_results.errors:
        print(f"\n{RED}Errors ({len(all_results.errors)}):{RESET}")
        for error in all_results.errors:
            print(f"  {RED}✗{RESET} {error.get('file')}: {error.get('message')}")
            if args.verbose and "suggestion" in error:
                print(f"    {BLUE}→{RESET} {error['suggestion']}")

    if all_results.warnings:
        print(f"\n{YELLOW}Warnings ({len(all_results.warnings)}):{RESET}")
        for warning in all_results.warnings:
            print(f"  {YELLOW}⚠{RESET} {warning.get('file')}: {warning.get('message')}")

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
