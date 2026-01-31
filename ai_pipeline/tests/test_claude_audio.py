"""
Tests for Claude Audio Integration
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ai_pipeline.pipeline.integrations.claude_audio import (
    ClaudeAudioProcessor,
    AudioTranscriptResult,
    SUPPORTED_AUDIO_FORMATS,
    MAX_AUDIO_SIZE_BYTES,
)


class TestClaudeAudioProcessor:
    """ClaudeAudioProcessor 테스트"""

    @pytest.fixture
    def mock_anthropic(self):
        """Anthropic 클라이언트 모킹"""
        with patch("ai_pipeline.pipeline.integrations.claude_audio.Anthropic") as mock:
            yield mock

    @pytest.fixture
    def processor(self, mock_anthropic):
        """테스트용 프로세서 인스턴스"""
        return ClaudeAudioProcessor(api_key="test-api-key")

    def test_init_with_api_key(self, mock_anthropic):
        """API 키로 초기화"""
        processor = ClaudeAudioProcessor(api_key="test-key")
        assert processor.api_key == "test-key"
        mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_without_api_key_raises(self, mock_anthropic):
        """API 키 없이 초기화시 에러"""
        with patch("ai_pipeline.pipeline.integrations.claude_audio.settings") as mock_settings:
            mock_settings.claude_api_key = None
            with pytest.raises(ValueError, match="API key is required"):
                ClaudeAudioProcessor()

    def test_get_media_type_wav(self, processor):
        """WAV 파일 media type"""
        path = Path("test.wav")
        assert processor._get_media_type(path) == "audio/wav"

    def test_get_media_type_mp3(self, processor):
        """MP3 파일 media type"""
        path = Path("test.mp3")
        assert processor._get_media_type(path) == "audio/mp3"

    def test_get_media_type_unsupported(self, processor):
        """지원하지 않는 형식"""
        path = Path("test.xyz")
        with pytest.raises(ValueError, match="지원하지 않는 오디오 형식"):
            processor._get_media_type(path)

    def test_supported_formats(self):
        """지원 형식 목록"""
        assert ".wav" in SUPPORTED_AUDIO_FORMATS
        assert ".mp3" in SUPPORTED_AUDIO_FORMATS
        assert ".flac" in SUPPORTED_AUDIO_FORMATS
        assert ".m4a" in SUPPORTED_AUDIO_FORMATS

    def test_extract_speakers_korean(self, processor):
        """한국어 화자 추출"""
        transcript = """
화자 1: 안녕하세요.
화자 2: 네, 안녕하세요.
화자 1: 오늘 회의를 시작하겠습니다.
"""
        speakers = processor._extract_speakers(transcript)
        assert "화자 1" in speakers
        assert "화자 2" in speakers

    def test_extract_speakers_with_names(self, processor):
        """이름이 있는 화자 추출"""
        transcript = """
김철수: 안녕하세요.
이영희: 네, 안녕하세요.
"""
        speakers = processor._extract_speakers(transcript)
        assert len(speakers) >= 2

    def test_parse_full_response(self, processor):
        """전체 응답 파싱"""
        response = """## 트랜스크립트
화자 1: 안녕하세요.
화자 2: 네.

## 요약
테스트 회의 요약입니다.

## 핵심 포인트
- 포인트 1
- 포인트 2

## 액션 아이템
- [ ] 보고서 작성 - 담당자: 김철수
- [ ] 자료 준비 - 담당자: 이영희

## 화자 목록
- 화자 1: 진행자
- 화자 2: 참석자
"""
        result = processor._parse_full_response(response)

        assert "화자 1: 안녕하세요" in result.transcript
        assert result.summary == "테스트 회의 요약입니다."
        assert len(result.key_points) == 2
        assert "포인트 1" in result.key_points
        assert len(result.action_items) == 2
        assert result.action_items[0]["content"] == "보고서 작성"
        assert result.action_items[0]["assignee"] == "김철수"
        assert "화자 1" in result.speakers


class TestAudioTranscriptResult:
    """AudioTranscriptResult 테스트"""

    def test_basic_result(self):
        """기본 결과 생성"""
        result = AudioTranscriptResult(
            transcript="테스트 트랜스크립트",
            summary="테스트 요약",
        )
        assert result.transcript == "테스트 트랜스크립트"
        assert result.summary == "테스트 요약"
        assert result.speakers is None
        assert result.action_items is None

    def test_full_result(self):
        """전체 결과 생성"""
        result = AudioTranscriptResult(
            transcript="트랜스크립트",
            summary="요약",
            speakers=["화자 1", "화자 2"],
            key_points=["포인트 1", "포인트 2"],
            action_items=[
                {"content": "할 일", "assignee": "담당자", "priority": "high"}
            ],
            duration_seconds=300.0,
            model="claude-sonnet-4-5-20250929",
        )
        assert len(result.speakers) == 2
        assert len(result.key_points) == 2
        assert len(result.action_items) == 1
        assert result.duration_seconds == 300.0
        assert "claude" in result.model


class TestMaxFileSize:
    """파일 크기 제한 테스트"""

    def test_max_size_constant(self):
        """최대 크기 상수"""
        assert MAX_AUDIO_SIZE_BYTES == 25 * 1024 * 1024  # 25MB
