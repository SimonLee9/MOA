"""
Skill Registry - monet-registry 스타일의 스킬 로더 및 레지스트리

마크다운 파일에서 스킬을 로드하고 관리합니다.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta


@dataclass
class Skill:
    """스킬 정의"""
    name: str
    version: str
    description: str
    category: str
    system_prompt: str
    user_prompt_template: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)

    def get_system_prompt(self, **kwargs: Any) -> str:
        """시스템 프롬프트 반환 (변수 치환 포함)"""
        prompt = self.system_prompt

        # 날짜 관련 기본 변수 추가
        defaults = {
            "today_date": datetime.now().strftime("%Y-%m-%d"),
            "next_week_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        }

        for key, value in {**defaults, **kwargs}.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        return prompt

    def format_user_prompt(self, **kwargs: Any) -> str:
        """사용자 프롬프트 템플릿에 변수 적용"""
        prompt = self.user_prompt_template

        # Handlebars 스타일 조건문 처리 {{#if var}}...{{/if}}
        prompt = self._process_conditionals(prompt, kwargs)

        # 변수 치환 {{var}}
        for key, value in kwargs.items():
            if value is not None:
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            else:
                prompt = prompt.replace(f"{{{{{key}}}}}", "")

        return prompt.strip()

    def _process_conditionals(self, template: str, variables: dict) -> str:
        """Handlebars 스타일 조건문 처리"""
        pattern = r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}"

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            content = match.group(2)
            if variables.get(var_name):
                return content
            return ""

        return re.sub(pattern, replacer, template, flags=re.DOTALL)

    def validate_input(self, **kwargs: Any) -> list[str]:
        """입력 스키마 검증"""
        errors = []
        required = self.input_schema.get("required", [])

        for field_name in required:
            if field_name not in kwargs or kwargs[field_name] is None:
                errors.append(f"필수 입력 '{field_name}'이(가) 누락되었습니다.")

        return errors


class SkillRegistry:
    """스킬 레지스트리 - 스킬 로드 및 관리"""

    def __init__(self, skills_dir: Path | str | None = None):
        """
        Args:
            skills_dir: 스킬 파일들이 있는 디렉토리 경로
                        None이면 기본 경로 사용
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent
        elif isinstance(skills_dir, str):
            skills_dir = Path(skills_dir)

        self.skills_dir = skills_dir
        self._skills: dict[str, Skill] = {}
        self._load_all_skills()

    def _load_all_skills(self) -> None:
        """디렉토리의 모든 스킬 파일 로드"""
        for md_file in self.skills_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue
            try:
                skill = self._load_skill_file(md_file)
                self._skills[skill.name] = skill
            except Exception as e:
                print(f"Warning: Failed to load skill from {md_file}: {e}")

    def _load_skill_file(self, file_path: Path) -> Skill:
        """마크다운 파일에서 스킬 로드"""
        content = file_path.read_text(encoding="utf-8")

        # YAML 프론트매터 파싱
        frontmatter, body = self._parse_frontmatter(content)

        # System Prompt와 User Prompt Template 섹션 추출
        system_prompt = self._extract_section(body, "System Prompt")
        user_prompt_template = self._extract_section(body, "User Prompt Template")

        return Skill(
            name=frontmatter.get("name", file_path.stem),
            version=frontmatter.get("version", "1.0"),
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "general"),
            input_schema=frontmatter.get("input_schema", {}),
            output_schema=frontmatter.get("output_schema", {}),
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """YAML 프론트매터 파싱"""
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
        else:
            frontmatter = {}
            body = content

        return frontmatter, body

    def _extract_section(self, content: str, section_name: str) -> str:
        """마크다운 섹션 내용 추출"""
        pattern = rf"#\s*{re.escape(section_name)}\s*\n(.*?)(?=\n#\s|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()
        return ""

    def get_skill(self, name: str) -> Skill:
        """이름으로 스킬 조회"""
        if name not in self._skills:
            raise KeyError(f"스킬 '{name}'을(를) 찾을 수 없습니다. "
                          f"사용 가능한 스킬: {list(self._skills.keys())}")
        return self._skills[name]

    def list_skills(self) -> list[str]:
        """등록된 모든 스킬 이름 반환"""
        return list(self._skills.keys())

    def list_skills_by_category(self, category: str) -> list[str]:
        """카테고리별 스킬 목록 반환"""
        return [
            name for name, skill in self._skills.items()
            if skill.category == category
        ]

    def get_categories(self) -> list[str]:
        """모든 카테고리 목록 반환"""
        return list(set(skill.category for skill in self._skills.values()))

    def reload(self) -> None:
        """모든 스킬 다시 로드"""
        self._skills.clear()
        self._load_all_skills()

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __len__(self) -> int:
        return len(self._skills)

    def __iter__(self):
        return iter(self._skills.values())
