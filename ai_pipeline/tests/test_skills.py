"""
Tests for MOA Skills Registry
"""

import pytest
from pathlib import Path

from ai_pipeline.skills import SkillRegistry, Skill


class TestSkillRegistry:
    """SkillRegistry 테스트"""

    @pytest.fixture
    def registry(self):
        """스킬 레지스트리 인스턴스"""
        return SkillRegistry()

    def test_load_skills(self, registry):
        """스킬 로드 테스트"""
        skills = registry.list_skills()
        assert len(skills) > 0
        assert "summarize" in skills
        assert "extract-actions" in skills

    def test_get_skill(self, registry):
        """스킬 조회 테스트"""
        skill = registry.get_skill("summarize")
        assert isinstance(skill, Skill)
        assert skill.name == "summarize"
        assert skill.version == "1.0"
        assert skill.category == "core"

    def test_get_skill_not_found(self, registry):
        """없는 스킬 조회 시 에러"""
        with pytest.raises(KeyError):
            registry.get_skill("nonexistent-skill")

    def test_list_skills_by_category(self, registry):
        """카테고리별 스킬 목록"""
        core_skills = registry.list_skills_by_category("core")
        assert "summarize" in core_skills
        assert "extract-actions" in core_skills

    def test_get_categories(self, registry):
        """카테고리 목록 테스트"""
        categories = registry.get_categories()
        assert "core" in categories

    def test_registry_contains(self, registry):
        """스킬 존재 확인"""
        assert "summarize" in registry
        assert "nonexistent" not in registry

    def test_registry_len(self, registry):
        """스킬 개수 확인"""
        assert len(registry) >= 6  # 최소 6개의 스킬


class TestSkill:
    """Skill 클래스 테스트"""

    @pytest.fixture
    def summarize_skill(self):
        """summarize 스킬 인스턴스"""
        registry = SkillRegistry()
        return registry.get_skill("summarize")

    def test_get_system_prompt(self, summarize_skill):
        """시스템 프롬프트 조회"""
        prompt = summarize_skill.get_system_prompt()
        assert "회의록" in prompt
        assert "JSON" in prompt

    def test_format_user_prompt(self, summarize_skill):
        """사용자 프롬프트 포맷팅"""
        prompt = summarize_skill.format_user_prompt(
            meeting_title="프로젝트 킥오프",
            meeting_date="2026-01-31",
            speakers="김철수, 이영희",
            transcript="회의 내용..."
        )
        assert "프로젝트 킥오프" in prompt
        assert "2026-01-31" in prompt
        assert "김철수, 이영희" in prompt
        assert "회의 내용..." in prompt

    def test_format_user_prompt_with_none(self, summarize_skill):
        """None 값 처리"""
        prompt = summarize_skill.format_user_prompt(
            meeting_title=None,
            meeting_date=None,
            speakers=None,
            transcript="테스트 내용"
        )
        assert "테스트 내용" in prompt

    def test_validate_input(self, summarize_skill):
        """입력 검증"""
        # 필수 필드 누락
        errors = summarize_skill.validate_input()
        assert len(errors) > 0

        # 필수 필드 포함
        errors = summarize_skill.validate_input(transcript="테스트")
        assert len(errors) == 0


class TestSkillConditionals:
    """조건문 처리 테스트"""

    @pytest.fixture
    def extract_actions_skill(self):
        """extract-actions 스킬 인스턴스"""
        registry = SkillRegistry()
        return registry.get_skill("extract-actions")

    def test_conditional_with_value(self, extract_actions_skill):
        """조건문 - 값이 있는 경우"""
        prompt = extract_actions_skill.format_user_prompt(
            meeting_title="테스트 회의",
            meeting_date="2026-01-31",
            speakers="참석자",
            transcript="내용",
            summary="요약 내용"
        )
        assert "요약 내용" in prompt

    def test_conditional_without_value(self, extract_actions_skill):
        """조건문 - 값이 없는 경우"""
        prompt = extract_actions_skill.format_user_prompt(
            meeting_title="테스트 회의",
            meeting_date="2026-01-31",
            speakers="참석자",
            transcript="내용",
            summary=None
        )
        assert "<summary>" not in prompt


class TestSkillDateVariables:
    """날짜 변수 테스트"""

    @pytest.fixture
    def extract_actions_skill(self):
        registry = SkillRegistry()
        return registry.get_skill("extract-actions")

    def test_today_date_in_system_prompt(self, extract_actions_skill):
        """시스템 프롬프트에 오늘 날짜 포함"""
        prompt = extract_actions_skill.get_system_prompt()
        # 날짜가 치환되었는지 확인 ({{today_date}}가 없어야 함)
        assert "{{today_date}}" not in prompt
        # YYYY-MM-DD 형식의 날짜가 있어야 함
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", prompt)
